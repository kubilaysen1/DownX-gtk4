#!/usr/bin/env python3
"""
DownX - Modern GTK4 Application (Bazzite Style)
🎨 Clean, modern interface inspired by Bazzite OS
⚡ High performance with batch updates
"""

import sys
import gi
from pathlib import Path

gi.require_version('Gtk', '4.0')
gi.require_version('Adw', '1')

from gi.repository import Gtk, Adw, Gio, GLib

# --- BAZZITE-STYLE CSS ---
BAZZITE_CSS = """
/* 🎨 BAZZITE-INSPIRED THEME */

/* Modern purple/blue accent colors */
window {
    background-color: @window_bg_color;
}

/* Purple accent for important actions */
.suggested-action {
    background: linear-gradient(to bottom, #7c3aed, #6d28d9);
    color: white;
    font-weight: bold;
}

.suggested-action:hover {
    background: linear-gradient(to bottom, #8b5cf6, #7c3aed);
}

/* Destructive actions (red) */
.destructive-action {
    background: linear-gradient(to bottom, #ef4444, #dc2626);
}

.destructive-action:hover {
    background: linear-gradient(to bottom, #f87171, #ef4444);
}

/* Clean card style */
.card {
    background-color: @card_bg_color;
    border-radius: 12px;
    padding: 16px;
    margin: 8px;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Status indicators */
.status-pending {
    color: #a855f7;
}

.status-downloading {
    color: #3b82f6;
}

.status-completed {
    color: #10b981;
}

.status-error {
    color: #ef4444;
}

/* Pill buttons (rounded) */
.pill {
    border-radius: 24px;
    padding: 8px 20px;
}

/* Smooth animations */
* {
    transition: all 200ms cubic-bezier(0.4, 0.0, 0.2, 1);
}

/* Modern progress bars */
progressbar progress {
    background: linear-gradient(90deg, #7c3aed, #3b82f6);
}

/* Search entry styling */
entry.search {
    border-radius: 24px;
    padding: 12px 20px;
    min-height: 48px;
}

/* Navigation sidebar (for list items) */
.navigation-sidebar {
    background-color: @view_bg_color;
}

.navigation-sidebar row {
    border-radius: 8px;
    margin: 2px 8px;
}

.navigation-sidebar row:selected {
    background-color: alpha(@accent_color, 0.15);
}

/* Toolbar styling */
headerbar {
    background: @headerbar_bg_color;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.1);
}

/* Preferences window */
preferencespage > scrolledwindow > viewport > clamp > box {
    margin: 24px 12px;
}

preferencesgroup {
    margin-bottom: 24px;
}
"""

# --- DEPENDENCY CHECK ---
def check_dependencies():
    """Check critical dependencies"""
    missing = []
    
    try:
        import yt_dlp
    except ImportError:
        missing.append("yt-dlp")
    
    try:
        import spotipy
    except ImportError:
        missing.append("spotipy")
    
    try:
        import mutagen
    except ImportError:
        missing.append("mutagen")
    
    try:
        from PIL import Image
    except ImportError:
        missing.append("Pillow")
    
    import shutil
    if not shutil.which("ffmpeg"):
        missing.append("ffmpeg (system)")
    
    return missing


# --- MODULE IMPORTS ---
try:
    from search_tab import SearchTab
except ImportError as e:
    print(f"⚠️ WARNING: search_tab import failed: {e}")
    SearchTab = None

try:
    from downloads_tab import DownloadsTab
except ImportError as e:
    print(f"⚠️ WARNING: downloads_tab import failed: {e}")
    DownloadsTab = None

try:
    from settings_tab import SettingsTab
except ImportError as e:
    print(f"⚠️ WARNING: settings_tab import failed: {e}")
    SettingsTab = None

try:
    from tools_tab import ToolsTab
except ImportError as e:
    print(f"⚠️ WARNING: tools_tab import failed: {e}")
    ToolsTab = None


class MainWindow(Adw.ApplicationWindow):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # --- THEME SETUP ---
        style_manager = Adw.StyleManager.get_default()
        style_manager.set_color_scheme(Adw.ColorScheme.PREFER_DARK)
        
        # Load custom CSS
        self._load_custom_css()
        
        self.set_title("DownX")
        self.set_default_size(1100, 750)
        self.set_icon_name("multimedia-video-player")
        
        # --- TOAST OVERLAY ---
        self.toast_overlay = Adw.ToastOverlay()
        
        # --- QUEUE MANAGER ---
        try:
            from queue_manager import QueueManager
            from spotify_client import SpotifyClient
            from youtube_client import YouTubeClient
            
            sp_client = SpotifyClient()
            yt_client = YouTubeClient()
            
            self.queue_manager = QueueManager(self, sp_client, yt_client)
            print("✅ Queue Manager started")
        except Exception as e:
            print(f"⚠️ Queue Manager failed: {e}")
            self.queue_manager = None
        
        self.connect("close-request", self.on_close_request)
        
        # --- MAIN LAYOUT ---
        self.toolbar_view = Adw.ToolbarView()
        self.toast_overlay.set_child(self.toolbar_view)
        self.set_content(self.toast_overlay)
        
        # 1. HEADER BAR
        header_bar = Adw.HeaderBar()
        self._add_header_buttons(header_bar)
        self.toolbar_view.add_top_bar(header_bar)
        
        # 2. CONTENT STACK
        self.stack = Adw.ViewStack()
        self.toolbar_view.set_content(self.stack)
        
        # --- ADD PAGES ---
        self._add_search_page()
        self._add_downloads_page()
        self._add_tools_page()
        self._add_settings_page()
        
        # 3. BOTTOM SWITCHER BAR
        switcher_bar = Adw.ViewSwitcherBar()
        switcher_bar.set_stack(self.stack)
        switcher_bar.set_reveal(True)
        self.toolbar_view.add_bottom_bar(switcher_bar)
    
    def _load_custom_css(self):
        """Load Bazzite-style CSS"""
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(BAZZITE_CSS.encode())
        Gtk.StyleContext.add_provider_for_display(
            self.get_display(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
        print("🎨 Bazzite-style CSS loaded")
    
    def _add_header_buttons(self, header_bar):
        """Add menu and info buttons to header"""
        # Menu button (right side)
        menu_button = Gtk.MenuButton()
        menu_button.set_icon_name("open-menu-symbolic")
        
        menu = Gio.Menu()
        menu.append("Hakkında", "app.about")
        menu.append("Çıkış", "app.quit")
        menu_button.set_menu_model(menu)
        
        header_bar.pack_end(menu_button)
        
        # Title
        title_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        icon = Gtk.Image.new_from_icon_name("multimedia-video-player")
        icon.set_pixel_size(24)
        title_label = Gtk.Label(label="DownX")
        title_label.add_css_class("title")
        
        title_box.append(icon)
        title_box.append(title_label)
        header_bar.set_title_widget(title_box)
    
    def _add_search_page(self):
        """Add search page"""
        if SearchTab:
            try:
                search_page = SearchTab(self)
                page = self.stack.add_named(search_page, "search")
                page.set_title("Ana Sayfa")
                page.set_icon_name("system-search-symbolic")
            except Exception as e:
                print(f"❌ Search page error: {e}")
                self._add_placeholder_page("search", "Ana Sayfa", 
                    "dialog-error-symbolic", f"Error: {e}")
        else:
            self._add_placeholder_page("search", "Ana Sayfa", 
                "dialog-warning-symbolic", "search_tab.py not found")
    
    def _add_downloads_page(self):
        """Add downloads page"""
        if DownloadsTab:
            try:
                downloads_page = DownloadsTab(self)
                page = self.stack.add_named(downloads_page, "downloads")
                page.set_title("İndirilenler")
                page.set_icon_name("folder-download-symbolic")
            except Exception as e:
                print(f"❌ Downloads page error: {e}")
                self._add_placeholder_page("downloads", "İndirilenler",
                    "dialog-error-symbolic", f"Error: {e}")
        else:
            self._add_placeholder_page("downloads", "İndirilenler",
                "dialog-warning-symbolic", "downloads_tab.py not found")
    
    def _add_tools_page(self):
        """Add tools page"""
        if ToolsTab:
            try:
                tools_page = ToolsTab(self)
                page = self.stack.add_named(tools_page, "tools")
                page.set_title("Araçlar")
                page.set_icon_name("applications-utilities-symbolic")
            except Exception as e:
                print(f"❌ Tools page error: {e}")
                self._add_placeholder_page("tools", "Araçlar",
                    "dialog-error-symbolic", f"Error: {e}")
        else:
            self._add_placeholder_page("tools", "Araçlar",
                "dialog-warning-symbolic", "tools_tab.py not found")
    
    def _add_settings_page(self):
        """Add settings page"""
        if SettingsTab:
            try:
                settings_page = SettingsTab(self)
                page = self.stack.add_named(settings_page, "settings")
                page.set_title("Ayarlar")
                page.set_icon_name("emblem-system-symbolic")
            except Exception as e:
                print(f"❌ Settings page error: {e}")
                self._add_placeholder_page("settings", "Ayarlar",
                    "dialog-error-symbolic", f"Error: {e}")
        else:
            self._add_placeholder_page("settings", "Ayarlar",
                "dialog-warning-symbolic", "settings_tab.py not found")
    
    def _add_placeholder_page(self, name, title, icon_name, text):
        """Placeholder for missing pages"""
        status_page = Adw.StatusPage()
        status_page.set_icon_name(icon_name)
        status_page.set_title(title)
        status_page.set_description(text)
        
        page = self.stack.add_named(status_page, name)
        page.set_title(title)
        page.set_icon_name(icon_name)
    
    def show_toast(self, message, timeout=3):
        """Show toast notification (Bazzite style)"""
        toast = Adw.Toast.new(message)
        toast.set_timeout(timeout)
        self.toast_overlay.add_toast(toast)
    
    def on_close_request(self, *args):
        return False


class DownXApp(Adw.Application):
    def __init__(self):
        super().__init__(
            application_id="com.kubilaysen.DownX",
            flags=Gio.ApplicationFlags.DEFAULT_FLAGS
        )
        
        # Actions
        self.create_action("quit", lambda *_: self.quit())
        self.create_action("about", self.on_about)
    
    def create_action(self, name, callback):
        """Create a simple action"""
        action = Gio.SimpleAction.new(name, None)
        action.connect("activate", callback)
        self.add_action(action)
    
    def on_about(self, action, param):
        """Show about dialog"""
        about = Adw.AboutWindow(
            transient_for=self.props.active_window,
            application_name="DownX",
            application_icon="multimedia-video-player",
            developer_name="Kubilay Şen",
            version="3.0.0",
            website="https://github.com/kubilaysen/downx",
            issue_url="https://github.com/kubilaysen/downx/issues",
            copyright="© 2025 Kubilay Şen",
            license_type=Gtk.License.GPL_3_0,
            developers=["Kubilay Şen"],
            designers=["Bazzite OS Team (inspiration)"]
        )
        about.present()
    
    def do_activate(self):
        """App activation"""
        if not self.props.active_window:
            # Check dependencies on first run
            missing = check_dependencies()
            if missing:
                print(f"⚠️ Missing dependencies: {', '.join(missing)}")
        
        win = self.props.active_window
        if not win:
            win = MainWindow(application=self)
        win.present()


if __name__ == "__main__":
    app = DownXApp()
    sys.exit(app.run(sys.argv))
