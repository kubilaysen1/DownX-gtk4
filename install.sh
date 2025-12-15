#!/bin/bash

# DownX GTK4 - Otomatik Kurulum Script
# Bazzite OS uyumlu

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}🎵 DownX GTK4 Kurulumu Başlatılıyor...${NC}"
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
    if ! python3 -c "import ${package//-/_}" 2>/dev/null; then
        MISSING_PACKAGES+=("$package")
    fi
done

if [ ${#MISSING_PACKAGES[@]} -ne 0 ]; then
    echo -e "${BLUE}📥 Eksik paketler yükleniyor: ${MISSING_PACKAGES[*]}${NC}"
    pip install --break-system-packages "${MISSING_PACKAGES[@]}"
fi

# FFmpeg kontrolü
if ! command -v ffmpeg &> /dev/null; then
    echo -e "${RED}⚠️  FFmpeg bulunamadı!${NC}"
    echo -e "${BLUE}Yüklemek için: rpm-ostree install ffmpeg${NC}"
    echo -e "${BLUE}Sonra reboot yapın ve tekrar çalıştırın.${NC}"
    exit 1
fi

# Dosyaları kopyala
echo -e "${BLUE}📂 Dosyalar kopyalanıyor...${NC}"

# GitHub'dan indir
if [ -d "DownX-gtk4" ]; then
    cp -r DownX-gtk4/* "$INSTALL_DIR/"
else
    echo -e "${BLUE}📥 GitHub'dan indiriliyor...${NC}"
    git clone https://github.com/kubilaysen1/DownX-gtk4.git /tmp/downx-temp
    cp -r /tmp/downx-temp/* "$INSTALL_DIR/"
    rm -rf /tmp/downx-temp
fi

# Başlatıcı script oluştur
cat > "$BIN_DIR/downx" << 'LAUNCHER'
#!/bin/bash
cd "$HOME/.local/share/downx"
python3 gui.py "$@"
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

# İkon oluştur (basit SVG)
cat > "$ICON_DIR/downx.svg" << 'ICON'
<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" rx="40" fill="#3584e4"/>
  <text x="128" y="180" font-size="160" text-anchor="middle" fill="white" font-family="sans-serif" font-weight="bold">↓</text>
</svg>
ICON

# Desktop database güncelle
if command -v update-desktop-database &> /dev/null; then
    update-desktop-database "$DESKTOP_DIR" 2>/dev/null || true
fi

# PATH kontrolü
if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo ""
    echo -e "${RED}⚠️  $BIN_DIR PATH'de değil!${NC}"
    echo -e "${BLUE}Şunu .bashrc veya .zshrc'ye ekle:${NC}"
    echo -e "${GREEN}export PATH=\"\$HOME/.local/bin:\$PATH\"${NC}"
    echo ""
fi

echo ""
echo -e "${GREEN}✅ DownX başarıyla kuruldu!${NC}"
echo ""
echo -e "${BLUE}🚀 Başlatmak için:${NC}"
echo -e "   ${GREEN}downx${NC}  (veya uygulama menüsünden)"
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
rm -f "$HOME/.local/share/applications/downx.desktop"
rm -f "$HOME/.local/share/icons/hicolor/256x256/apps/downx.svg"
update-desktop-database "$HOME/.local/share/applications" 2>/dev/null || true
echo "✅ DownX kaldırıldı!"
UNINSTALL

chmod +x "$INSTALL_DIR/uninstall.sh"
