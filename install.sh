#!/bin/bash

# DownX GTK4 - Otomatik Kurulum Script (DEBUG MODU)
# Bazzite OS uyumlu

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎵 DownX GTK4 Kurulumu Başlatılıyor... (DEBUG MODE)${NC}"
echo ""

# Root kontrolü
if [ "$EUID" -eq 0 ]; then 
   echo -e "${RED}❌ Root olarak çalıştırmayın!${NC}"
   exit 1
fi

# Kurulum dizini
INSTALL_DIR="$HOME/.local/share/downx"
BIN_DIR="$HOME/.local/bin"
DESKTOP_DIR="$HOME/.local/share/applications"
ICON_DIR="$HOME/.local/share/icons/hicolor/256x256/apps"

echo -e "${BLUE}📁 Dizinler oluşturuluyor...${NC}"
mkdir -p "$INSTALL_DIR"
mkdir -p "$BIN_DIR"
mkdir -p "$DESKTOP_DIR"
mkdir -p "$ICON_DIR"

# Python bağımlılıklarını kontrol et
echo -e "${BLUE}📦 Python bağımlılıkları kontrol ediliyor...${NC}"

REQUIRED_PACKAGES=(
    "yt-dlp"
    "spotipy"
    "mutagen"
    "requests"
    "Pillow"
)

MISSING_PACKAGES=()

for package in "${REQUIRED_PACKAGES[@]}"; do
    package_import=${package//-/_}
    if ! python3 -c "import ${package_import}" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
        echo -e "${YELLOW}⚠️  Eksik: $package${NC}"
    else
        echo -e "${GREEN}✅ $package${NC}"
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${BLUE}📥 Eksik paketler yükleniyor: ${MISSING_PACKAGES[*]}${NC}"
    pip install --break-system-packages "${MISSING_PACKAGES[@]}"
fi

# FFmpeg kontrolü
echo -e "${BLUE}🎬 FFmpeg kontrolü...${NC}"
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}⚠️  FFmpeg bulunamadı!${NC}"
    echo -e "${BLUE}Yüklemek için: rpm-ostree install ffmpeg${NC}"
    echo -e "${BLUE}Sonra reboot yapın ve tekrar çalıştırın.${NC}"
    exit 1
else
    echo -e "${GREEN}✅ FFmpeg: $(ffmpeg -version | head -1)${NC}"
fi

# Dosyaları kopyala
echo -e "${BLUE}📂 Dosyalar kopyalanıyor...${NC}"

if [ -d "DownX-gtk4" ]; then
    echo -e "${BLUE}Lokal dizinden kopyalanıyor...${NC}"
    cp -r DownX-gtk4/* "$INSTALL_DIR/"
else
    echo -e "${BLUE}📥 GitHub'dan indiriliyor...${NC}"
    if command -v git &> /dev/null; then
        git clone https://github.com/kubilaysen1/DownX-gtk4.git /tmp/downx-temp
    else
        echo -e "${YELLOW}⚠️  Git yok, wget kullanılıyor...${NC}"
        wget https://github.com/kubilaysen1/DownX-gtk4/archive/refs/heads/main.zip -O /tmp/downx.zip
        unzip -q /tmp/downx.zip -d /tmp/
        mv /tmp/DownX-gtk4-main /tmp/downx-temp
    fi
    
    cp -r /tmp/downx-temp/* "$INSTALL_DIR/"
    rm -rf /tmp/downx-temp /tmp/downx.zip 2>/dev/null || true
fi

# Debug başlatıcı oluştur
cat > "$BIN_DIR/downx-debug" << 'DEBUGLAUNCHER'
#!/bin/bash
echo "🐛 DownX Debug Modu"
echo "=================="
echo ""
cd "$HOME/.local/share/downx"

echo "📦 Paket kontrolü:"
for pkg in yt_dlp spotipy mutagen requests PIL; do
    if python3 -c "import $pkg" 2>/dev/null; then
        echo "✅ $pkg"
    else
        echo "❌ $pkg"
    fi
done

echo ""
echo "🚀 Başlatılıyor..."
echo ""

export PYTHONUNBUFFERED=1
python3 -u gui.py 2>&1 | tee ~/downx-debug.log
DEBUGLAUNCHER

chmod +x "$BIN_DIR/downx-debug"

# Normal başlatıcı script oluştur
cat > "$BIN_DIR/downx" << 'LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/downx"
python3 gui.py "$@" 2>&1 | tee -a ~/downx.log
LAUNCHER

chmod +x "$BIN_DIR/downx"

# Desktop dosyası oluştur
cat > "$DESKTOP_DIR/downx.desktop" << 'DESKTOP'
[Desktop Entry]
Name=DownX
Comment=Modern Spotify/YouTube Downloader
Exec=downx
Icon=downx
Terminal=false
Type=Application
Categories=AudioVideo;Audio;Music;
Keywords=spotify;youtube;download;music;
StartupNotify=true
DESKTOP

# Desktop dosyası oluştur (DEBUG)
cat > "$DESKTOP_DIR/downx-debug.desktop" << 'DESKTOPDBG'
[Desktop Entry]
Name=DownX (Debug)
Comment=Modern Spotify/YouTube Downloader (Debug Mode)
Exec=downx-debug
Icon=downx
Terminal=true
Type=Application
Categories=AudioVideo;Audio;Music;
Keywords=spotify;youtube;download;music;debug;
StartupNotify=true
DESKTOPDBG

# İkon oluştur
cat > "$ICON_DIR/downx.svg" << 'ICON'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <defs>
    <linearGradient id="grad1" x1="0%" y1="0%" x2="0%" y2="100%">
      <stop offset="0%" style="stop-color:#3584e4;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#1c71d8;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="256" height="256" rx="40" fill="url(#grad1)"/>
  <path d="M 128 60 L 128 150 M 90 120 L 128 158 L 166 120" 
        stroke="white" stroke-width="16" stroke-linecap="round" 
        stroke-linejoin="round" fill="none"/>
  <rect x="70" y="180" width="116" height="16" rx="8" fill="white"/>
</svg>
ICON

# Desktop database güncelle
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# PATH kontrolü
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${YELLOW}⚠️  $BIN_DIR PATH'de değil!${NC}"
    echo -e "${BLUE}Şunu .bashrc veya .zshrc'ye ekle:${NC}"
    echo -e "${GREEN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo ""
    
    # Otomatik ekle
    if [ -f "$HOME/.bashrc" ]; then
        if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc"; then
            echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
            echo -e "${GREEN}✅ .bashrc'ye eklendi!${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}✅ DownX başarıyla kuruldu!${NC}"
echo ""
echo -e "${BLUE}🚀 Başlatmak için:${NC}"
echo -e "   ${GREEN}downx${NC}          # Normal mod"
echo -e "   ${GREEN}downx-debug${NC}    # Debug mod (hatalar terminalde)"
echo ""
echo -e "${BLUE}📄 Log dosyaları:${NC}"
echo -e "   ${GREEN}~/downx.log${NC}       # Normal log"
echo -e "   ${GREEN}~/downx-debug.log${NC} # Debug log"
echo ""
echo -e "${BLUE}🗑️  Kaldırmak için:${NC}"
echo -e "   ${GREEN}~/.local/share/downx/uninstall.sh${NC}"
echo ""

# Uninstall script oluştur
cat > "$INSTALL_DIR/uninstall.sh" << 'UNINSTALL'
#!/bin/bash
echo "🗑️  DownX kaldırılıyor..."
rm -rf "$HOME/.local/share/downx"
rm -f "$HOME/.local/bin/downx"
rm -f "$HOME/.local/bin/downx-debug"
rm -f "$HOME/.local/share/applications/downx.desktop"
rm -f "$HOME/.local/share/applications/downx-debug.desktop"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/downx.svg"
rm -f "$HOME/downx.log"
rm -f "$HOME/downx-debug.log"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "✅ DownX kaldırıldı!"
UNINSTALL

chmod +x "$INSTALL_DIR/uninstall.sh"

# Test
echo -e "${BLUE}🧪 Test ediliyor...${NC}"
if python3 -c "import sys; sys.path.insert(0, '$INSTALL_DIR'); import gui" 2>/dev/null; then
    echo -e "${GREEN}✅ Python modülleri OK${NC}"
else
    echo -e "${RED}⚠️  Python import hatası! downx-debug ile çalıştırın${NC}"
fi

echo ""
echo -e "${YELLOW}💡 İPUCU: İndirme hataları için 'downx-debug' kullanın!${NC}"
echo ""
