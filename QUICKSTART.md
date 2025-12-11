# 🚀 DownX - Quick Start Guide

## Bazzite OS Özel Kurulum

### 1️⃣ Distrobox İçinde Çalıştırma (Önerilen)

```bash
# Distrobox container oluştur
distrobox create --name downx-env --image fedora:39

# Container'a gir
distrobox enter downx-env

# Bağımlılıkları kur
sudo dnf install gtk4 libadwaita python3-gobject ffmpeg

# Python paketlerini kur
pip install -r requirements.txt

# Çalıştır
python launcher.py
```

### 2️⃣ Doğrudan Çalıştırma (Bazzite'de)

```bash
# Python paketlerini kur
pip install --user -r requirements.txt

# Çalıştır
python launcher.py
```

---

## ⚙️ Spotify API Kurulumu (İsteğe Bağlı)

1. https://developer.spotify.com/dashboard adresine git
2. Yeni bir app oluştur
3. Client ID ve Client Secret'i kopyala
4. Ayarlar sekmesinde yapıştır

---

## 🎨 Özellikler

- **🔍 Akıllı Arama** - YouTube ve Spotify'dan ara
- **📥 Çoklu İndirme** - Eş zamanlı indirme desteği
- **🎵 Otomatik Etiketleme** - ID3 tags + kapak resmi
- **📊 Canlı İstatistikler** - Gerçek zamanlı ilerleme
- **🌙 Koyu Tema** - Bazzite OS tarzı tasarım

---

## 🔧 Sorun Giderme

### GTK4 Bulunamadı
```bash
sudo dnf install gtk4-devel libadwaita-devel
```

### FFmpeg Bulunamadı
```bash
sudo dnf install ffmpeg ffmpeg-libs
```

### Python Modülleri Eksik
```bash
pip install --user -r requirements.txt --break-system-packages
```

---

## 💡 Kullanım İpuçları

1. **Toplu İndirme**: TXT dosyasına linkleri yazın, "TXT Yükle" butonuna tıklayın
2. **Hızlı Yapıştır**: Link'i kopyalayın, "Yapıştır" butonuna tıklayın
3. **Playlist Desteği**: Spotify/YouTube playlist linklerini direkt yapıştırın
4. **Klasör Düzeni**: Her playlist ayrı klasöre indirilir

---

## 📝 Notlar

- Bazzite OS'nin immutable yapısı nedeniyle Distrobox kullanımı önerilir
- İlk çalıştırmada bağımlılıklar kontrol edilir
- İndirme klasörü: `~/Music/4kTube/`
- Config dosyası: `~/.config/4ktube/config.json`

---

**Keyifli Kullanımlar! 🎧**
