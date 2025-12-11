#!/usr/bin/env python3
"""
DownX - Bazzite Style Launcher
🚀 Dependency checker and launcher
"""

import sys
import subprocess
import shutil
from pathlib import Path

# Colors
class C:
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    PURPLE = '\033[95m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_header():
    print(f"\n{C.PURPLE}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.END}")
    print(f"{C.PURPLE}{C.BOLD}   DownX - Bazzite Style Edition{C.END}")
    print(f"{C.PURPLE}{C.BOLD}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━{C.END}\n")

def check_status(name, check_fn):
    """Check and print status"""
    print(f"{C.BLUE}→{C.END} Checking {name}...", end=" ")
    result = check_fn()
    if result:
        print(f"{C.GREEN}✓{C.END}")
        return True
    else:
        print(f"{C.RED}✗{C.END}")
        return False

def check_python():
    """Check Python version"""
    return sys.version_info >= (3, 8)

def check_gtk():
    """Check GTK4"""
    try:
        import gi
        gi.require_version("Gtk", "4.0")
        gi.require_version("Adw", "1")
        from gi.repository import Gtk, Adw
        return True
    except:
        return False

def check_package(name):
    """Check Python package"""
    try:
        __import__(name)
        return True
    except ImportError:
        return False

def check_system_tool(name):
    """Check system tool"""
    return shutil.which(name) is not None

def main():
    print_header()
    
    # Checks
    checks = [
        ("Python 3.8+", check_python),
        ("GTK 4.0", check_gtk),
        ("yt-dlp", lambda: check_package("yt_dlp")),
        ("spotipy", lambda: check_package("spotipy")),
        ("mutagen", lambda: check_package("mutagen")),
        ("Pillow", lambda: check_package("PIL")),
        ("FFmpeg", lambda: check_system_tool("ffmpeg")),
    ]
    
    failed = []
    for name, check in checks:
        if not check_status(name, check):
            failed.append(name)
    
    if failed:
        print(f"\n{C.YELLOW}⚠️  Missing dependencies:{C.END}")
        for item in failed:
            print(f"  • {item}")
        
        print(f"\n{C.BLUE}ℹ️  Install with:{C.END}")
        print(f"  pip install -r requirements.txt")
        print(f"  sudo dnf install gtk4 libadwaita ffmpeg  # Fedora/Bazzite")
        sys.exit(1)
    
    # Launch
    print(f"\n{C.GREEN}{C.BOLD}🚀 All dependencies OK! Launching...{C.END}\n")
    
    try:
        subprocess.run([sys.executable, "gui.py"])
    except KeyboardInterrupt:
        print(f"\n{C.YELLOW}👋 Goodbye!{C.END}")

if __name__ == "__main__":
    main()
