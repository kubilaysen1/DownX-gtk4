"""
Downloads Tab - BAZZITE ULTRA POLISH ✨
⚡ High performance with 500ms batch updates
🎨 Stunning animations and transitions
💎 Refined spacing and hover effects
"""

import gi
gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GObject, Pango, GLib, Gio, Gdk

import time
from collections import deque


# --- DATA MODEL ---
class DownloadObject(GObject.Object):
    """Download item with properties for binding"""
    __gtype_name__ = 'DownloadObject'

    def __init__(self, uid, title, artist, status, progress=0):
        super().__init__()
        self.uid = uid
        self._title = title
        self._artist = artist
        self._status = status
        self._progress = progress
        self._last_update = time.time()

    @GObject.Property(type=str)
    def title(self):
        return self._title

    @title.setter
    def title(self, value):
        self._title = value

    @GObject.Property(type=str)
    def artist(self):
        return self._artist

    @artist.setter
    def artist(self, value):
        self._artist = value

    @GObject.Property(type=str)
    def status(self):
        return self._status

    @status.setter
    def status(self, value):
        self._status = value
        self._last_update = time.time()

    @GObject.Property(type=float)
    def progress(self):
        return self._progress

    @progress.setter
    def progress(self, value):
        self._progress = max(0.0, min(1.0, value))


class DownloadsTab(Adw.Bin):
    """Ultra-polished downloads manager with smooth animations"""

    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.queue_manager = getattr(main_window, 'queue_manager', None)

        # Performance optimization (unchanged)
        self._pending_updates = deque(maxlen=100)
        self._last_full_refresh = 0
        self._update_interval = 500  # ms

        # Statistics
        self.stats = {"queue": 0, "active": 0, "completed": 0, "failed": 0}

        self._setup_ui()
        self._add_custom_css()

        # Start update timer
        GLib.timeout_add(self._update_interval, self._batch_update_timer)

    def _add_custom_css(self):
        """Add refined Bazzite styling"""
        css = """
        /* Download item cards with hover effect */
        .download-card {
            background: alpha(@view_bg_color, 0.5);
            border-radius: 12px;
            border: 1px solid alpha(@borders, 0.1);
            padding: 14px;
            margin: 3px 8px;
            transition: all 200ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        .download-card:hover {
            background: alpha(@view_bg_color, 0.8);
            border-color: alpha(@accent_color, 0.3);
            box-shadow: 0 2px 8px alpha(@accent_color, 0.15);
            transform: translateY(-1px);
        }

        /* Animated gradient progress bar */
        .download-progress {
            min-height: 4px;
            border-radius: 2px;
            background: linear-gradient(
                90deg,
                alpha(@accent_color, 0.2),
                alpha(@accent_color, 0.1)
            );
        }

        .download-progress progress {
            background: linear-gradient(
                90deg,
                #7c3aed,
                #a855f7,
                #7c3aed
            );
            background-size: 200% 100%;
            animation: shimmer 2s linear infinite;
            border-radius: 2px;
            box-shadow: 0 0 8px alpha(#a855f7, 0.4);
        }

        @keyframes shimmer {
            0% { background-position: 200% 0; }
            100% { background-position: -200% 0; }
        }

        /* Status badges */
        .status-badge {
            padding: 4px 12px;
            border-radius: 12px;
            font-size: 0.75rem;
            font-weight: 600;
            letter-spacing: 0.3px;
            transition: all 150ms ease;
        }

        .status-pending {
            background: alpha(#a855f7, 0.15);
            color: #a855f7;
        }

        .status-downloading {
            background: alpha(#3b82f6, 0.15);
            color: #3b82f6;
            animation: pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite;
        }

        .status-completed {
            background: alpha(#10b981, 0.15);
            color: #10b981;
        }

        .status-error {
            background: alpha(#ef4444, 0.15);
            color: #ef4444;
        }

        @keyframes pulse {
            0%, 100% { opacity: 1; }
            50% { opacity: 0.7; }
        }

        /* Item icon with subtle shadow */
        .download-icon {
            background: alpha(@accent_color, 0.1);
            border-radius: 10px;
            padding: 8px;
            box-shadow: 0 1px 3px alpha(black, 0.1);
        }

        /* Smooth hover for action buttons */
        .download-action {
            opacity: 0;
            transition: opacity 150ms ease;
        }

        .download-card:hover .download-action {
            opacity: 1;
        }

        /* Stats label styling */
        .stats-chip {
            background: alpha(@accent_color, 0.1);
            border-radius: 8px;
            padding: 2px 8px;
            margin: 0 2px;
        }

        /* Pill button refinement */
        .pill-button {
            border-radius: 18px;
            padding: 8px 16px;
            font-weight: 600;
            transition: all 150ms cubic-bezier(0.25, 0.46, 0.45, 0.94);
        }

        .pill-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 12px alpha(@accent_color, 0.25);
        }

        /* List background */
        .downloads-list {
            background: transparent;
        }

        /* Empty state refinement */
        .empty-state-icon {
            opacity: 0.4;
            color: @accent_color;
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
        """Setup ultra-polished UI"""
        # Main container
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        # --- ELEGANT TOOLBAR ---
        toolbar = Adw.HeaderBar()
        toolbar.set_show_title(False)

        # Title with refined stats
        title_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        title_box.set_valign(Gtk.Align.CENTER)

        self.title_label = Gtk.Label(label="İndirme Kuyruğu")
        self.title_label.add_css_class("title-3")
        title_box.append(self.title_label)

        self.stats_label = Gtk.Label()
        self.stats_label.add_css_class("caption")
        self.stats_label.add_css_class("dim-label")
        self._update_stats_label()
        title_box.append(self.stats_label)

        toolbar.set_title_widget(title_box)

        # Refined control buttons
        controls = Gtk.Box(spacing=8)

        self.btn_start = Gtk.Button()
        self.btn_start.set_icon_name("media-playback-start-symbolic")
        self.btn_start.set_tooltip_text("İndirmeleri Başlat")
        self.btn_start.add_css_class("suggested-action")
        self.btn_start.add_css_class("pill-button")
        self.btn_start.connect("clicked", self._on_start_clicked)
        controls.append(self.btn_start)

        self.btn_stop = Gtk.Button()
        self.btn_stop.set_icon_name("media-playback-stop-symbolic")
        self.btn_stop.set_tooltip_text("Durdur")
        self.btn_stop.add_css_class("pill-button")
        self.btn_stop.set_sensitive(False)
        self.btn_stop.connect("clicked", self._on_stop_clicked)
        controls.append(self.btn_stop)

        btn_clear = Gtk.Button()
        btn_clear.set_icon_name("user-trash-symbolic")
        btn_clear.set_tooltip_text("Tamamlananları Temizle")
        btn_clear.add_css_class("pill-button")
        btn_clear.connect("clicked", self._on_clear_clicked)
        controls.append(btn_clear)

        btn_folder = Gtk.Button()
        btn_folder.set_icon_name("folder-open-symbolic")
        btn_folder.set_tooltip_text("Klasörü Aç")
        btn_folder.add_css_class("pill-button")
        btn_folder.connect("clicked", self._on_folder_clicked)
        controls.append(btn_folder)

        toolbar.pack_end(controls)
        main_box.append(toolbar)

        # --- SMOOTH STACK TRANSITIONS ---
        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.SLIDE_UP_DOWN)
        self.stack.set_transition_duration(250)
        main_box.append(self.stack)

        # Refined empty state
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("folder-download-symbolic")
        self.status_page.add_css_class("empty-state-icon")
        self.status_page.set_title("Henüz İndirme Yok")
        self.status_page.set_description(
            "Arama sekmesinden video veya müzik ekleyin\n"
            "Linkler otomatik olarak kuyruğa eklenecek"
        )

        # Add a subtle hint button
        hint_btn = Gtk.Button(label="Nasıl Kullanılır?")
        hint_btn.add_css_class("pill")
        hint_btn.set_halign(Gtk.Align.CENTER)
        hint_btn.connect("clicked", self._show_help)
        self.status_page.set_child(hint_btn)

        self.stack.add_named(self.status_page, "empty")

        # Polished list view
        self.store = Gio.ListStore(item_type=DownloadObject)
        self.selection_model = Gtk.NoSelection(model=self.store)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        self.list_view = Gtk.ListView(
            model=self.selection_model,
            factory=factory
        )
        self.list_view.add_css_class("downloads-list")
        self.list_view.set_single_click_activate(False)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(self.list_view)
        scrolled.set_vexpand(True)
        scrolled.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        self.stack.add_named(scrolled, "list")

        # Show empty state initially
        self.stack.set_visible_child_name("empty")

    def _on_factory_setup(self, factory, list_item):
        """Setup refined card-style list item"""
        # Main card container
        card = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=14)
        card.add_css_class("download-card")

        # Icon with background
        icon_box = Gtk.Box()
        icon_box.add_css_class("download-icon")
        icon = Gtk.Image.new_from_icon_name("audio-x-generic-symbolic")
        icon.set_pixel_size(32)
        icon_box.append(icon)
        card.append(icon_box)

        # Content box with better spacing
        content = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        content.set_hexpand(True)
        content.set_valign(Gtk.Align.CENTER)

        # Title
        title = Gtk.Label(xalign=0)
        title.add_css_class("heading")
        title.set_ellipsize(Pango.EllipsizeMode.END)
        title.set_max_width_chars(45)
        content.append(title)

        # Artist with icon
        artist_box = Gtk.Box(spacing=6)
        artist_icon = Gtk.Image.new_from_icon_name("avatar-default-symbolic")
        artist_icon.set_pixel_size(14)
        artist_icon.add_css_class("dim-label")
        artist_box.append(artist_icon)

        artist = Gtk.Label(xalign=0)
        artist.add_css_class("caption")
        artist.add_css_class("dim-label")
        artist.set_ellipsize(Pango.EllipsizeMode.END)
        artist_box.append(artist)
        content.append(artist_box)

        card.append(content)

        # Status and progress box
        status_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        status_box.set_valign(Gtk.Align.CENTER)
        status_box.set_size_request(160, -1)

        # Status badge
        status_label = Gtk.Label(xalign=1)
        status_label.add_css_class("status-badge")
        status_box.append(status_label)

        # Progress bar with custom styling
        progress = Gtk.ProgressBar()
        progress.set_show_text(False)
        progress.add_css_class("download-progress")
        status_box.append(progress)

        card.append(status_box)

        # Action buttons (appear on hover)
        actions = Gtk.Box(spacing=4)
        actions.add_css_class("download-action")
        actions.set_valign(Gtk.Align.CENTER)

        btn_retry = Gtk.Button()
        btn_retry.set_icon_name("view-refresh-symbolic")
        btn_retry.set_tooltip_text("Tekrar Dene")
        btn_retry.add_css_class("flat")
        btn_retry.add_css_class("circular")
        actions.append(btn_retry)

        btn_remove = Gtk.Button()
        btn_remove.set_icon_name("user-trash-symbolic")
        btn_remove.set_tooltip_text("Kuyruktan Kaldır")
        btn_remove.add_css_class("flat")
        btn_remove.add_css_class("circular")
        actions.append(btn_remove)

        card.append(actions)

        list_item.set_child(card)

    def _on_factory_bind(self, factory, list_item):
        """Bind data with smooth updates"""
        card = list_item.get_child()
        item = list_item.get_item()

        # Navigate widget tree (GTK4 style)
        icon_box = card.get_first_child()
        content = icon_box.get_next_sibling()
        title = content.get_first_child()
        artist_box = title.get_next_sibling()
        artist = artist_box.get_last_child()

        status_box = content.get_next_sibling()
        status_label = status_box.get_first_child()
        progress = status_label.get_next_sibling()

        actions = status_box.get_next_sibling()

        # Bind properties with smooth transitions
        item.bind_property("title", title, "label",
                          GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("artist", artist, "label",
                          GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("status", status_label, "label",
                          GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("progress", progress, "fraction",
                          GObject.BindingFlags.SYNC_CREATE)

        # Dynamic status styling with transitions
        def update_status_style(obj, pspec):
            status = obj.get_property("status")

            # Remove all status classes
            for cls in ["status-pending", "status-downloading", "status-completed", "status-error"]:
                status_label.remove_css_class(cls)

            # Apply appropriate class
            if "Tamamlandı" in status or "Atlandı" in status:
                status_label.add_css_class("status-completed")
                progress.set_visible(False)
            elif "İndiriliyor" in status or "Dönüştürülüyor" in status or "%" in status:
                status_label.add_css_class("status-downloading")
                progress.set_visible(True)
            elif "Hata" in status:
                status_label.add_css_class("status-error")
                progress.set_visible(False)
            else:
                status_label.add_css_class("status-pending")
                progress.set_visible(False)

        item.connect("notify::status", update_status_style)
        update_status_style(item, None)

        # Action button handlers
        btn_retry = actions.get_first_child()
        btn_remove = btn_retry.get_next_sibling()

        def on_retry_clicked(btn):
            # TODO: Implement retry logic
            self.main_window.show_toast(f"🔄 Tekrar deneniyor: {item.title}")

        def on_remove_clicked(btn):
            if self.queue_manager:
                with self.queue_manager.lock:
                    self.queue_manager.queue = [
                        i for i in self.queue_manager.queue
                        if i.get("id") != item.uid
                    ]
                self.update_from_queue()
                self.main_window.show_toast("🗑️ Kuyruktan kaldırıldı")

        btn_retry.connect("clicked", on_retry_clicked)
        btn_remove.connect("clicked", on_remove_clicked)

    # --- UPDATE LOGIC (Performance unchanged) ---

    def _batch_update_timer(self):
        """Batch update timer (500ms intervals)"""
        now = time.time()

        # Full refresh every 1 second
        if now - self._last_full_refresh > 1.0:
            self.update_from_queue()
            self._last_full_refresh = now

        # Process pending updates
        while self._pending_updates:
            update = self._pending_updates.popleft()
            # Process individual update if needed

        return True  # Keep timer running

    def update_from_queue(self):
        """Update UI from queue manager (optimized)"""
        if not self.queue_manager:
            if hasattr(self.main_window, 'queue_manager'):
                self.queue_manager = self.main_window.queue_manager
            else:
                return

        queue = self.queue_manager.queue if self.queue_manager else []

        # Update stats
        self._calculate_stats(queue)
        self._update_stats_label()

        # Sync store with queue
        current_count = self.store.get_n_items()
        queue_count = len(queue)

        if current_count != queue_count:
            # Full rebuild
            self.store.remove_all()
            for item in queue:
                self.store.append(DownloadObject(
                    item.get("id"),
                    item.get("title", "Unknown"),
                    item.get("artist", ""),
                    item.get("status", "Pending"),
                    0.0
                ))
        else:
            # Update existing items
            for i, item in enumerate(queue):
                obj = self.store.get_item(i)
                if obj:
                    obj.status = item.get("status", "")
                    # Extract progress from status if it contains %
                    status = item.get("status", "")
                    if "%" in status:
                        try:
                            pct = int(status.replace("%", ""))
                            obj.progress = pct / 100.0
                        except:
                            pass

        # Update button states
        is_downloading = getattr(self.queue_manager, 'is_downloading', False)
        self.btn_start.set_sensitive(not is_downloading and queue_count > 0)
        self.btn_stop.set_sensitive(is_downloading)

        # Show correct view with smooth transition
        if queue_count > 0:
            if self.stack.get_visible_child_name() != "list":
                self.stack.set_visible_child_name("list")
        else:
            if self.stack.get_visible_child_name() != "empty":
                self.stack.set_visible_child_name("empty")

    def _calculate_stats(self, queue):
        """Calculate download statistics"""
        self.stats = {"queue": 0, "active": 0, "completed": 0, "failed": 0}

        for item in queue:
            status = item.get("status", "")
            if "Tamamlandı" in status or "Atlandı" in status:
                self.stats["completed"] += 1
            elif "İndiriliyor" in status or "Dönüştürülüyor" in status or "%" in status:
                self.stats["active"] += 1
            elif "Hata" in status:
                self.stats["failed"] += 1
            else:
                self.stats["queue"] += 1

    def _update_stats_label(self):
        """Update statistics with refined styling"""
        parts = []

        if self.stats['queue'] > 0:
            parts.append(f"📋 {self.stats['queue']} bekliyor")
        if self.stats['active'] > 0:
            parts.append(f"⚡ {self.stats['active']} aktif")
        if self.stats['completed'] > 0:
            parts.append(f"✓ {self.stats['completed']} bitti")
        if self.stats['failed'] > 0:
            parts.append(f"✗ {self.stats['failed']} hata")

        text = " · ".join(parts) if parts else "Kuyruk boş"
        self.stats_label.set_text(text)

    # --- BUTTON HANDLERS ---

    def _on_start_clicked(self, btn):
        """Start downloads with animation"""
        if self.queue_manager:
            self.queue_manager.start_downloads()
            self.main_window.show_toast("🚀 İndirmeler başlatıldı!")

    def _on_stop_clicked(self, btn):
        """Stop downloads"""
        if self.queue_manager:
            self.queue_manager.stop_downloads()
            self.main_window.show_toast("⏸️ İndirmeler durduruldu")

    def _on_clear_clicked(self, btn):
        """Clear completed/failed downloads"""
        if not self.queue_manager:
            return

        with self.queue_manager.lock:
            before = len(self.queue_manager.queue)
            self.queue_manager.queue = [
                i for i in self.queue_manager.queue
                if i.get("status") not in ["Tamamlandı", "Atlandı (Mevcut)"]
                and "Hata" not in i.get("status", "")
            ]
            after = len(self.queue_manager.queue)
            removed = before - after

        if removed > 0:
            self.main_window.show_toast(f"🧹 {removed} öğe temizlendi")

        self.update_from_queue()

    def _on_folder_clicked(self, btn):
        """Open downloads folder"""
        try:
            import subprocess
            from settings import get_download_dir
            subprocess.Popen(['xdg-open', get_download_dir()])
        except Exception as e:
            print(f"Error opening folder: {e}")

    def _show_help(self, btn):
        """Show quick help"""
        self.main_window.show_toast(
            "💡 Arama sekmesinden link ekle → Otomatik kuyruğa gelir → "
            "İndirmeleri Başlat düğmesine bas!"
        )

    # --- PUBLIC API ---

    def update_downloads_page_content(self):
        """Legacy compatibility method"""
        self.update_from_queue()

    def update_download_status(self, item_id, message):
        """Update single item status"""
        self._pending_updates.append(("status", item_id, message))

    def update_download_progress(self, item_id, percent, message=""):
        """Update single item progress"""
        self._pending_updates.append(("progress", item_id, percent))
