@echo off
setlocal EnableDelayedExpansion
color 0B
title DownX - Windows Build Araci (FINAL FIX 6.0)

cd /d "%~dp0"

echo ========================================================
echo   DownX - TAM OTOMATIK BUILD SISTEMI (FINAL FIX 6.0)
echo   "Linux Script Enjeksiyonu + Path Fix"
echo ========================================================
echo.

REM ----------------------------------------------------------
REM 1. ADIM: TEMIZLIK
REM ----------------------------------------------------------
echo [1/8] Temizlik yapiliyor...
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"
if exist "build_helper.sh" del "build_helper.sh"
echo    [OK] Temizlik yapildi.

REM ----------------------------------------------------------
REM 2. ADIM: MSYS2 KONTROLU
REM ----------------------------------------------------------
echo.
echo [2/8] MSYS2 sistemi kontrol ediliyor...

if exist "C:\msys64\usr\bin\bash.exe" (
    echo    [OK] MSYS2 bulundu.
) else (
    echo    [!] MSYS2 bulunamadi. Otomatik indiriliyor...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/msys2/msys2-installer/releases/download/2024-01-13/msys2-x86_64-20240113.exe' -OutFile 'msys2_setup.exe'"
    
    if not exist "msys2_setup.exe" (
        color 0C
        echo [HATA] MSYS2 indirilemedi.
        pause
        exit /b
    )
    
    echo    [!] MSYS2 kuruluyor...
    start /wait msys2_setup.exe --confirm-command --accept-messages --root C:\msys64
    del msys2_setup.exe
    echo    [OK] MSYS2 kurulumu tamamlandi.
)

REM ----------------------------------------------------------
REM 3. ADIM: SPEC DOSYASI
REM ----------------------------------------------------------
echo.
echo [3/8] DownX.spec dosyasi hazirlaniyor...

(
echo # -*- mode: python ; coding: utf-8 -*-
echo import sys
echo import os
echo from PyInstaller.utils.hooks import collect_data_files
echo.
echo block_cipher = None
echo app_name = "DownX"
echo.
echo datas = []
echo datas += collect_data_files^('mutagen'^)
echo datas += collect_data_files^('certifi'^)
echo.
echo # MSYS2 Yollari
echo msys_prefix = sys.prefix
echo datas.append^(^(os.path.join^(msys_prefix, 'share', 'glib-2.0', 'schemas'^), 'share/glib-2.0/schemas'^)^)
echo datas.append^(^(os.path.join^(msys_prefix, 'share', 'icons'^), 'share/icons'^)^)
echo datas.append^(^(os.path.join^(msys_prefix, 'lib', 'gdk-pixbuf-2.0'^), 'lib/gdk-pixbuf-2.0'^)^)
echo.
echo hiddenimports = [
echo     'gi', 'gi.repository.Gtk', 'gi.repository.Adw', 'gi.repository.Gio', 
echo     'gi.repository.GLib', 'gi.repository.GObject', 'yt_dlp', 'spotipy', 
echo     'PIL', 'mutagen'
echo ]
echo.
echo a = Analysis^(
echo     ['gui.py'],
echo     pathex=[],
echo     binaries=[],
echo     datas=datas,
echo     hiddenimports=hiddenimports,
echo     hookspath=[],
echo     hooksconfig={},
echo     runtime_hooks=[],
echo     excludes=['tkinter', 'unittest'],
echo     win_no_prefer_redirects=False,
echo     win_private_assemblies=False,
echo     cipher=block_cipher,
echo     noarchive=False,
echo ^)
echo pyz = PYZ^(a.pure, a.zipped_data, cipher=block_cipher^)
echo.
echo exe = EXE^(
echo     pyz,
echo     a.scripts,
echo     [],
echo     exclude_binaries=True,
echo     name=app_name,
echo     debug=False,
echo     bootloader_ignore_signals=False,
echo     strip=False,
echo     upx=True,
echo     console=True, 
echo     disable_windowed_traceback=False,
echo     argv_emulation=False,
echo     target_arch=None,
echo     codesign_identity=None,
echo     entitlements_file=None,
echo     icon='app.ico' if os.path.exists^('app.ico'^) else None
echo ^)
echo.
echo coll = COLLECT^(
echo     exe,
echo     a.binaries,
echo     a.zipfiles,
echo     a.datas,
echo     strip=False,
echo     upx=True,
echo     upx_exclude=[],
echo     name=app_name,
echo ^)
) > DownX.spec

echo    [OK] Spec dosyasi yenilendi.

REM ----------------------------------------------------------
REM 4. ADIM: CEKIRDEK GUNCELLEME VE RESET
REM ----------------------------------------------------------
echo.
echo [4/8] MSYS2 Cekirdegi Guncelleniyor...
echo    Bu islemden sonra MSYS2 surecleri zorla kapatilacak.

C:\msys64\usr\bin\bash.exe -lc "pacman -S --noconfirm --needed --disable-download-timeout msys2-runtime"

echo.
echo    [RESET] Fork hatasini onlemek icin surecler temizleniyor...
taskkill /F /IM gpg-agent.exe >nul 2>&1
taskkill /F /IM dirmngr.exe >nul 2>&1
taskkill /F /IM bash.exe >nul 2>&1
taskkill /F /IM mintty.exe >nul 2>&1
timeout /t 2 >nul

REM ----------------------------------------------------------
REM 5. ADIM: BUILD SCRIPTINI OLUSTURMA (GUVENLI MOD)
REM ----------------------------------------------------------
echo.
echo [5/8] Linux build scripti olusturuluyor...

REM Ozel karakter sorunu olmasin diye gecici olarak kapatiyoruz
setlocal DisableDelayedExpansion
(
echo #!/bin/bash
echo source /etc/profile
echo export PATH="/mingw64/bin:$PATH"
echo.
echo echo "--- PAKET KURULUMU BASLIYOR ---"
echo pacman -Sy
echo.
echo pacman -S --noconfirm --needed --disable-download-timeout mingw-w64-x86_64-python mingw-w64-x86_64-python-gobject mingw-w64-x86_64-gtk4 mingw-w64-x86_64-python-pip mingw-w64-x86_64-python-pyinstaller mingw-w64-x86_64-ffmpeg mingw-w64-x86_64-adwaita-icon-theme gcc pkg-config
echo.
echo echo "--- PYTHON PAKETLERI KURULUYOR ---"
echo python -m pip install -r requirements.txt --break-system-packages --no-cache-dir
echo.
echo echo "--- EXE DERLENIYOR ---"
echo pyinstaller DownX.spec --clean --noconfirm
) > build_helper.sh
endlocal

if exist "build_helper.sh" (
    echo    [OK] Yardimci script olusturuldu.
) else (
    color 0C
    echo    [HATA] Script dosyasi olusturulamadi!
    pause
    exit /b
)

REM ----------------------------------------------------------
REM 6. ADIM: BUILD SCRIPTINI CALISTIRMA
REM ----------------------------------------------------------
echo.
echo [6/8] Derleme islemi baslatiliyor...
echo    MSYS2 uzerinde komutlar calistirilacak.

REM Windows yolunu Linux formatina cevir (Ters slashlari duzelt)
set "LINUX_PATH=%cd:\=/%"

REM Bash komutunu calistir (Dogru yola giderek)
C:\msys64\usr\bin\bash.exe -l -c "cd '%LINUX_PATH%'; chmod +x build_helper.sh; ./build_helper.sh"

REM ----------------------------------------------------------
REM 7. ADIM: SONUC KONTROLU
REM ----------------------------------------------------------
echo.
echo [7/8] Sonuc kontrol ediliyor...

if exist "dist\DownX\DownX.exe" (
    color 0A
    echo.
    echo    [BASARILI] EXE dosyasi olusturuldu!
    
    echo    FFmpeg kopyalaniyor...
    if exist "C:\msys64\mingw64\bin\ffmpeg.exe" (
        copy "C:\msys64\mingw64\bin\ffmpeg.exe" "dist\DownX\" >nul
        copy "C:\msys64\mingw64\bin\ffprobe.exe" "dist\DownX\" >nul
    )
    
    if exist "app.ico" copy "app.ico" "dist\DownX\" >nul
    
    REM Scripti temizle
    if exist "build_helper.sh" del "build_helper.sh"
    
    echo.
    echo ========================================================
    echo   ISLEM BASARIYLA TAMAMLANDI KANKACIM!
    echo ========================================================
    echo.
    echo   Klasorun surada hazir:
    echo   --^> %~dp0dist\DownX
) else (
    color 0C
    echo.
    echo    [HATA] EXE olusturulamadi. 
    echo    MSYS2 icindeki islemler sirasinda hata olustu.
)

echo.
echo   (Kapatmak icin bir tusa bas)
pause
