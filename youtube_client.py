import yt_dlp
import os
from settings import COOKIES_FILE

class YouTubeClient:
    def __init__(self):
        self.ytdlp_opts = {
            "quiet": False, 
            "extract_flat": True,
            "skip_download": True,
            "format": "best", 
            "youtube_client": "web", # Arama için web kullanmak daha iyidir
        }

        # Eğer cookies dosyası varsa ekle
        if os.path.exists(COOKIES_FILE):
            self.ytdlp_opts["cookiefile"] = COOKIES_FILE

    def search_videos(self, query, limit=10):
        """
        Verilen sorguya göre YouTube'da video arar.
        """
        results = []
        # ytsearch, arama yapmayı sağlar.
        search_query = f"ytsearch{limit}:{query}" 

        with yt_dlp.YoutubeDL(self.ytdlp_opts) as ydl:
            try:
                # download=False sadece meta veriyi indirir
                info = ydl.extract_info(search_query, download=False)
                
                # entries alanındaki her bir sonuç için gerekli bilgileri alıyoruz
                for entry in info.get("entries", []):
                    # extract_flat: True olduğunda, bazı alanlar eksik gelebilir.
                    if entry and entry.get("duration"): # Sadece süresi olan geçerli girişleri al
                        thumbnails = entry.get("thumbnails", [])
                        thumbnail_url = thumbnails[-1].get("url") if thumbnails else entry.get("thumbnail")

                        results.append({
                            "title": entry.get("title"),
                            "url": entry.get("url"),
                            "duration": entry.get("duration"),
                            "channel": entry.get("channel"),
                            "thumbnail": thumbnail_url,
                            "id": entry.get("id"),
                            # ID3 etiketleme için gerekli temel bilgiler:
                            "artist": entry.get("channel"),
                            "album": "YouTube",
                            "year": "", # Yıl bilgisi arama sonuçlarında zor bulunur, boş bırakalım
                            "track_no": 0,
                            "cover_url": thumbnail_url
                        })
            except Exception as e:
                print("Hata oluştu (yt-dlp):", e)
                return [] 
        return results

    def get_playlist_tracks_meta(self, url):
        """
        Playlist URL'sinden tüm parçaların meta verisini döner.
        Playlist ID'sini URL'den ayırarak daha saf bir sorgu gönderir.
        """
        
        # Playlist ID'sini ayıkla
        playlist_id = None
        if "list=" in url:
             playlist_id = url.split("list=")[-1].split("&")[0]
        elif "playlist/" in url:
             playlist_id = url.split("playlist/")[-1].split("?")[0]
        
        if not playlist_id:
             print(f"[HATA] Geçersiz playlist URL formatı: {url}")
             return []
        
        # Sadece Playlist ID'si ile yeni URL oluştur
        playlist_url = f"https://www.youtube.com/playlist?list={playlist_id}"
        
        ydl_opts = {
            "quiet": True, 
            "extract_flat": True, 
            "skip_download": True,
            "force_generic_extractor": True, 
            "youtube_client": "web",
        }
        
        if os.path.exists(COOKIES_FILE):
             ydl_opts["cookiefile"] = COOKIES_FILE
             
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            try:
                info = ydl.extract_info(playlist_url, download=False)
                
                if info.get('_type') == 'playlist':
                    tracks = []
                    playlist_title = info.get("title", "YouTube Playlist")
                    
                    # Sadece temel bilgileri çekiyoruz
                    for idx, entry in enumerate(info.get("entries", []), 1):
                        if entry and entry.get("id"):
                            thumbnail = entry.get("thumbnail")
                            # Yüksek kalite thumbnail URL'si oluştur
                            video_id = entry.get("id")
                            if not thumbnail and video_id:
                                thumbnail = f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg"
                            
                            tracks.append({
                                "url": entry.get("url") or f"https://www.youtube.com/watch?v={video_id}",
                                "title": entry.get("title", "Video"),
                                "channel": entry.get("channel", "YouTube"),
                                "thumbnail": thumbnail,
                                "cover_url": thumbnail,  # tagger için
                                "playlist_title": playlist_title,
                                "track_no": idx,
                                "artist": entry.get("channel", "YouTube"),
                                "album": playlist_title
                            })
                    return tracks
                else:
                    return []
                    
            except Exception as e:
                print(f"[HATA] Playlist meta veri hatası: {e}")
                return []