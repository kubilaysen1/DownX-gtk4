"""
Settings Tab - SMART DYNAMIC BAZZITE STYLE ✨
🎯 Mode-based dynamic settings
🎨 Refined grouping and polish
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, Gio, GLib, Gdk
from pathlib import Path

from settings import GLOBAL_CONFIG, save_config, update_download_dir


class SettingsTab(Adw.PreferencesPage):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window

        self._add_custom_css()
        self._setup_ui()

    def _add_custom_css(self):
        """Add refined styling"""
        css = """
        /* Smooth group transitions */
        .preferences-group {
            transition: all 300ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        /* Mode selector refinement */
        .mode-selector {
            background: alpha(@accent_color, 0.08);
            border-radius: 12px;
            padding: 4px;
        }

        /* Settings icon refinement */
        .settings-icon {
            background: alpha(@accent_color, 0.1);
            border-radius: 8px;
            padding: 6px;
        }

        /* Group header polish */
        .preferences-group > box > label {
            font-weight: 600;
            letter-spacing: 0.5px;
        }

        /* Action button hover */
        .action-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px alpha(@accent_color, 0.2);
        }
        """

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(css.encode())
        Gtk.StyleContext.add_provider_for_display(
            Gdk.Display.get_default(),
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )

    def _setup_ui(self):
        """Setup smart dynamic UI"""

        # --- 1. DOWNLOAD MODE (Primary Setting) ---
        group_mode = Adw.PreferencesGroup(
            title="İndirme Tipi",
            description="Ses veya video olarak indirin"
        )
        self.add(group_mode)

        # Mode selector (2 options only)
        self.mode_model = Gtk.StringList()
        self.mode_model.append("🎵 Sadece Ses (Audio)")
        self.mode_model.append("🎬 Sadece Video")

        self.row_mode = Adw.ComboRow(title="İndirme Modu", model=self.mode_model)
        self.row_mode.set_icon_name("media-playback-start-symbolic")
        self.row_mode.add_css_class("mode-selector")

        # Load current mode
        current_mode = GLOBAL_CONFIG.get("download_mode", "audio")
        if current_mode in ["video+audio", "video"]:
            self.row_mode.set_selected(1)  # Video
        else:
            self.row_mode.set_selected(0)  # Audio

        self.row_mode.connect("notify::selected", self._on_mode_changed)
        group_mode.add(self.row_mode)

        # Download folder
        self.row_folder = Adw.ActionRow(title="İndirme Klasörü")
        self.row_folder.set_subtitle(str(GLOBAL_CONFIG.get("download_path", "~/Music")))
        self.row_folder.set_icon_name("folder-download-symbolic")

        btn_folder = Gtk.Button(icon_name="folder-open-symbolic")
        btn_folder.set_valign(Gtk.Align.CENTER)
        btn_folder.add_css_class("flat")
        btn_folder.add_css_class("circular")
        btn_folder.connect("clicked", self._on_folder_clicked)

        self.row_folder.add_suffix(btn_folder)
        group_mode.add(self.row_folder)

        # --- 2. AUDIO SETTINGS (Dynamic) ---
        self.group_audio = Adw.PreferencesGroup(
            title="🎵 Ses Ayarları",
            description="Müzik kalitesi ve format seçenekleri"
        )
        self.add(self.group_audio)

        # Audio quality
        quality_model = Gtk.StringList()
        for q in ["320 kbps (En İyi)", "256 kbps (Yüksek)", "192 kbps (Standart)", "128 kbps (Düşük)"]:
            quality_model.append(q)

        self.row_quality = Adw.ComboRow(title="Ses Kalitesi", model=quality_model)
        self.row_quality.set_icon_name("audio-volume-high-symbolic")

        saved_q = GLOBAL_CONFIG.get("audio_quality", "192")
        for i, q in enumerate(["320", "256", "192", "128"]):
            if q in str(saved_q):
                self.row_quality.set_selected(i)
                break

        self.row_quality.connect("notify::selected", self._on_quality_changed)
        self.group_audio.add(self.row_quality)

        # Audio format
        format_model = Gtk.StringList()
        format_model.append("MP3 (Evrensel)")
        format_model.append("M4A/AAC (Apple)")
        format_model.append("FLAC (Kayıpsız)")
        format_model.append("WAV (Ham)")
        format_model.append("OGG Vorbis")

        self.row_audio_format = Adw.ComboRow(title="Ses Formatı", model=format_model)
        self.row_audio_format.set_subtitle("Müzik dosyalarının formatı")
        self.row_audio_format.set_icon_name("document-properties-symbolic")

        formats = ["mp3", "m4a", "flac", "wav", "ogg"]
        current_format = GLOBAL_CONFIG.get("audio_format", "mp3")
        if current_format in formats:
            self.row_audio_format.set_selected(formats.index(current_format))

        self.row_audio_format.connect("notify::selected", self._on_audio_format_changed)
        self.group_audio.add(self.row_audio_format)

        # --- 3. VIDEO SETTINGS (Dynamic) ---
        self.group_video = Adw.PreferencesGroup(
            title="🎬 Video Ayarları",
            description="Video kalitesi ve format seçenekleri"
        )
        self.add(self.group_video)

        # Video quality
        video_quality_model = Gtk.StringList()
        video_quality_model.append("2160p (4K Ultra HD)")
        video_quality_model.append("1440p (2K QHD)")
        video_quality_model.append("1080p (Full HD)")
        video_quality_model.append("720p (HD)")
        video_quality_model.append("480p (SD)")

        self.row_video_quality = Adw.ComboRow(title="Video Kalitesi", model=video_quality_model)
        self.row_video_quality.set_icon_name("view-fullscreen-symbolic")

        video_qualities = ["2160", "1440", "1080", "720", "480"]
        current_video_quality = str(GLOBAL_CONFIG.get("video_quality", "1080")).replace("p", "")
        if current_video_quality in video_qualities:
            self.row_video_quality.set_selected(video_qualities.index(current_video_quality))

        self.row_video_quality.connect("notify::selected", self._on_video_quality_changed)
        self.group_video.add(self.row_video_quality)

        # Video format
        video_format_model = Gtk.StringList()
        video_format_model.append("MP4 (Standart)")
        video_format_model.append("MKV (Yüksek Kalite)")
        video_format_model.append("WEBM (Hafif)")

        self.row_video_format = Adw.ComboRow(title="Video Formatı", model=video_format_model)
        self.row_video_format.set_subtitle("Video dosyalarının formatı")
        self.row_video_format.set_icon_name("video-x-generic-symbolic")

        video_formats = ["mp4", "mkv", "webm"]
        current_video_format = GLOBAL_CONFIG.get("video_format", "mp4")
        if current_video_format in video_formats:
            self.row_video_format.set_selected(video_formats.index(current_video_format))

        self.row_video_format.connect("notify::selected", self._on_video_format_changed)
        self.group_video.add(self.row_video_format)

        # --- 4. METADATA & FEATURES ---
        group_features = Adw.PreferencesGroup(
            title="Özellikler",
            description="Dosya işleme seçenekleri"
        )
        self.add(group_features)

        # Metadata
        self.row_meta = Adw.SwitchRow(title="Metadata Ekle")
        self.row_meta.set_subtitle("Şarkı/video bilgilerini dosyaya işle")
        self.row_meta.set_icon_name("document-edit-symbolic")
        self.row_meta.set_active(GLOBAL_CONFIG.get("embed_metadata", True))
        self.row_meta.connect("notify::active", self._on_switch_changed, "embed_metadata")
        group_features.add(self.row_meta)

        # Thumbnail
        self.row_thumb = Adw.SwitchRow(title="Kapak Resmi Ekle")
        self.row_thumb.set_subtitle("Thumbnail'i dosyaya gömülü kapak olarak ekle")
        self.row_thumb.set_icon_name("image-x-generic-symbolic")
        self.row_thumb.set_active(GLOBAL_CONFIG.get("embed_thumbnail", True))
        self.row_thumb.connect("notify::active", self._on_switch_changed, "embed_thumbnail")
        group_features.add(self.row_thumb)

        # Skip existing
        self.row_skip = Adw.SwitchRow(title="Mevcut Dosyaları Atla")
        self.row_skip.set_subtitle("Daha önce indirilmiş dosyalar tekrar indirilmesin")
        self.row_skip.set_icon_name("media-skip-forward-symbolic")
        self.row_skip.set_active(GLOBAL_CONFIG.get("skip_existing", True))
        self.row_skip.connect("notify::active", self._on_switch_changed, "skip_existing")
        group_features.add(self.row_skip)

        # --- 5. SPOTIFY API ---
        group_api = Adw.PreferencesGroup(
            title="Spotify API",
            description="Spotify playlistleri için gerekli"
        )
        self.add(group_api)

        # Client ID
        self.entry_client_id = Adw.EntryRow(title="Client ID")
        self.entry_client_id.set_text(GLOBAL_CONFIG.get("spotify_client_id", ""))
        self.entry_client_id.connect("apply", self._on_api_changed, "spotify_client_id")
        group_api.add(self.entry_client_id)

        # Client Secret
        self.entry_secret = Adw.PasswordEntryRow(title="Client Secret")
        self.entry_secret.set_text(GLOBAL_CONFIG.get("spotify_client_secret", ""))
        self.entry_secret.connect("apply", self._on_api_changed, "spotify_client_secret")
        group_api.add(self.entry_secret)

        # Info row with link button
        info_row = Adw.ActionRow(
            title="API Anahtarlarını Nereden Alırım?",
            subtitle="developer.spotify.com/dashboard - Ücretsiz hesap gerekli"
        )
        info_row.set_icon_name("dialog-information-symbolic")

        btn_open = Gtk.Button()
        btn_open.set_icon_name("web-browser-symbolic")
        btn_open.set_valign(Gtk.Align.CENTER)
        btn_open.add_css_class("flat")
        btn_open.add_css_class("circular")
        btn_open.set_tooltip_text("Spotify Developer Dashboard'u Aç")
        btn_open.connect("clicked", lambda b: self._open_url("https://developer.spotify.com/dashboard"))
        info_row.add_suffix(btn_open)

        group_api.add(info_row)

        # --- 6. ADVANCED ---
        group_advanced = Adw.PreferencesGroup(
            title="Gelişmiş Ayarlar"
        )
        self.add(group_advanced)

        # Concurrent downloads
        self.row_concurrent = Adw.SpinRow.new_with_range(1, 10, 1)
        self.row_concurrent.set_title("Eş Zamanlı İndirme")
        self.row_concurrent.set_subtitle("Aynı anda kaç dosya indirilsin (1-10)")
        self.row_concurrent.set_icon_name("system-run-symbolic")
        self.row_concurrent.set_value(GLOBAL_CONFIG.get("concurrent_downloads", 3))
        self.row_concurrent.connect("notify::value", self._on_concurrent_changed)
        group_advanced.add(self.row_concurrent)

        # --- 7. ACTIONS ---
        group_actions = Adw.PreferencesGroup()
        self.add(group_actions)

        # Reset button
        btn_reset = Gtk.Button(label="🔄 Varsayılanlara Sıfırla")
        btn_reset.add_css_class("destructive-action")
        btn_reset.add_css_class("pill")
        btn_reset.add_css_class("action-button")
        btn_reset.set_halign(Gtk.Align.CENTER)
        btn_reset.set_margin_top(16)
        btn_reset.set_margin_bottom(8)
        btn_reset.connect("clicked", self._on_reset_clicked)
        group_actions.add(btn_reset)

        # Initial visibility update (defer to idle to ensure widgets are ready)
        GLib.idle_add(self._update_visibility)

    # --- DYNAMIC VISIBILITY ---

    def _update_visibility(self):
        """Show/hide groups based on mode"""
        selected = self.row_mode.get_selected()

        print(f"[SETTINGS] Mode değişti: {selected} ({'Audio' if selected == 0 else 'Video'})")

        # Smooth fade transition
        if selected == 0:  # Audio mode
            print("[SETTINGS] → Ses Ayarları gösteriliyor, Video Ayarları gizleniyor")
            self.group_audio.set_visible(True)
            self.group_video.set_visible(False)
        else:  # Video mode
            print("[SETTINGS] → Video Ayarları gösteriliyor, Ses Ayarları gizleniyor")
            self.group_audio.set_visible(False)
            self.group_video.set_visible(True)

        # Return False to stop idle callback
        return False

    # --- EVENT HANDLERS ---

    def _on_mode_changed(self, row, param):
        """Mode changed - update visibility and config"""
        selected = row.get_selected()

        if selected == 0:  # Audio
            save_config({"download_mode": "audio"})
            self._show_toast("🎵 Mod: Sadece Ses")
        else:  # Video
            save_config({"download_mode": "video"})
            self._show_toast("🎬 Mod: Sadece Video")

        # Update visibility with smooth transition
        self._update_visibility()

    def _on_quality_changed(self, row, param):
        qualities = ["320", "256", "192", "128"]
        selected_q = qualities[row.get_selected()]
        save_config({"audio_quality": selected_q})
        self._show_toast(f"🎵 Ses Kalitesi: {selected_q} kbps")

    def _on_audio_format_changed(self, row, param):
        formats = ["mp3", "m4a", "flac", "wav", "ogg"]
        selected_format = formats[row.get_selected()]
        save_config({"audio_format": selected_format})
        self._show_toast(f"📄 Ses Formatı: {selected_format.upper()}")

    def _on_video_format_changed(self, row, param):
        formats = ["mp4", "mkv", "webm"]
        selected_format = formats[row.get_selected()]
        save_config({"video_format": selected_format})
        self._show_toast(f"📄 Video Formatı: {selected_format.upper()}")

    def _on_video_quality_changed(self, row, param):
        qualities = ["2160", "1440", "1080", "720", "480"]
        selected_quality = qualities[row.get_selected()]
        save_config({"video_quality": selected_quality})
        self._show_toast(f"🎬 Video Kalitesi: {selected_quality}p")

    def _on_switch_changed(self, row, param, config_key):
        value = row.get_active()
        save_config({config_key: value})

        # User-friendly messages
        messages = {
            "embed_metadata": "✓ Metadata" if value else "✗ Metadata",
            "embed_thumbnail": "✓ Kapak Resmi" if value else "✗ Kapak Resmi",
            "skip_existing": "✓ Mevcut Dosyalar Atlanıyor" if value else "✗ Tekrar İndirilecek"
        }

        if config_key in messages:
            self._show_toast(messages[config_key])

    def _on_api_changed(self, entry, config_key):
        text = entry.get_text()
        save_config({config_key: text})

        if text:
            self._show_toast("✓ API anahtarı kaydedildi")

    def _on_concurrent_changed(self, row, param):
        value = int(row.get_value())
        save_config({"concurrent_downloads": value})
        self._show_toast(f"⚡ Eş Zamanlı İndirme: {value}")

    def _on_folder_clicked(self, btn):
        """Open folder picker"""
        dialog = Gtk.FileDialog()
        dialog.set_title("İndirme Klasörünü Seç")
        dialog.select_folder(self.parent_window, None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        """Handle folder selection"""
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                path = folder.get_path()
                self.row_folder.set_subtitle(path)
                update_download_dir(path)
                self._show_toast("📁 Klasör güncellendi")
        except Exception as e:
            print(f"Folder selection error: {e}")

    def _on_reset_clicked(self, btn):
        """Reset to defaults"""
        dialog = Adw.MessageDialog.new(
            self.parent_window,
            "Ayarları Sıfırla?",
            "Tüm ayarlar varsayılan değerlere dönecek. Bu işlem geri alınamaz."
        )
        dialog.add_response("cancel", "İptal")
        dialog.add_response("reset", "Sıfırla")
        dialog.set_response_appearance("reset", Adw.ResponseAppearance.DESTRUCTIVE)
        dialog.connect("response", self._on_reset_confirmed)
        dialog.present()

    def _on_reset_confirmed(self, dialog, response):
        """Handle reset confirmation"""
        if response == "reset":
            from settings import DEFAULT_CONFIG
            save_config(DEFAULT_CONFIG)
            self._show_toast("⚠️ Ayarlar sıfırlandı. Uygulamayı yeniden başlatın.")

    def _open_url(self, url):
        """Open URL in browser"""
        try:
            import subprocess
            subprocess.Popen(['xdg-open', url])
        except Exception as e:
            print(f"Error opening URL: {e}")

    def _show_toast(self, message):
        """Show toast notification"""
        if hasattr(self.parent_window, 'show_toast'):
            self.parent_window.show_toast(message)
        else:
            print(f"[TOAST] {message}")
