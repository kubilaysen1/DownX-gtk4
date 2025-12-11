# -*- mode: python ; coding: utf-8 -*-
import sys
import os
import site
from PyInstaller.utils.hooks import collect_data_files, collect_submodules

block_cipher = None
app_name = "DownX"

# --- GTK ve Adwaita Yollarını Otomatik Bul ---
# Sanal ortamdaki veya sistemdeki site-packages yolunu bul
site_packages = site.getsitepackages()[1] if len(site.getsitepackages()) > 1 else site.getsitepackages()[0]
gnome_path = os.path.join(site_packages, 'gnome')

# Binaryler ve Veriler
binaries = []
datas = []

# Eğer gvsbuild ile kurulduysa 'gnome' klasörünü ekle
if os.path.exists(gnome_path):
    print(f"GTK4 Runtime bulundu: {gnome_path}")
    # DLL'leri binaries olarak ekle
    binaries.append((os.path.join(gnome_path, 'bin', '*.dll'), '.'))
    # Şema ve ikonları datas olarak ekle
    datas.append((os.path.join(gnome_path, 'share'), 'share'))
    datas.append((os.path.join(gnome_path, 'lib'), 'lib'))

# Diğer Python kütüphane verileri
datas += collect_data_files('gi')
datas += collect_data_files('mutagen')

hiddenimports = [
    'gi', 'gi.repository.Gtk', 'gi.repository.Adw', 'gi.repository.Gio',
    'gi.repository.GLib', 'gi.repository.GObject', 'yt_dlp', 'spotipy',
    'PIL', 'mutagen'
]

a = Analysis(
    ['gui.py'],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['tkinter', 'unittest'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=app_name,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False, # Konsol penceresi olmasın (Hata ayıklamak istersen True yap)
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='app.ico' if os.path.exists('app.ico') else None
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=app_name,
)
