"""
4KTube Free - Settings & Configuration
Windows ve Linux uyumlu versiyon
"""

import os
import sys
import json
from pathlib import Path

# Platform detection
IS_WINDOWS = sys.platform == 'win32'
IS_LINUX = sys.platform.startswith('linux')

# Platform-specific paths
if IS_WINDOWS:
    # Windows: %APPDATA%\4kTube
    CONFIG_DIR = os.path.join(os.getenv('APPDATA'), '4kTube')
    DEFAULT_DOWNLOAD_DIR = os.path.join(os.getenv('USERPROFILE'), 'Music', '4kTube Downloads')
    CACHE_DIR = os.path.join(os.getenv('LOCALAPPDATA'), '4kTube', 'cache')
else:
    # Linux: ~/.config/4ktube
    CONFIG_DIR = os.path.expanduser("~/.config/4ktube")
    DEFAULT_DOWNLOAD_DIR = os.path.expanduser("~/Music/4kTube")
    CACHE_DIR = os.path.expanduser("~/.cache/4ktube")

# Create directories
os.makedirs(CONFIG_DIR, exist_ok=True)
os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)
os.makedirs(CACHE_DIR, exist_ok=True)

# File paths
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.json")
COOKIES_FILE = os.path.join(CONFIG_DIR, "cookies.txt")
LOG_FILE = os.path.join(CONFIG_DIR, "app.log")
TASKS_FILE = os.path.join(CONFIG_DIR, "tasks.json")

# Default configuration
DEFAULT_CONFIG = {
    "download_dir": DEFAULT_DOWNLOAD_DIR,
    "download_mode": "audio",
    "audio_quality": "320",
    "video_quality": "1080",
    "audio_format": "m4a",
    "video_format": "mp4",
    "video_codec": "h264",
    "concurrent_downloads": 3,
    "skip_existing": True,
    "embed_metadata": True,
    "embed_thumbnail": True,
    "use_sponsorblock": False,
    "theme": "dark",
    "language": "tr",
    "show_notifications": True,
}

# Global config instance
GLOBAL_CONFIG = {}


def load_config():
    """Load configuration from file"""
    global GLOBAL_CONFIG

    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                loaded_config = json.load(f)

            # Merge with defaults (add missing keys)
            GLOBAL_CONFIG = {**DEFAULT_CONFIG, **loaded_config}

            # Validate download directory
            if not os.path.exists(GLOBAL_CONFIG.get("download_dir", "")):
                GLOBAL_CONFIG["download_dir"] = DEFAULT_DOWNLOAD_DIR
                os.makedirs(DEFAULT_DOWNLOAD_DIR, exist_ok=True)

            print(f"[CONFIG] Yüklendi: {CONFIG_FILE}")
            return GLOBAL_CONFIG

        except Exception as e:
            print(f"[CONFIG HATA] Yüklenemedi: {e}")
            GLOBAL_CONFIG = DEFAULT_CONFIG.copy()
            save_config()
    else:
        print(f"[CONFIG] Yeni config oluşturuluyor: {CONFIG_FILE}")
        GLOBAL_CONFIG = DEFAULT_CONFIG.copy()
        save_config()

    return GLOBAL_CONFIG


def save_config():
    """Save configuration to file"""
    global GLOBAL_CONFIG

    try:
        # Ensure download directory exists
        download_dir = GLOBAL_CONFIG.get("download_dir", DEFAULT_DOWNLOAD_DIR)
        os.makedirs(download_dir, exist_ok=True)

        with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
            json.dump(GLOBAL_CONFIG, f, indent=4, ensure_ascii=False)

        print(f"[CONFIG] Kaydedildi: {CONFIG_FILE}")
        return True

    except Exception as e:
        print(f"[CONFIG HATA] Kaydedilemedi: {e}")
        return False


def get_download_dir():
    """Get current download directory"""
    return GLOBAL_CONFIG.get("download_dir", DEFAULT_DOWNLOAD_DIR)


def update_download_dir(new_dir):
    """Update download directory"""
    global GLOBAL_CONFIG

    if new_dir and os.path.isdir(new_dir):
        GLOBAL_CONFIG["download_dir"] = new_dir
        save_config()
        print(f"[CONFIG] İndirme klasörü güncellendi: {new_dir}")
        return True

    return False


def get_config_value(key, default=None):
    """Get a config value by key"""
    return GLOBAL_CONFIG.get(key, default)


def set_config_value(key, value):
    """Set a config value"""
    global GLOBAL_CONFIG
    GLOBAL_CONFIG[key] = value
    save_config()


def reset_config():
    """Reset configuration to defaults"""
    global GLOBAL_CONFIG
    GLOBAL_CONFIG = DEFAULT_CONFIG.copy()
    save_config()
    print("[CONFIG] Varsayılan ayarlara sıfırlandı")


def print_config_summary():
    """Print configuration summary"""
    print("\n" + "="*70)
    print("📁 YAPIL ANDIRMA BİLGİLERİ")
    print("="*70)
    print(f"│ Platform: {'Windows' if IS_WINDOWS else 'Linux'}")
    print(f"│ Config Dir: {CONFIG_DIR}")
    print(f"│ Download Dir: {get_download_dir()}")
    print(f"│ Cache Dir: {CACHE_DIR}")
    print("─"*70)

    mode = GLOBAL_CONFIG.get("download_mode", "audio")
    audio_quality = GLOBAL_CONFIG.get("audio_quality", "192")
    video_quality = GLOBAL_CONFIG.get("video_quality", "1080")
    audio_format = GLOBAL_CONFIG.get("audio_format", "mp3")
    video_format = GLOBAL_CONFIG.get("video_format", "mp4")
    concurrent = GLOBAL_CONFIG.get("concurrent_downloads", 3)
    skip_existing = GLOBAL_CONFIG.get("skip_existing", True)
    metadata = GLOBAL_CONFIG.get("embed_metadata", True)
    thumbnail = GLOBAL_CONFIG.get("embed_thumbnail", True)

    # Safe formatting - handle None values
    audio_format_display = audio_format.upper() if audio_format else "MP3"
    video_format_display = video_format.upper() if video_format else "MP4"

    print(f"│ Mod: {mode.upper():50} │")
    print(f"│ Ses Kalitesi: {audio_quality} kbps{' '*40} │")
    print(f"│ Video Kalitesi: {video_quality}p{' '*40} │")
    print(f"│ Ses Format: {audio_format_display:50} │")
    print(f"│ Video Format: {video_format_display:50} │")
    print(f"│ Eş Zamanlı: {concurrent} indirme{' '*40} │")
    print(f"│ Mevcut Atla: {'✓' if skip_existing else '✗'}{' '*50} │")
    print(f"│ Metadata: {'✓' if metadata else '✗'}{' '*50} │")
    print(f"│ Kapak Resmi: {'✓' if thumbnail else '✗'}{' '*50} │")
    print("="*70 + "\n")


# Initialize config on import
load_config()


# Windows-specific helpers
def get_windows_music_folder():
    """Get Windows Music folder path"""
    if IS_WINDOWS:
        try:
            import winreg
            key = winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders"
            )
            music_folder, _ = winreg.QueryValueEx(key, "My Music")
            winreg.CloseKey(key)
            return os.path.expandvars(music_folder)
        except:
            pass

    return os.path.join(os.getenv('USERPROFILE', ''), 'Music') if IS_WINDOWS else None


def open_folder_in_explorer(path):
    """Open folder in Windows Explorer or Linux file manager"""
    if not os.path.exists(path):
        return False

    try:
        if IS_WINDOWS:
            os.startfile(path)
        elif IS_LINUX:
            import subprocess
            subprocess.Popen(['xdg-open', path])
        return True
    except Exception as e:
        print(f"[ERROR] Klasör açılamadı: {e}")
        return False


if __name__ == "__main__":
    print_config_summary()
    print(f"\nConfig file: {CONFIG_FILE}")
    print(f"Cookies file: {COOKIES_FILE}")
    print(f"Log file: {LOG_FILE}")
