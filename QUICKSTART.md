# 🚀 DownX - Quick Start Guide

## 🪟 Windows Kurulumu (Tam Otomatik)

Windows'ta kurulum yapmadan, tek tıkla çalıştırılabilir `.exe` oluşturmak için özel bir script hazırladık.

### 1️⃣ Hazırlık
1. **Python 3.8+** kurun ([python.org](https://www.python.org/downloads/)).
   > ⚠️ Kurulum sırasında **"Add Python to PATH"** kutucuğunu mutlaka işaretleyin!
2. Bu projeyi indirin (Download ZIP veya Git Clone).

### 2️⃣ Kurulum ve Çalıştırma
1. Klasördeki **`tam_otomatik_kurulum.bat`** dosyasına sağ tıklayın ve **"Yönetici Olarak Çalıştır"** deyin.
2. Script şunları otomatik yapacaktır:
   - Gerekli kütüphaneleri kurar.
   - **FFmpeg**'i indirip hazırlar.
   - Uygulamayı `.exe` paketine dönüştürür.
3. İşlem bitince oluşan **`dist/DownX`** klasörüne girin.
4. **`DownX.exe`** dosyasını çalıştırın.

---

## 🐧 Bazzite OS / Linux Kurulumu

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
2️⃣ Doğrudan Çalıştırma (Bazzite'de)
Bash

# Python paketlerini kur
pip install --user -r requirements.txt

# Çalıştır
python launcher.py
⚙️ Spotify API Kurulumu (İsteğe Bağlı)
https://developer.spotify.com/dashboard adresine git

Yeni bir app oluştur

Client ID ve Client Secret'i kopyala

Uygulama içinde Ayarlar sekmesinde yapıştır

🎨 Özellikler
🔍 Akıllı Arama - YouTube ve Spotify'dan ara

📥 Çoklu İndirme - Eş zamanlı indirme desteği

🎵 Otomatik Etiketleme - ID3 tags + kapak resmi

📊 Canlı İstatistikler - Gerçek zamanlı ilerleme

🌙 Koyu Tema - Bazzite OS ve Windows uyumlu tasarım

🚗 Teyp Modu - Eski teypler için kapak resmini otomatik küçültme

🔧 Sorun Giderme
Windows: "Python Bulunamadı"
Python'u silip tekrar yükleyin ve yükleme ekranının en altındaki "Add Python to PATH" seçeneğini işaretlediğinizden emin olun.

Linux: GTK4 Bulunamadı
Bash

sudo dnf install gtk4-devel libadwaita-devel
Linux: FFmpeg Bulunamadı
Bash

sudo dnf install ffmpeg ffmpeg-libs
💡 Kullanım İpuçları
Toplu İndirme: TXT dosyasına linkleri yazın, "TXT Yükle" butonuna tıklayın

Hızlı Yapıştır: Link'i kopyalayın, "Yapıştır" butonuna tıklayın

Playlist Desteği: Spotify/YouTube playlist linklerini direkt yapıştırın

Taşınabilirlik: Windows sürümünü (dist/DownX klasörü) USB belleğe atıp başka bilgisayarda çalıştırabilirsiniz.

📝 Notlar
Windows: İndirme klasörü: Belgelerim/Music/4kTube/

Linux: İndirme klasörü: ~/Music/4kTube/

Linux: Bazzite OS'nin immutable yapısı nedeniyle Distrobox kullanımı önerilir.

İlk çalıştırmada bağımlılıklar kontrol edilir.

Keyifli Kullanımlar! 🎧
