# 🎵 DownX GTK4

Modern, kullanıcı dostu Spotify ve YouTube müzik indirme uygulaması.

## 🚀 Hızlı Kurulum (Bazzite/Fedora)

### ⚡ Tek Komut ile Kur

```bash
curl -fsSL https://raw.githubusercontent.com/kubilaysen1/DownX-gtk4/main/install.sh | bash
```

### 📥 Manuel Kurulum

```bash
# 1. Script'i indir
wget https://github.com/kubilaysen1/DownX-gtk4/raw/main/install.sh

# 2. Çalıştırılabilir yap
chmod +x install.sh

# 3. Kur
./install.sh
```

### 🎮 Çalıştır

```bash
downx
```

veya **Uygulama Menüsü → Ses/Video → DownX**

### 🗑️ Kaldır

```bash
~/.local/share/downx/uninstall.sh
```

---

## ✨ Özellikler

- 🎵 **Spotify İndirme**: Playlist, albüm ve tekli şarkı desteği
- 🎬 **YouTube İndirme**: Video ve ses formatları
- 🏷️ **Otomatik Etiketleme**: ID3v2/MP4 metadata desteği
- 🎨 **Kapak Resimleri**: Otomatik boyutlandırma (300x300, teyp uyumlu)
- 📁 **Akıllı Organizasyon**: Albüm/playlist klasörleri
- 🚀 **Çoklu İndirme**: Paralel download desteği (3 eşzamanlı)
- 💾 **LRU Cache**: Memory leak önleme (100 kapak)
- 🎨 **Modern Arayüz**: GTK4/Adwaita tasarım
- 🌐 **Google Drive**: Müzik yedekleme desteği

---

## 📋 Gereksinimler

### Sistem Gereksinimleri

- **İşletim Sistemi**: Bazzite, Fedora 39+, Ubuntu 23.04+
- **Python**: 3.10 veya üzeri
- **GTK**: 4.0+
- **FFmpeg**: Ses dönüştürme için

### Python Kütüphaneleri

Kurulum scripti otomatik yükler, ancak manuel kurulum için:

```bash
pip install --break-system-packages \
    yt-dlp \
    spotipy \
    mutagen \
    requests \
    Pillow \
    google-api-python-client \
    google-auth-httplib2 \
    google-auth-oauthlib
```

### FFmpeg Kurulumu

#### Bazzite/Fedora
```bash
rpm-ostree install ffmpeg
systemctl reboot
```

#### Ubuntu/Debian
```bash
sudo apt install ffmpeg
```

---

## ⚙️ Yapılandırma

İlk çalıştırmada **Ayarlar** sekmesinden:

### 1. Spotify API

1. [Spotify Developer Dashboard](https://developer.spotify.com/dashboard)'a git
2. **Create App** → Uygulama adı: "DownX"
3. **Client ID** ve **Client Secret** kopyala
4. DownX → Ayarlar → Spotify bilgilerini gir

### 2. İndirme Ayarları

- **Dizin**: Müzik klasörünü seç
- **Format**: MP3 / M4A / FLAC / OPUS / WAV
- **Kalite**: 128-320 kbps
- **Metadata**: Otomatik etiketleme (varsayılan açık)

### 3. Google Drive (Opsiyonel)

1. [Google Cloud Console](https://console.cloud.google.com/) → API'lar ve Servisler
2. Google Drive API'yi etkinleştir
3. OAuth 2.0 kimlik bilgileri oluştur
4. credentials.json'u indir
5. DownX → Ayarlar → Google Drive → Bağlan

---

## 📖 Kullanım

### 🎵 Spotify İndirme

1. Spotify'dan şarkı/playlist/albüm linkini kopyala
   - Şarkı: `https://open.spotify.com/track/...`
   - Playlist: `https://open.spotify.com/playlist/...`
   - Albüm: `https://open.spotify.com/album/...`
2. DownX'e yapıştır
3. **İndir** butonuna tıkla

### 🎬 YouTube İndirme

1. YouTube video linkini kopyala
2. DownX'e yapıştır
3. Format seç (Ses / Video)
4. Kalite seç
5. **İndir** butonuna tıkla

### 📁 Toplu İndirme

1. **Araçlar** sekmesi → **URL Listesinden İçe Aktar**
2. TXT dosyası seç (her satırda bir URL)
3. **Tümünü İndir** butonuna tıkla

**Örnek TXT:**
```
https://open.spotify.com/track/abc123
https://open.spotify.com/playlist/xyz789
https://www.youtube.com/watch?v=def456
```

---

## 🛠️ Teknik Detaylar

### Mimari

- **GUI**: GTK4 (libadwaita)
- **İndirme**: yt-dlp (YouTube Music entegrasyonu)
- **Metadata**: Mutagen (ID3v2 / MP4 tags)
- **API**: Spotipy, Google APIs
- **Threading**: ThreadPoolExecutor (3 worker)

### Dosya Yapısı

```
DownX-gtk4/
├── gui.py                  # Ana GTK4 arayüzü
├── queue_manager.py        # İndirme kuyruğu yöneticisi
├── tagger.py              # Metadata yazıcı (teyp uyumlu)
├── spotify_client.py      # Spotify API client
├── youtube_client.py      # YouTube API client
├── downloader.py          # yt-dlp wrapper
├── settings.py            # Ayarlar yöneticisi
├── downloads_tab.py       # İndirmeler sekmesi
├── search_tab.py          # Arama sekmesi
├── tools_tab.py           # Araçlar sekmesi
├── settings_tab.py        # Ayarlar sekmesi
└── install.sh             # Otomatik kurulum scripti
```

### Metadata Optimizasyonu

- **Kapak Boyutu**: 640x640 → 300x300 (eski teyp uyumlu)
- **Kapak Sıkıştırma**: Max 80KB (JPEG quality=85)
- **Tag Formatı**: ID3v2.3 (MP3), MP4 (M4A)
- **Cache**: LRU (100 kapak) - memory leak önleme

### Spotify → YouTube Music Süreci

1. Spotify API'den metadata al (artist, title, album, cover_url)
2. YouTube Music'te ara: `"{artist} - {title}"`
3. En iyi eşleşmeyi bul (başlık benzerliği)
4. yt-dlp ile indir (320kbps M4A)
5. Mutagen ile etiketle (Spotify metadata)
6. Kapak resmini küçült ve ekle

---

## 🔧 Sorun Giderme

### "command not found: downx"

```bash
# PATH'e ekle
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
source ~/.bashrc
```

### "No module named 'gi'"

```bash
# GTK4 Python bindings
rpm-ostree install python3-gobject gtk4
systemctl reboot
```

### "FFmpeg not found"

```bash
# Bazzite/Fedora
rpm-ostree install ffmpeg
systemctl reboot

# Ubuntu
sudo apt install ffmpeg
```

### "Spotify API error"

- Ayarlar → Spotify → Client ID/Secret doğru girdiğinden emin ol
- [Spotify Dashboard](https://developer.spotify.com/dashboard)'da uygulamanın aktif olduğunu kontrol et

### "YouTube download failed"

- İnternet bağlantını kontrol et
- yt-dlp'yi güncelle: `pip install --upgrade --break-system-packages yt-dlp`

### Kapak resimleri görünmüyor

- Pillow kurulu mu kontrol et: `python3 -c "import PIL"`
- Yoksa: `pip install --break-system-packages Pillow`

---

## 📝 Changelog

### v3.1.0 (2024-12-11)

#### ✨ Yenilikler
- ✅ SpotDL → yt-dlp tam migration
- ✅ Python 3.14 uyumluluk
- ✅ Otomatik kurulum scripti (install.sh)
- ✅ Tagger.py tam entegrasyonu
- ✅ Kapak boyutlandırma (teyp uyumlu)

#### 🐛 Düzeltmeler
- ✅ Settings tab dinamik visibility
- ✅ Memory leak düzeltmesi (LRU cache)
- ✅ Metadata yazma hataları düzeltildi
- ✅ Threading timeout koruması

#### 🔧 Teknik
- Python 3.14 asyncio uyumluluğu
- GTK4 dinamik UI güncellemeleri
- yt-dlp library API kullanımı
- Mutagen ID3v2.3 formatı

### v3.0.0 (2024-12-10)
- 🎉 GTK3 → GTK4 tam migration
- 🎨 Adwaita modern tasarım
- 📱 Mobile-friendly UI
- 🚀 Performance iyileştirmeleri

---

## 🤝 Katkıda Bulunma

1. Fork yapın
2. Feature branch oluşturun (`git checkout -b feature/amazing`)
3. Commit yapın (`git commit -m 'feat: amazing feature'`)
4. Push yapın (`git push origin feature/amazing`)
5. Pull Request açın

### Geliştirme Ortamı

```bash
# Repo'yu klonla
git clone https://github.com/kubilaysen1/DownX-gtk4.git
cd DownX-gtk4

# Bağımlılıkları yükle
pip install --break-system-packages -r requirements.txt

# Çalıştır
python3 gui.py
```

---

## 📜 Lisans

GPL-3.0 License - Detaylar için [LICENSE](LICENSE) dosyasına bakın.

---

## 👤 Yazar

**Kubilay Sen**

- GitHub: [@kubilaysen1](https://github.com/kubilaysen1)
- Proje: [DownX-gtk4](https://github.com/kubilaysen1/DownX-gtk4)

---

## 🙏 Teşekkürler

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) - Video/ses indirme
- [Spotipy](https://github.com/spotipy-dev/spotipy) - Spotify API wrapper
- [Mutagen](https://github.com/quodlibet/mutagen) - Audio metadata
- [GTK](https://www.gtk.org/) - GUI toolkit
- [Anthropic Claude](https://www.anthropic.com/) - Development assistance

---

## ⚠️ Yasal Uyarı

Bu yazılım **sadece eğitim amaçlıdır**. Kullanıcılar telif hakkı yasalarına uymakla yükümlüdür. İndirdiğiniz içerikleri kullanma hakkınızın olduğundan emin olun.

---

## 🌟 Yıldız Ver!

Bu projeyi beğendiyseniz, lütfen GitHub'da ⭐ verin!

[![GitHub stars](https://img.shields.io/github/stars/kubilaysen1/DownX-gtk4.svg?style=social&label=Star)](https://github.com/kubilaysen1/DownX-gtk4)
[![GitHub forks](https://img.shields.io/github/forks/kubilaysen1/DownX-gtk4.svg?style=social&label=Fork)](https://github.com/kubilaysen1/DownX-gtk4/fork)

---

## 📧 İletişim

Sorularınız veya önerileriniz için GitHub Issues kullanın:
https://github.com/kubilaysen1/DownX-gtk4/issues
