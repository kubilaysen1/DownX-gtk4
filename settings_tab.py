import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib
from pathlib import Path

# Ayarları çekiyoruz
from settings import GLOBAL_CONFIG, save_config, update_download_dir

class SettingsTab(Adw.PreferencesPage):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        # --- 1. GRUP: Temel Ayarlar ---
        group_basic = Adw.PreferencesGroup(title="Temel Ayarlar", description="İndirme konumu ve modu")
        self.add(group_basic)

        # İndirme Modu
        self.mode_model = Gtk.StringList()
        self.mode_model.append("Sadece Müzik (MP3)")
        self.mode_model.append("Video + Ses (MP4)")
        self.mode_model.append("Sadece Video")

        self.row_mode = Adw.ComboRow(title="İndirme Modu", model=self.mode_model)
        self.row_mode.set_icon_name("audio-x-generic-symbolic")

        modes = ["audio", "video+audio", "video"]
        current_mode = GLOBAL_CONFIG.get("download_mode", "audio")
        if current_mode in modes:
            self.row_mode.set_selected(modes.index(current_mode))

        self.row_mode.connect("notify::selected", self.on_mode_changed)
        group_basic.add(self.row_mode)

        # Klasör Seçimi
        self.row_folder = Adw.ActionRow(title="İndirme Klasörü")
        self.row_folder.set_subtitle(str(GLOBAL_CONFIG.get("download_dir", "~/Music")))
        self.row_folder.set_icon_name("folder-download-symbolic")

        btn_folder = Gtk.Button(icon_name="folder-open-symbolic")
        btn_folder.set_valign(Gtk.Align.CENTER)
        btn_folder.connect("clicked", self.on_folder_clicked)

        self.row_folder.add_suffix(btn_folder)
        group_basic.add(self.row_folder)

        # --- 2. GRUP: Kalite ve Özellikler ---
        group_quality = Adw.PreferencesGroup(title="Kalite ve Özellikler")
        self.add(group_quality)

        # Kalite
        quality_model = Gtk.StringList()
        for q in ["320 kbps (En İyi)", "256 kbps", "192 kbps (Standart)", "128 kbps"]:
            quality_model.append(q)

        self.row_quality = Adw.ComboRow(title="Ses Kalitesi", model=quality_model)
        self.row_quality.set_icon_name("audio-volume-high-symbolic")

        # Mevcut kaliteyi seç
        saved_q = GLOBAL_CONFIG.get("audio_quality", "192")
        for i, q in enumerate(["320", "256", "192", "128"]):
            if q in str(saved_q):
                self.row_quality.set_selected(i)
                break

        self.row_quality.connect("notify::selected", self.on_quality_changed)
        group_quality.add(self.row_quality)

        # Metadata
        self.row_meta = Adw.SwitchRow(title="Metadata Ekle")
        self.row_meta.set_subtitle("Şarkı bilgilerini dosyaya işle")
        self.row_meta.set_active(GLOBAL_CONFIG.get("embed_metadata", True))
        self.row_meta.connect("notify::active", self.on_switch_changed, "embed_metadata")
        group_quality.add(self.row_meta)

        # Thumbnail
        self.row_thumb = Adw.SwitchRow(title="Kapak Resmi")
        self.row_thumb.set_subtitle("Video resmini albüm kapağı yap")
        self.row_thumb.set_active(GLOBAL_CONFIG.get("embed_thumbnail", True))
        self.row_thumb.connect("notify::active", self.on_switch_changed, "embed_thumbnail")
        group_quality.add(self.row_thumb)

        # --- 3. GRUP: Spotify API ---
        group_api = Adw.PreferencesGroup(title="Spotify Bağlantısı", description="Şarkı listelerini çekmek için gereklidir")
        self.add(group_api)

        # Client ID
        self.entry_client_id = Adw.EntryRow(title="Client ID")
        self.entry_client_id.set_text(GLOBAL_CONFIG.get("spotify_client_id", ""))
        self.entry_client_id.connect("apply", self.on_api_changed, "spotify_client_id")
        group_api.add(self.entry_client_id)

        # Client Secret
        self.entry_secret = Adw.PasswordEntryRow(title="Client Secret")
        self.entry_secret.set_text(GLOBAL_CONFIG.get("spotify_client_secret", ""))
        self.entry_secret.connect("apply", self.on_api_changed, "spotify_client_secret")
        group_api.add(self.entry_secret)

        # --- 4. GRUP: Sıfırlama ---
        group_actions = Adw.PreferencesGroup()
        self.add(group_actions)

        btn_reset = Gtk.Button(label="Varsayılanlara Sıfırla")
        btn_reset.add_css_class("destructive-action")
        btn_reset.connect("clicked", self.on_reset_clicked)
        group_actions.add(btn_reset)

    # --- Olaylar (Logic) ---

    def on_mode_changed(self, row, param):
        """İndirme modu değiştiğinde"""
        modes = ["audio", "video+audio", "video"]
        selected_mode = modes[row.get_selected()]
        GLOBAL_CONFIG["download_mode"] = selected_mode
        save_config()
        print(f"[AYAR] Mod: {selected_mode}")

    def on_quality_changed(self, row, param):
        """Ses kalitesi değiştiğinde"""
        qualities = ["320", "256", "192", "128"]
        selected_q = qualities[row.get_selected()]
        GLOBAL_CONFIG["audio_quality"] = selected_q
        save_config()
        print(f"[AYAR] Kalite: {selected_q}kbps")

    def on_switch_changed(self, row, param, config_key):
        """Switch (metadata/thumbnail) değiştiğinde"""
        value = row.get_active()
        GLOBAL_CONFIG[config_key] = value
        save_config()
        print(f"[AYAR] {config_key}: {value}")

    def on_api_changed(self, entry, config_key):
        """Spotify API bilgileri değiştiğinde"""
        text = entry.get_text()
        GLOBAL_CONFIG[config_key] = text
        save_config()
        print(f"[AYAR] {config_key} güncellendi")

    def on_folder_clicked(self, btn):
        """Klasör seçme butonu tıklandığında"""
        dialog = Gtk.FileDialog()
        dialog.select_folder(self.parent_window, None, self.on_folder_selected)

    def on_folder_selected(self, dialog, result):
        """Klasör seçildiğinde"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self.row_folder.set_subtitle(path)
                GLOBAL_CONFIG["download_dir"] = path
                save_config()
                print(f"[AYAR] Klasör: {path}")
        except Exception as e:
            print(f"[AYAR HATA] Klasör seçilemedi: {e}")

    def on_reset_clicked(self, btn):
        """Ayarları sıfırla butonu"""
        from settings import DEFAULT_CONFIG
        
        # Varsayılan değerleri GLOBAL_CONFIG'e kopyala
        for key, value in DEFAULT_CONFIG.items():
            GLOBAL_CONFIG[key] = value
        
        save_config()
        print("[AYAR] Varsayılanlara sıfırlandı. Uygulamayı yeniden başlatın.")
        
        # Toast bildirimi göster
        toast = Adw.Toast(title="Ayarlar sıfırlandı. Uygulamayı yeniden başlatın.")
        toast.set_timeout(3)
        
        # Parent window'dan toast overlay'i bul ve toast'ı göster
        if hasattr(self.parent_window, 'toast_overlay'):
            self.parent_window.toast_overlay.add_toast(toast)
