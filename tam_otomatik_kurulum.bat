@echo off
setlocal EnableDelayedExpansion
color 0B
title DownX - Tam Otomatik Kurulum ve Build Araci

:: Proje klasorune gecisi garanti et
cd /d "%~dp0"

echo ========================================================
echo   DownX - BAZZITE STYLE - WINDOWS BUILD OTOMASYONU
echo ========================================================
echo.

:: 1. PYTHON KONTROLU
echo [1/6] Python kontrol ediliyor...
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [HATA] Python bulunamadi! Lutfen Python'u kurup "Add to PATH" secenegini isaretleyin.
    pause
    exit /b
)
echo    Python mevcut.

:: 2. SANAL ORTAM (VENV) TEMIZ KURULUM
echo.
echo [2/6] Sanal ortam (venv) hazirlaniyor...
:: Eski venv varsa sil (Hatalari onlemek icin)
if exist "venv" (
    echo    Eski bozuk ortam temizleniyor...
    rmdir /s /q "venv"
)

python -m venv venv
if %errorlevel% neq 0 (
    echo [HATA] Venv olusturulamadi. Python kurulumunuzu kontrol edin.
    pause
    exit /b
)
echo    Venv olusturuldu.

call venv\Scripts\activate
if %errorlevel% neq 0 (
    echo [HATA] Venv aktif edilemedi.
    pause
    exit /b
)
echo    Venv aktif edildi.

:: 3. KUTUPHANELER VE GTK4
echo.
echo [3/6] Gerekli kutuphaneler yukleniyor...
echo    Bu islem internet hizina gore biraz zaman alabilir...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller
pip install pygobject

:: 4. FFMPEG OTOMATIK INDIRME
echo.
echo [4/6] FFmpeg kontrol ediliyor ve indiriliyor...
if not exist "ffmpeg.exe" (
    echo    FFmpeg indiriliyor (PowerShell)...
    powershell -Command "Invoke-WebRequest -Uri 'https://github.com/BtbN/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-win64-gpl.zip' -OutFile 'ffmpeg.zip'"
    
    echo    Zip'ten cikariliyor...
    powershell -Command "Expand-Archive -Path 'ffmpeg.zip' -DestinationPath 'ffmpeg_temp' -Force"
    
    echo    Dosyalar yerlestiriliyor...
    REM Zip yapisina gore exe'yi bulup tasi
    for /r "ffmpeg_temp" %%f in (ffmpeg.exe) do move "%%f" . >nul
    for /r "ffmpeg_temp" %%f in (ffprobe.exe) do move "%%f" . >nul
    
    REM Temizlik
    del ffmpeg.zip
    rmdir /s /q ffmpeg_temp
    echo    FFmpeg hazir!
) else (
    echo    FFmpeg zaten mevcut.
)

:: 5. BUILD ISLEMI
echo.
echo [5/6] PyInstaller ile EXE olusturuluyor...
pyinstaller DownX.spec --clean --noconfirm

:: 6. SON RUTUSLAR
echo.
echo [6/6] Dosyalar 'dist' klasorune tasiniyor...
if exist "dist\DownX" (
    copy ffmpeg.exe "dist\DownX\" >nul
    copy ffprobe.exe "dist\DownX\" >nul
    echo    FFmpeg dosyalari pakete eklendi.
)

echo.
echo ========================================================
echo   ISLEM BASARIYLA TAMAMLANDI!
echo ========================================================
echo.
echo   Uygulamaniz su klasorde hazir:
echo   --^>  dist\DownX\DownX.exe
echo.
pause
