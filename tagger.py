"""
4KTube Free - Tagger (TEYP UYUMLU VERSİYON)
Mutagen ile MP3 ve M4A etiketleme.
✅ LRU Cache ile memory leak düzeltildi
✅ Kapak resmi otomatik küçültülür (300x300, max 80KB)
✅ Ford X-9030 gibi eski teyplerle uyumlu
✅ Zaman aşımı koruması
"""

import os
import io
import requests
from mutagen.id3 import ID3, TIT2, TPE1, TALB, TRCK, TDRC, APIC, ID3NoHeaderError
from mutagen.mp3 import MP3
from mutagen.mp4 import MP4, MP4Cover
from collections import OrderedDict

# PIL/Pillow import - Kapak resmi küçültme için
try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    print("[TAGGER UYARI] Pillow yüklü değil. Kapak resimleri küçültülmeyecek.")
    print("[TAGGER UYARI] Yüklemek için: pip install Pillow --break-system-packages")


class LRUCoverCache:
    """
    LRU (Least Recently Used) Cache - Kapak resimleri için
    Maksimum boyut sınırı ile memory leak önlenir
    """
    def __init__(self, max_size=100):
        self.cache = OrderedDict()
        self.max_size = max_size

    def get(self, url):
        """URL'den kapak al, cache'te varsa en üste taşı"""
        if url in self.cache:
            self.cache.move_to_end(url)
            return self.cache[url]
        return None

    def set(self, url, data):
        """Kapak resmini cache'e ekle, limit aşılırsa en eskiyi sil"""
        if url in self.cache:
            self.cache.move_to_end(url)
        self.cache[url] = data
        if len(self.cache) > self.max_size:
            self.cache.popitem(last=False)  # En eski öğeyi sil

    def clear(self):
        """Tüm cache'i temizle"""
        self.cache.clear()

    def size(self):
        """Cache'teki öğe sayısı"""
        return len(self.cache)


# Global cache instance - Maksimum 100 kapak resmi saklar
_cover_cache = LRUCoverCache(max_size=100)

# Minimum dosya boyutu (50KB - gerçekçi bir değer)
MIN_AUDIO_FILE_SIZE = 50_000


def resize_cover_for_car(cover_data, max_size_px=300, max_size_kb=80):
    """
    Kapak resmini teyp uyumlu boyuta küçült.

    Args:
        cover_data: Orijinal kapak resmi (bytes)
        max_size_px: Maksimum boyut (piksel) - varsayılan 300x300
        max_size_kb: Maksimum dosya boyutu (KB) - varsayılan 80KB

    Returns:
        bytes: Küçültülmüş kapak resmi veya None
    """
    if not PIL_AVAILABLE:
        print("[TAGGER] Pillow yok, orijinal kapak kullanılıyor")
        return cover_data

    try:
        # Resmi aç
        img = Image.open(io.BytesIO(cover_data))

        # Orijinal boyut bilgisi
        original_size = len(cover_data)
        original_dimensions = img.size
        print(f"[TAGGER] Orijinal kapak: {original_dimensions[0]}x{original_dimensions[1]}, {original_size // 1024}KB")

        # Eğer zaten küçükse ve boyut limiti altındaysa, direkt dön
        if original_dimensions[0] <= max_size_px and original_dimensions[1] <= max_size_px:
            if original_size <= max_size_kb * 1024:
                print(f"[TAGGER] Kapak zaten uygun boyutta, küçültme gerekmiyor")
                return cover_data

        # RGB formatına çevir (RGBA varsa)
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        elif img.mode != 'RGB':
            img = img.convert('RGB')

        # Oranı koruyarak küçült (thumbnail)
        img.thumbnail((max_size_px, max_size_px), Image.LANCZOS)

        # Quality ile deneme yap - 80KB altına düşmeye çalış
        for quality in [85, 75, 65, 55, 45]:
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=quality, optimize=True)
            output_size = output.tell()

            if output_size <= max_size_kb * 1024:
                result = output.getvalue()
                new_dimensions = img.size
                print(f"[TAGGER] ✅ Kapak küçültüldü: {new_dimensions[0]}x{new_dimensions[1]}, {output_size // 1024}KB (quality={quality})")
                return result

        # En düşük quality ile bile büyükse, en son halini dön
        result = output.getvalue()
        print(f"[TAGGER] ⚠️ Kapak küçültüldü ama hala büyük: {len(result) // 1024}KB")
        return result

    except Exception as e:
        print(f"[TAGGER HATA] Kapak küçültme hatası: {e}")
        print(f"[TAGGER] Orijinal kapak kullanılıyor")
        return cover_data


def set_id3_tags(file_path, info):
    """
    Dosya formatına (MP3 veya M4A) göre etiketleri yazar.
    info = {"title":..., "artist":..., "album":..., "track_no":..., "year":..., "cover_url":...}
    """
    try:
        # 1. Dosya Kontrolleri
        if not file_path or not os.path.exists(file_path):
            print(f"[TAGGER HATA] Dosya bulunamadı: {file_path}")
            return False

        # Bozuk veya boş dosya kontrolü - Artık 50KB minimum
        file_size = os.path.getsize(file_path)
        if file_size < MIN_AUDIO_FILE_SIZE:
            print(f"[TAGGER HATA] Dosya çok küçük veya bozuk ({file_size} bytes, min {MIN_AUDIO_FILE_SIZE}): {file_path}")
            return False

        # Info kontrolü
        if not info:
            print(f"[TAGGER HATA] Etiket bilgisi boş: {file_path}")
            return False

        # Dosya uzantısını kontrol et
        _, ext = os.path.splitext(file_path)
        ext = ext.lower()

        # Debug: Ne etiketlenecek göster
        print(f"[TAGGER] Etiketleniyor: {os.path.basename(file_path)}")
        print(f"  -> Title: {info.get('title', 'YOK')}")
        print(f"  -> Artist: {info.get('artist', 'YOK')}")
        print(f"  -> Album: {info.get('album', 'YOK')}")
        print(f"  -> Cover: {'VAR' if info.get('cover_url') else 'YOK'}")

        # Format yönlendirmesi
        if ext == '.mp3':
            return _tag_mp3(file_path, info)
        elif ext in ['.m4a', '.mp4']:
            return _tag_m4a(file_path, info)
        else:
            print(f"[TAGGER UYARI] Desteklenmeyen format: {ext}")
            return False

    except Exception as ex:
        print(f"[TAGGER HATA] Genel Etiketleme hatası: {ex}")
        return False


def _download_cover(url):
    """Kapak resmini indir, önbellekte varsa kullan."""
    if not url:
        return None

    # Önbellekte var mı?
    cached = _cover_cache.get(url)
    if cached:
        print(f"[TAGGER] Kapak cache'ten alındı (Cache: {_cover_cache.size()}/{_cover_cache.max_size})")
        return cached

    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        # KRİTİK: Timeout eklendi (10 saniye). İnternet yoksa program donmasın.
        r = requests.get(url, timeout=10, headers=headers)

        if r.status_code == 200 and len(r.content) > 1000:
            # Kapak resmini küçült (teyp uyumlu)
            resized_cover = resize_cover_for_car(r.content, max_size_px=300, max_size_kb=80)

            if resized_cover:
                _cover_cache.set(url, resized_cover)
                print(f"[TAGGER] Kapak indirildi, küçültüldü ve cache'e eklendi (Cache: {_cover_cache.size()}/{_cover_cache.max_size})")
                return resized_cover
            else:
                print(f"[TAGGER] Kapak küçültülemedi, orijinal kullanılıyor")
                _cover_cache.set(url, r.content)
                return r.content
        else:
            print(f"[TAGGER] Kapak indirilemedi: HTTP {r.status_code}")
            return None

    except requests.Timeout:
        print(f"[TAGGER] Kapak indirme zaman aşımı: {url[:50]}...")
        return None
    except requests.RequestException as e:
        print(f"[TAGGER] Kapak indirme hatası (Network): {e}")
        return None
    except Exception as e:
        print(f"[TAGGER] Beklenmeyen kapak indirme hatası: {e}")
        return None


def _tag_mp3(path, info):
    """MP3 dosyaları için ID3v2 etiketleme."""
    try:
        # ID3 tag'ı aç veya oluştur
        try:
            audio = MP3(path, ID3=ID3)
        except ID3NoHeaderError:
            audio = MP3(path)
            audio.add_tags()

        if audio.tags is None:
            audio.add_tags()

        # Mevcut tag'ları temizle
        # Bu, eski çöp verilerin kalmasını engeller.
        frames_to_delete = ["TIT2", "TPE1", "TALB", "TRCK", "TDRC", "APIC", "COMM", "USLT"]
        for frame in frames_to_delete:
            audio.tags.delall(frame)

        # Verileri hazırla
        title = str(info.get("title", "")).strip()
        artist = str(info.get("artist", "")).strip()
        album = str(info.get("album", "")).strip()

        # Yeni tag'ları yaz
        if title:
            audio.tags.add(TIT2(encoding=3, text=title[:128]))
        if artist:
            audio.tags.add(TPE1(encoding=3, text=artist[:128]))
        if album:
            audio.tags.add(TALB(encoding=3, text=album[:128]))

        # Track numarası
        if info.get("track_no"):
            try:
                audio.tags.add(TRCK(encoding=3, text=str(info["track_no"])))
            except:
                pass

        # Yıl
        if info.get("year"):
            y = str(info.get("year"))
            # Sadece geçerli yılları yaz
            if y.isdigit() and len(y) == 4:
                audio.tags.add(TDRC(encoding=3, text=y))

        # Kapak Resmi (Küçültülmüş)
        cover_url = info.get("cover_url")
        if cover_url:
            cover_data = _download_cover(cover_url)
            if cover_data:
                audio.tags.add(APIC(
                    encoding=3,
                    mime='image/jpeg',
                    type=3,  # Front cover
                    desc='Cover',
                    data=cover_data
                ))
                print(f"[TAGGER] ✅ MP3 Kapak eklendi: {len(cover_data) // 1024}KB (Teyp uyumlu)")

        # v2.3 formatında kaydet (Windows uyumluluğu için en iyisi)
        audio.save(v2_version=3)
        print(f"[TAGGER OK] MP3 etiketlendi: {os.path.basename(path)}")
        return True

    except Exception as e:
        print(f"[TAGGER HATA] MP3 Tag Hatası: {e}")
        return False


def _tag_m4a(path, info):
    """M4A (AAC) dosyaları için MP4 etiketleme."""
    try:
        audio = MP4(path)

        # Mevcut tag'ları temizle (Temiz başlangıç)
        audio.clear()

        title = str(info.get("title", "")).strip()
        artist = str(info.get("artist", "")).strip()
        album = str(info.get("album", "")).strip()

        if title:
            audio["\xa9nam"] = [title[:128]]
        if artist:
            audio["\xa9ART"] = [artist[:128]]
        if album:
            audio["\xa9alb"] = [album[:128]]

        if info.get("track_no"):
            try:
                # M4A track formatı: (track_num, total_tracks)
                audio["trkn"] = [(int(info["track_no"]), 0)]
            except:
                pass

        if info.get("year"):
            audio["\xa9day"] = [str(info["year"])]

        # Kapak Resmi (Küçültülmüş)
        cover_url = info.get("cover_url")
        if cover_url:
            cover_data = _download_cover(cover_url)
            if cover_data:
                audio["covr"] = [MP4Cover(cover_data, imageformat=MP4Cover.FORMAT_JPEG)]
                print(f"[TAGGER] ✅ M4A Kapak eklendi: {len(cover_data) // 1024}KB (Teyp uyumlu)")

        audio.save()
        print(f"[TAGGER OK] M4A etiketlendi: {os.path.basename(path)}")
        return True

    except Exception as e:
        print(f"[TAGGER HATA] M4A Tag Hatası: {e}")
        return False


def clear_cache():
    """Cache'i manuel temizleme fonksiyonu (isteğe bağlı kullanım için)"""
    global _cover_cache
    _cover_cache.clear()
    print(f"[TAGGER] Kapak cache'i temizlendi")


def get_cache_stats():
    """Cache istatistikleri (debug için)"""
    return {
        "size": _cover_cache.size(),
        "max_size": _cover_cache.max_size
    }


def tag_audio(file_path, info):
    """
    Ana etiketleme fonksiyonu (queue_manager.py tarafından çağrılır)

    Args:
        file_path: Ses dosyasının yolu
        info: Metadata dict {title, artist, album, cover_url, year, track_no}

    Returns:
        bool: Başarılı ise True
    """
    if not os.path.exists(file_path):
        print(f"[TAGGER] Dosya bulunamadı: {file_path}")
        return False

    # Dosya boyutu kontrolü
    file_size = os.path.getsize(file_path)
    if file_size < MIN_AUDIO_FILE_SIZE:
        print(f"[TAGGER] Dosya çok küçük ({file_size} bytes), etiketlenmiyor")
        return False

    # Dosya uzantısına göre işle
    ext = os.path.splitext(file_path)[1].lower()

    if ext in ['.mp3']:
        return _tag_mp3(file_path, info)
    elif ext in ['.m4a', '.mp4']:
        return _tag_m4a(file_path, info)
    else:
        print(f"[TAGGER] Desteklenmeyen format: {ext}")
        return False
