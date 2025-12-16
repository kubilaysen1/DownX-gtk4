"""
4KTube Free - YouTube Downloader (GELİŞTİRİLMİŞ)
Sadece YouTube videoları için yt-dlp kullanır
Spotify indirmeleri queue_manager.py içinde SpotDL ile yapılır

DEĞİŞİKLİKLER:
- Config key bug düzeltildi: "mode" -> "download_mode"
- Timeout handling iyileştirildi
- Daha detaylı hata mesajları
"""

import yt_dlp
import os
import threading
import re 
import glob 
import copy
from settings import COOKIES_FILE, GLOBAL_CONFIG, get_download_dir
from tagger import set_id3_tags 

# Terminal Renk Kodlarını Temizleyen Regex
ANSI_ESCAPE = re.compile(r'\x1b\[[0-9;]*m')


def sanitize_filename(filename, max_length=200):
    """
    Dosya adı olarak kullanılamayacak karakterleri temizler.
    
    Args:
        filename: Temizlenecek dosya adı
        max_length: Maksimum karakter sayısı
    
    Returns:
        Temiz dosya adı veya "Unknown"
    """
    if not filename or not str(filename).strip():
        return "Unknown"
    
    clean = str(filename)
    # Windows/Linux'ta yasak karakterleri temizle
    clean = re.sub(r'[<>:"/\\|?*]', '', clean)
    # Baştan/sondan boşluk ve nokta temizle
    clean = clean.strip('. ')
    
    # Maksimum uzunluk kontrolü
    if len(clean) > max_length:
        clean = clean[:max_length]
    
    return clean if clean else "Unknown"


class Downloader(threading.Thread):
    """
    YouTube Video/Ses İndirici
    NOT: Spotify için kullanılmaz! (queue_manager.py içinde SpotDL kullanılır)
    """
    
    def __init__(self, video_url, track_info, progress_callback, finished_callback):
        super().__init__()
        self.video_url = video_url
        
        # KRİTİK: track_info'nun derin kopyasını al
        self.track_info = copy.deepcopy(track_info) if track_info else {}
        
        self.progress_callback = progress_callback
        self.finished_callback = finished_callback
        self.is_downloading = False

        # AYARLARI AL - DÜZELTİLDİ: "download_mode" key kullan!
        download_mode = GLOBAL_CONFIG.get("download_mode", "audio")
        
        # SES AYARLARI
        audio_format = (GLOBAL_CONFIG.get("audio_format") or "mp3").lower()
        
        audio_quality = GLOBAL_CONFIG.get("audio_quality", "192")
        # Sadece sayı varsa 'k' ekle
        if audio_quality.isdigit():
            audio_quality = f"{audio_quality}k"
        
        audio_bitrate_mode = GLOBAL_CONFIG.get("audio_bitrate_mode", "cbr")
        mp3_codec = GLOBAL_CONFIG.get("mp3_codec", "libmp3lame")
        aac_codec = GLOBAL_CONFIG.get("aac_codec", "aac")
        audio_sample_rate = GLOBAL_CONFIG.get("audio_sample_rate", "44100")
        audio_channels = GLOBAL_CONFIG.get("audio_channels", "2")
        
        # VIDEO AYARLARI
        video_format = (GLOBAL_CONFIG.get("video_format") or "mp4").lower()
        video_codec = GLOBAL_CONFIG.get("video_codec", "h264")
        video_quality = GLOBAL_CONFIG.get("video_quality", "1080p")
        video_bitrate = GLOBAL_CONFIG.get("video_bitrate", "auto")
        video_fps = GLOBAL_CONFIG.get("video_fps", "source")
        video_crf = GLOBAL_CONFIG.get("video_crf", "23")
        video_preset = GLOBAL_CONFIG.get("video_preset", "medium")
        video_include_audio = GLOBAL_CONFIG.get("video_include_audio", True)
        
        # DEBUG
        print(f"\n[YOUTUBE] {track_info.get('title', '?')[:40]}")
        print(f"  Mod: {download_mode}")
        print(f"  Video Format: {video_format}, Ses Format: {audio_format}")
        print(f"  Ses Kalitesi: {audio_quality}")
        
        # Klasör
        download_dir = get_download_dir()
        
        playlist_album_name = sanitize_filename(track_info.get('album', 'YouTube'))
        
        if track_info.get('is_playlist') and playlist_album_name not in ['Tekli', 'YouTube']:
            target_directory = os.path.join(download_dir, playlist_album_name)
        else:
            target_directory = download_dir
            
        os.makedirs(target_directory, exist_ok=True)
        
        # yt-dlp'nin kendi metadata'sını kullan
        output_template = os.path.join(
            target_directory,
            "%(title)s.%(ext)s"
        )
        
        # Postprocessor ile dosya adını temizleyeceğiz
        self.target_directory = target_directory
        self.safe_filename = None  # Sonra set edilecek 
        
        # YT-DLP OPTIONS
        self.ytdlp_opts = {
            "progress_hooks": [self.progress_hook],
            "outtmpl": output_template,
            "postprocessor_hooks": [self.postprocessor_hook],
            "quiet": False, 
            "noprogress": True,
            "noplaylist": True, 
            "youtube_client": "web", 
            "keepvideo": False, 
            "socket_timeout": 30,
            "retries": 2,
            "extractor_args": {
                "youtube": {
                    "player_client": ["android", "web"]
                }
            }
        }
        
        if os.path.exists(COOKIES_FILE):
            self.ytdlp_opts["cookiefile"] = COOKIES_FILE
        
        # FORMAT SEÇİMİ
        if download_mode == "audio":
            # Sadece ses
            self._setup_audio(audio_format, audio_quality, audio_bitrate_mode, mp3_codec, aac_codec, audio_sample_rate, audio_channels)
            self.final_path = os.path.join(target_directory, f"temp.{audio_format}")
        
        elif download_mode == "video":
            # Sadece video (sessiz)
            self._setup_video(video_format, video_codec, video_quality, video_bitrate, video_fps, video_crf, video_preset, include_audio=False)
            self.final_path = os.path.join(target_directory, f"temp.{video_format}")
        
        else:  # "video+audio" veya "both"
            # Video + Ses
            self._setup_video(video_format, video_codec, video_quality, video_bitrate, video_fps, video_crf, video_preset, include_audio=True)
            self.final_path = os.path.join(target_directory, f"temp.{video_format}")

    def _setup_audio(self, fmt, quality, bitrate_mode, mp3_codec, aac_codec, sample_rate, channels):
        """Ses indirme ayarları"""
        self.ytdlp_opts["format"] = "bestaudio/best"
        
        audio_pp = {
            "key": "FFmpegExtractAudio", 
            "preferredcodec": fmt,
            "preferredquality": quality.replace('k', '') if not quality.isdigit() else quality,
        }
        
        pp_args = []
        
        if fmt == "mp3":
            pp_args.extend(['-acodec', mp3_codec])
        elif fmt in ["m4a", "aac"]:
            pp_args.extend(['-acodec', aac_codec])
        
        if not quality.isdigit():
            if bitrate_mode == "cbr":
                pp_args.extend(['-b:a', quality, '-minrate', quality, '-maxrate', quality, '-bufsize', '2M'])
            elif bitrate_mode == "abr":
                pp_args.extend(['-b:a', quality])
        
        pp_args.extend(['-ar', sample_rate, '-ac', channels])
        
        self.ytdlp_opts["postprocessors"] = [audio_pp, {"key": "FFmpegMetadata"}]
        self.ytdlp_opts['postprocessor_args'] = pp_args

    def _setup_video(self, fmt, codec, quality, bitrate, fps, crf, preset, include_audio=True):
        """Video indirme ayarları"""
        if include_audio:
            if quality == "best":
                format_str = "bestvideo+bestaudio/best"
            elif quality == "worst":
                format_str = "worstvideo+worstaudio/worst"
            else:
                height = quality.replace('p', '')
                format_str = f"bestvideo[height<={height}]+bestaudio/best[height<={height}]"
        else:
            # Sadece video (sessiz)
            if quality == "best":
                format_str = "bestvideo"
            elif quality == "worst":
                format_str = "worstvideo"
            else:
                height = quality.replace('p', '')
                format_str = f"bestvideo[height<={height}]"
        
        self.ytdlp_opts["format"] = format_str
        
        pp_args = []
        
        if codec == "h264":
            pp_args.extend(['-vcodec', 'libx264'])
        elif codec == "h265":
            pp_args.extend(['-vcodec', 'libx265'])
        elif codec == "copy":
            pp_args.extend(['-vcodec', 'copy'])
        
        if codec in ["h264", "h265"] and crf != "auto":
            pp_args.extend(['-crf', crf])
            pp_args.extend(['-preset', preset])
        
        if bitrate != "auto":
            pp_args.extend(['-b:v', bitrate])
        
        if fps != "source":
            pp_args.extend(['-r', fps])
        
        if include_audio:
            pp_args.extend(['-acodec', 'aac', '-b:a', '192k'])
        
        postprocessors = []
        if include_audio:
            postprocessors.append({
                "key": "FFmpegVideoConvertor", 
                "preferedformat": fmt
            })
        postprocessors.append({"key": "FFmpegMetadata"})
        
        self.ytdlp_opts["postprocessors"] = postprocessors
        self.ytdlp_opts['postprocessor_args'] = pp_args
        
        # merge_output_format ekle
        self.ytdlp_opts["merge_output_format"] = fmt

    def postprocessor_hook(self, d):
        """Dosya adını temizle (FFmpeg postprocess SONRASI)"""
        if d.get('status') != 'finished':
            return
        
        postprocessor = d.get('postprocessor')
        if postprocessor and 'FFmpeg' not in postprocessor:
            return
        
        filepath = d.get('info_dict', {}).get('filepath') or d.get('filepath')
        
        if not filepath or not os.path.exists(filepath):
            return
        
        self._cleanup_temp_files(os.path.dirname(filepath))
        
        directory = os.path.dirname(filepath)
        filename = os.path.basename(filepath)
        name, ext = os.path.splitext(filename)
        
        cleaned_name = self._clean_title(name)
        
        if cleaned_name != name:
            new_filepath = os.path.join(directory, f"{cleaned_name}{ext}")
            
            try:
                if not os.path.exists(new_filepath):
                    os.rename(filepath, new_filepath)
                    print(f"[RENAME] {filename} → {cleaned_name}{ext}")
                    self.safe_filename = cleaned_name
                    self.final_path = new_filepath
                else:
                    print(f"[RENAME] Hedef zaten var: {new_filepath}")
                    self.final_path = filepath
            except Exception as e:
                print(f"[RENAME] Hata: {e}")
                self.final_path = filepath
        else:
            self.safe_filename = name
            self.final_path = filepath
    
    def _cleanup_temp_files(self, directory):
        """Geçici dosyaları temizle"""
        patterns = [
            os.path.join(directory, "*.temp.*"),
            os.path.join(directory, "*.f[0-9]*.webm"),
            os.path.join(directory, "*.f[0-9]*.mp4"),
            os.path.join(directory, "*.f[0-9]*.m4a"),
        ]
        
        for pattern in patterns:
            for temp_file in glob.glob(pattern):
                try:
                    os.remove(temp_file)
                    print(f"[CLEANUP] Silindi: {os.path.basename(temp_file)}")
                except Exception as e:
                    print(f"[CLEANUP] Hata: {e}")
    
    def _clean_title(self, title):
        """YouTube başlığını temizle"""
        original_title = title
        
        # Gereksiz suffiksleri temizle
        title = re.sub(r'\s*\(Official.*?\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[Official.*?\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*Official\s+(Video|Audio|Music\s+Video).*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(Lyric.*?\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[Lyric.*?\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*Lyric\s+Video.*$', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(HD\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[HD\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(4K\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\[4K\]', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(.*?Audio\)', '', title, flags=re.IGNORECASE)
        title = re.sub(r'\s*\(.*?Video\)', '', title, flags=re.IGNORECASE)
        
        # " - " ile böl
        if " - " in title:
            parts = title.split(" - ")
            
            # Artist tekrarı kontrolü
            if hasattr(self, 'track_info') and self.track_info:
                artist = self.track_info.get('artist', '').strip()
                
                if artist and len(parts) >= 2:
                    if len(parts) >= 3 and parts[0].strip().lower() == parts[1].strip().lower():
                        title = f"{parts[0]} - {parts[2]}"
                        return sanitize_filename(title.strip())
                    
                    if parts[0].strip().lower() == artist.lower():
                        title = " - ".join(parts[:2])
                        return sanitize_filename(title.strip())
            
            # Normal temizleme
            if len(parts) >= 3:
                title = f"{parts[-2]} - {parts[-1]}"
            elif len(parts) == 2:
                first = parts[0].lower()
                if any(word in first for word in ['official', 'music', 'plak', 'records', 'channel', 'vevo', 'topic']):
                    title = parts[1]
        
        return sanitize_filename(title.strip())

    def progress_hook(self, d):
        """Progress callback"""
        if d['status'] == 'downloading':
            if d.get('total_bytes'):
                percent = ANSI_ESCAPE.sub('', d['_percent_str']).replace('%', '').strip()
                try:
                    percent_float = float(percent)
                except:
                    percent_float = 0.0
                self.progress_callback(percent_float, f"İndiriliyor: {percent}%")
        elif d['status'] == 'postprocessing':
            self.progress_callback(99.0, "Dönüştürülüyor...")
        
    def run(self):
        """İndirme başlat"""
        self.is_downloading = True
        self.final_path = None
        
        try:
            self.progress_callback(0.0, "Başlatılıyor...")
            
            with yt_dlp.YoutubeDL(self.ytdlp_opts) as ydl:
                ydl.download([self.video_url])
            
            if not self.final_path:
                # Fallback: glob ile bul
                possible = []
                for f in glob.glob(os.path.join(self.target_directory, "*.*")):
                    if '.temp.' in f or re.search(r'\.f\d+\.', f):
                        continue
                    possible.append(f)
                
                if possible:
                    self.final_path = max(possible, key=os.path.getmtime)
            
            if not self.final_path or not os.path.exists(self.final_path):
                raise FileNotFoundError(f"İndirilen dosya bulunamadı!")
            
            self._cleanup_temp_files(self.target_directory)
            
            # Etiket ekle (sadece ses için) - DÜZELTİLDİ: download_mode key
            download_mode = GLOBAL_CONFIG.get("download_mode", "audio")
            if download_mode == "audio":
                self.progress_callback(95.0, "Etiketler ekleniyor...")
                set_id3_tags(self.final_path, self.track_info)
            
            self.finished_callback(True, f"Başarılı: {self.final_path}")

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Video unavailable" in error_msg:
                print(f"\n[HATA] Video bulunamadı veya kaldırıldı\n")
                self.finished_callback(False, "Video bulunamadı")
            elif "Private video" in error_msg:
                print(f"\n[HATA] Video özel (private)\n")
                self.finished_callback(False, "Video özel")
            else:
                print(f"\n[HATA] İndirme hatası: {e}\n")
                self.finished_callback(False, f"İndirme hatası: {error_msg[:100]}")
        except Exception as e:
            print(f"\n[HATA] Beklenmeyen hata: {e}\n")
            try:
                self._cleanup_temp_files(self.target_directory)
            except:
                pass
            self.finished_callback(False, str(e))
        
        finally:
            self.is_downloading = False
