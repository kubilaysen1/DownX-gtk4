"""
Tools Tab - GTK4 Bazzite Style
🔧 Extra tools and utilities
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GLib, Gio

import os
import subprocess
import threading
from pathlib import Path

from settings import CACHE_DIR, get_download_dir


class ToolsTab(Adw.PreferencesPage):
    def __init__(self, parent_window):
        super().__init__()
        self.parent_window = parent_window
        self.set_title("Araçlar")
        self.set_icon_name("applications-utilities-symbolic")

        # --- 1. FORMAT CONVERSION ---
        group_convert = Adw.PreferencesGroup(
            title="Format Dönüştürme",
            description="Ses ve video dosyalarını farklı formatlara çevir"
        )
        self.add(group_convert)

        # File selection
        self.row_convert_file = Adw.ActionRow(title="Dosya Seçilmedi")
        self.row_convert_file.set_subtitle("Dönüştürülecek dosyayı seçin")
        self.row_convert_file.set_icon_name("document-open-symbolic")

        btn_select = Gtk.Button(label="Seç")
        btn_select.set_valign(Gtk.Align.CENTER)
        btn_select.add_css_class("pill")
        btn_select.connect("clicked", self._on_select_file)
        self.row_convert_file.add_suffix(btn_select)
        group_convert.add(self.row_convert_file)

        # Target format
        format_model = Gtk.StringList()
        for fmt in ["MP3", "M4A", "FLAC", "WAV", "OGG", "MP4", "WEBM", "MKV"]:
            format_model.append(fmt)

        self.row_target_format = Adw.ComboRow(title="Hedef Format")
        self.row_target_format.set_model(format_model)
        self.row_target_format.set_selected(0)
        group_convert.add(self.row_target_format)

        # Convert button
        btn_convert = Gtk.Button(label="Dönüştür")
        btn_convert.add_css_class("suggested-action")
        btn_convert.add_css_class("pill")
        btn_convert.set_halign(Gtk.Align.CENTER)
        btn_convert.set_margin_top(12)
        btn_convert.connect("clicked", self._on_convert)
        group_convert.add(btn_convert)

        # --- 2. METADATA EDITING ---
        group_metadata = Adw.PreferencesGroup(
            title="Toplu Metadata Düzenleme",
            description="Birden fazla dosyanın etiketlerini düzenle"
        )
        self.add(group_metadata)

        # Folder selection
        self.row_metadata_folder = Adw.ActionRow(title="Klasör Seçilmedi")
        self.row_metadata_folder.set_subtitle("Düzenlenecek dosyaların klasörü")
        self.row_metadata_folder.set_icon_name("folder-music-symbolic")

        btn_select_folder = Gtk.Button(label="Seç")
        btn_select_folder.set_valign(Gtk.Align.CENTER)
        btn_select_folder.add_css_class("pill")
        btn_select_folder.connect("clicked", self._on_select_folder)
        self.row_metadata_folder.add_suffix(btn_select_folder)
        group_metadata.add(self.row_metadata_folder)

        # Artist
        self.entry_artist = Adw.EntryRow(title="Sanatçı (Tümüne Uygulanır)")
        group_metadata.add(self.entry_artist)

        # Album
        self.entry_album = Adw.EntryRow(title="Albüm (Tümüne Uygulanır)")
        group_metadata.add(self.entry_album)

        # Year
        self.entry_year = Adw.EntryRow(title="Yıl (Tümüne Uygulanır)")
        group_metadata.add(self.entry_year)

        # Apply button
        btn_apply_metadata = Gtk.Button(label="Metadata'yı Uygula")
        btn_apply_metadata.add_css_class("suggested-action")
        btn_apply_metadata.add_css_class("pill")
        btn_apply_metadata.set_halign(Gtk.Align.CENTER)
        btn_apply_metadata.set_margin_top(12)
        btn_apply_metadata.connect("clicked", self._on_apply_metadata)
        group_metadata.add(btn_apply_metadata)

        # --- 3. CACHE MANAGEMENT ---
        group_cache = Adw.PreferencesGroup(
            title="Önbellek Yönetimi",
            description="Uygulamanın kullandığı geçici dosyaları temizle"
        )
        self.add(group_cache)

        # Cache size
        self.row_cache_size = Adw.ActionRow(title="Önbellek Boyutu")
        self.row_cache_size.set_subtitle("Hesaplanıyor...")
        self.row_cache_size.set_icon_name("drive-harddisk-symbolic")
        group_cache.add(self.row_cache_size)

        # Calculate cache size
        threading.Thread(target=self._calculate_cache_size, daemon=True).start()

        # Clear button
        btn_clear_cache = Gtk.Button(label="Önbelleği Temizle")
        btn_clear_cache.add_css_class("destructive-action")
        btn_clear_cache.add_css_class("pill")
        btn_clear_cache.set_halign(Gtk.Align.CENTER)
        btn_clear_cache.set_margin_top(12)
        btn_clear_cache.connect("clicked", self._on_clear_cache)
        group_cache.add(btn_clear_cache)

        # --- 4. CLEANUP TOOLS ---
        group_cleanup = Adw.PreferencesGroup(
            title="İndirme Dizini Temizleme",
            description="Yinelenen veya bozuk dosyaları temizle"
        )
        self.add(group_cleanup)

        # Find duplicates
        btn_find_duplicates = Gtk.Button(label="Yinelenen Dosyaları Bul")
        btn_find_duplicates.add_css_class("pill")
        btn_find_duplicates.set_halign(Gtk.Align.CENTER)
        btn_find_duplicates.connect("clicked", self._on_find_duplicates)
        group_cleanup.add(btn_find_duplicates)

        # Find corrupt
        btn_find_corrupt = Gtk.Button(label="Bozuk Dosyaları Bul")
        btn_find_corrupt.add_css_class("pill")
        btn_find_corrupt.set_halign(Gtk.Align.CENTER)
        btn_find_corrupt.set_margin_top(8)
        btn_find_corrupt.connect("clicked", self._on_find_corrupt)
        group_cleanup.add(btn_find_corrupt)

    # --- HELPERS ---

    def _calculate_cache_size(self):
        """Calculate cache size"""
        try:
            total_size = 0
            cache_path = Path(CACHE_DIR)

            if cache_path.exists():
                for file in cache_path.rglob("*"):
                    if file.is_file():
                        total_size += file.stat().st_size

            size_mb = total_size / (1024 * 1024)
            GLib.idle_add(self.row_cache_size.set_subtitle, f"{size_mb:.2f} MB")
        except Exception as e:
            GLib.idle_add(self.row_cache_size.set_subtitle, f"Hesaplanamadı: {e}")

    def _show_toast(self, message):
        """Show toast"""
        if hasattr(self.parent_window, 'show_toast'):
            self.parent_window.show_toast(message)
        else:
            print(f"[TOAST] {message}")

    # --- FORMAT CONVERSION ---

    def _on_select_file(self, btn):
        """Select file for conversion"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Dosya Seç")

        # Filters
        filter_list = Gio.ListStore.new(Gtk.FileFilter)

        f_audio = Gtk.FileFilter()
        f_audio.set_name("Ses Dosyaları")
        f_audio.add_mime_type("audio/*")
        filter_list.append(f_audio)

        f_video = Gtk.FileFilter()
        f_video.set_name("Video Dosyaları")
        f_video.add_mime_type("video/*")
        filter_list.append(f_video)

        dialog.set_filters(filter_list)
        dialog.open(self.parent_window, None, self._on_file_selected)

    def _on_file_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                self.selected_file = file.get_path()
                self.row_convert_file.set_title(Path(self.selected_file).name)
                self.row_convert_file.set_subtitle(self.selected_file)
        except Exception as e:
            print(f"File selection error: {e}")

    def _on_convert(self, btn):
        """Start conversion"""
        if not hasattr(self, 'selected_file'):
            self._show_toast("Önce bir dosya seçin!")
            return

        formats = ["mp3", "m4a", "flac", "wav", "ogg", "mp4", "webm", "mkv"]
        target_format = formats[self.row_target_format.get_selected()].lower()

        input_path = Path(self.selected_file)
        output_path = input_path.parent / f"{input_path.stem}_converted.{target_format}"

        threading.Thread(
            target=self._convert_file,
            args=(str(input_path), str(output_path), target_format),
            daemon=True
        ).start()

        self._show_toast("Dönüştürme başlatıldı...")

    def _convert_file(self, input_file, output_file, target_format):
        """Convert file using FFmpeg"""
        try:
            cmd = ["ffmpeg", "-i", input_file, "-y", output_file]
            subprocess.run(cmd, check=True, capture_output=True)

            GLib.idle_add(self._show_toast,
                         f"✅ Dönüştürme tamamlandı: {Path(output_file).name}")
        except subprocess.CalledProcessError as e:
            GLib.idle_add(self._show_toast, f"❌ Dönüştürme hatası: {e}")
        except Exception as e:
            GLib.idle_add(self._show_toast, f"❌ Hata: {e}")

    # --- METADATA EDITING ---

    def _on_select_folder(self, btn):
        """Select folder for metadata editing"""
        dialog = Gtk.FileDialog()
        dialog.set_title("Klasör Seç")
        dialog.select_folder(self.parent_window, None, self._on_folder_selected)

    def _on_folder_selected(self, dialog, result):
        try:
            folder = dialog.select_folder_finish(result)
            if folder:
                self.selected_folder = folder.get_path()
                self.row_metadata_folder.set_title(Path(self.selected_folder).name)
                self.row_metadata_folder.set_subtitle(self.selected_folder)
        except Exception as e:
            print(f"Folder selection error: {e}")

    def _on_apply_metadata(self, btn):
        """Apply metadata to all files"""
        if not hasattr(self, 'selected_folder'):
            self._show_toast("Önce bir klasör seçin!")
            return

        artist = self.entry_artist.get_text()
        album = self.entry_album.get_text()
        year = self.entry_year.get_text()

        if not artist and not album and not year:
            self._show_toast("En az bir alan doldurun!")
            return

        threading.Thread(
            target=self._apply_metadata_bulk,
            args=(self.selected_folder, artist, album, year),
            daemon=True
        ).start()

        self._show_toast("Metadata güncelleniyor...")

    def _apply_metadata_bulk(self, folder, artist, album, year):
        """Apply metadata to all files in folder"""
        try:
            from tagger import set_id3_tags

            folder_path = Path(folder)
            audio_files = []

            for ext in ['.mp3', '.m4a', '.flac', '.ogg']:
                audio_files.extend(folder_path.glob(f"*{ext}"))

            count = 0
            for file in audio_files:
                info = {}
                if artist: info['artist'] = artist
                if album: info['album'] = album
                if year: info['year'] = year
                info['title'] = file.stem

                if set_id3_tags(str(file), info):
                    count += 1

            GLib.idle_add(self._show_toast, f"✅ {count} dosya güncellendi!")
        except Exception as e:
            GLib.idle_add(self._show_toast, f"❌ Hata: {e}")

    # --- CACHE MANAGEMENT ---

    def _on_clear_cache(self, btn):
        """Clear cache"""
        try:
            cache_path = Path(CACHE_DIR)

            if cache_path.exists():
                for file in cache_path.rglob("*"):
                    if file.is_file():
                        file.unlink()

                self._show_toast("✅ Önbellek temizlendi!")
                self.row_cache_size.set_subtitle("0.00 MB")
            else:
                self._show_toast("⚠️ Önbellek klasörü bulunamadı")
        except Exception as e:
            self._show_toast(f"❌ Hata: {e}")

    # --- CLEANUP TOOLS ---

    def _on_find_duplicates(self, btn):
        """Find duplicate files"""
        self._show_toast("🔍 Yinelenen dosyalar aranıyor...")
        threading.Thread(target=self._find_duplicates, daemon=True).start()

    def _find_duplicates(self):
        """Find duplicate files by hash"""
        try:
            import hashlib

            download_dir = Path(get_download_dir())
            hashes = {}
            duplicates = []

            for ext in ['.mp3', '.m4a', '.flac', '.mp4', '.mkv', '.webm']:
                for file in download_dir.rglob(f"*{ext}"):
                    with open(file, 'rb') as f:
                        file_hash = hashlib.md5(f.read()).hexdigest()

                    if file_hash in hashes:
                        duplicates.append((hashes[file_hash], file))
                    else:
                        hashes[file_hash] = file

            if duplicates:
                msg = f"⚠️ {len(duplicates)} yinelenen dosya bulundu!"
            else:
                msg = "✅ Yinelenen dosya bulunamadı"

            GLib.idle_add(self._show_toast, msg)
        except Exception as e:
            GLib.idle_add(self._show_toast, f"❌ Hata: {e}")

    def _on_find_corrupt(self, btn):
        """Find corrupt files"""
        self._show_toast("🔍 Bozuk dosyalar aranıyor...")
        threading.Thread(target=self._find_corrupt, daemon=True).start()

    def _find_corrupt(self):
        """Find corrupt/small files"""
        try:
            download_dir = Path(get_download_dir())
            corrupt = []

            MIN_SIZE = 50_000  # 50KB

            for ext in ['.mp3', '.m4a', '.flac', '.mp4', '.mkv']:
                for file in download_dir.rglob(f"*{ext}"):
                    if file.stat().st_size < MIN_SIZE:
                        corrupt.append(file)

            if corrupt:
                msg = f"⚠️ {len(corrupt)} şüpheli dosya bulundu! (< 50KB)"
            else:
                msg = "✅ Bozuk dosya bulunamadı"

            GLib.idle_add(self._show_toast, msg)
        except Exception as e:
            GLib.idle_add(self._show_toast, f"❌ Hata: {e}")
