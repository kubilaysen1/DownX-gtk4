import gi
import threading
import time
import html
import os

gi.require_version("Gtk", "4.0")
gi.require_version("Adw", "1")
from gi.repository import Gtk, Adw, GObject, GLib, Gio, Gdk

try:
    from youtube_client import YouTubeClient
except ImportError:
    print("⚠️ YouTubeClient not found")
    YouTubeClient = None

# --- DATA MODEL ---
class SearchResultObject(GObject.Object):
    __gtype_name__ = 'SearchResultObject'

    def __init__(self, title, channel, duration, url):
        super().__init__()
        self._title = html.escape(title)
        self._channel = html.escape(channel)
        self._duration = duration
        self._url = url

    @GObject.Property(type=str)
    def title(self):
        return self._title

    @GObject.Property(type=str)
    def subtitle(self):
        return f"{self._channel} • {self._duration}"

    @GObject.Property(type=str)
    def url(self):
        return self._url


class SearchTab(Adw.Bin):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.yt_client = YouTubeClient() if YouTubeClient else None

        # --- MAIN LAYOUT ---
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=0)
        self.set_child(main_box)

        # 1. SEARCH BAR (top)
        search_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        search_box.set_margin_top(16)
        search_box.set_margin_bottom(8)
        search_box.set_margin_start(16)
        search_box.set_margin_end(16)

        clamp = Adw.Clamp(maximum_size=600)
        self.search_entry = Gtk.SearchEntry(
            placeholder_text="YouTube / Spotify link veya şarkı adı..."
        )
        self.search_entry.add_css_class("pill")
        self.search_entry.connect("search-changed", self._on_search_changed)
        self.search_entry.connect("activate", self._on_search_activate)

        clamp.set_child(self.search_entry)
        search_box.append(clamp)

        # Quick action buttons
        actions = Gtk.Box(spacing=8)
        actions.set_halign(Gtk.Align.CENTER)

        btn_paste = Gtk.Button(label="📋 Yapıştır")
        btn_paste.add_css_class("pill")
        btn_paste.connect("clicked", self._on_paste_clicked)
        actions.append(btn_paste)

        btn_txt = Gtk.Button(label="📄 TXT Yükle")
        btn_txt.add_css_class("pill")
        btn_txt.connect("clicked", self._on_txt_clicked)
        actions.append(btn_txt)

        search_box.append(actions)
        main_box.append(search_box)

        # 2. STACK (empty / loading / results / error)
        self.stack = Gtk.Stack()
        self.stack.set_vexpand(True)
        self.stack.set_transition_type(Gtk.StackTransitionType.CROSSFADE)
        main_box.append(self.stack)

        # A) Empty state
        self.status_page = Adw.StatusPage()
        self.status_page.set_icon_name("system-search-symbolic")
        self.status_page.set_title("Müzik ve Video Ara")
        self.status_page.set_description(
            "İstediğin şarkıyı yaz veya link yapıştır.\n"
            "YouTube ve Spotify destekleniyor."
        )
        self.stack.add_named(self.status_page, "empty")

        # B) Loading
        spinner_page = Adw.StatusPage()
        spinner = Gtk.Spinner()
        spinner.set_size_request(48, 48)
        spinner.start()
        spinner_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        spinner_box.set_halign(Gtk.Align.CENTER)
        spinner_box.append(spinner)
        spinner_box.append(Gtk.Label(label="İşleniyor..."))
        spinner_page.set_child(spinner_box)
        spinner_page.set_title("Lütfen Bekleyin")
        self.stack.add_named(spinner_page, "loading")

        # C) Results list
        self.store = Gio.ListStore(item_type=SearchResultObject)
        self.selection_model = Gtk.NoSelection(model=self.store)

        factory = Gtk.SignalListItemFactory()
        factory.connect("setup", self._on_factory_setup)
        factory.connect("bind", self._on_factory_bind)

        self.list_view = Gtk.ListView(model=self.selection_model, factory=factory)
        self.list_view.add_css_class("navigation-sidebar")

        list_clamp = Adw.Clamp(maximum_size=900)
        list_clamp.set_child(self.list_view)

        scrolled = Gtk.ScrolledWindow()
        scrolled.set_child(list_clamp)
        self.stack.add_named(scrolled, "results")

        # D) Error
        self.error_page = Adw.StatusPage()
        self.error_page.set_icon_name("dialog-error-symbolic")
        self.error_page.set_title("Bir Hata Oluştu")
        self.stack.add_named(self.error_page, "error")

    def _on_factory_setup(self, factory, list_item):
        """Setup list item UI"""
        row = Adw.ActionRow()
        row.set_activatable(True)

        # Add button
        btn = Gtk.Button(icon_name="list-add-symbolic")
        btn.set_valign(Gtk.Align.CENTER)
        btn.add_css_class("flat")
        btn.add_css_class("circular")
        btn.set_tooltip_text("Kuyruğa Ekle")
        btn.connect("clicked", self._on_add_wrapper, list_item)
        row.add_suffix(btn)

        # Icon
        icon = Gtk.Image(icon_name="video-x-generic-symbolic")
        row.add_prefix(icon)

        list_item.set_child(row)

    def _on_factory_bind(self, factory, list_item):
        """Bind data"""
        row = list_item.get_child()
        item = list_item.get_item()

        item.bind_property("title", row, "title", GObject.BindingFlags.SYNC_CREATE)
        item.bind_property("subtitle", row, "subtitle", GObject.BindingFlags.SYNC_CREATE)

    def _on_add_wrapper(self, btn, list_item):
        """Add to queue wrapper"""
        item = list_item.get_item()
        if item:
            self._on_add_to_queue(btn, item)

    # --- EVENTS ---

    def _on_search_changed(self, entry):
        text = entry.get_text()
        if not text:
            self.stack.set_visible_child_name("empty")

    def _on_search_activate(self, entry):
        query = entry.get_text()
        if not query:
            return

        # Direct link
        if "http" in query and ("://" in query):
            if self.main_window.queue_manager:
                self.main_window.queue_manager.add_url_to_queue(query, clear_queue=True)
                self._show_toast("Link kuyruğa eklendi!")
            entry.set_text("")
            return

        # Search
        self.stack.set_visible_child_name("loading")
        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        """Search thread"""
        results = []
        error = None
        try:
            if self.yt_client:
                results = self.yt_client.search_videos(query, limit=15)
            else:
                error = "YouTube client not available"
        except Exception as e:
            error = str(e)
            print(f"Search error: {e}")

        GLib.idle_add(self._update_results, results, error)

    def _update_results(self, results, error):
        """Update UI with results"""
        if error:
            self.error_page.set_description(error)
            self.stack.set_visible_child_name("error")
            return

        self.store.remove_all()

        if not results:
            self.error_page.set_title("Sonuç Bulunamadı")
            self.error_page.set_description("Farklı kelimeler deneyin")
            self.stack.set_visible_child_name("error")
            return

        for vid in results:
            duration = str(vid.get('duration', ''))
            self.store.append(SearchResultObject(
                vid.get('title', 'No Title'),
                vid.get('channel', 'Unknown'),
                duration,
                vid.get('url', '')
            ))

        self.stack.set_visible_child_name("results")

    def _on_add_to_queue(self, btn, item):
        """Add to queue"""
        if self.main_window.queue_manager:
            self.main_window.queue_manager.add_url_to_queue(item.url, clear_queue=False)
            btn.set_icon_name("object-select-symbolic")
            btn.set_sensitive(False)
            self._show_toast(f"'{item.title}' kuyruğa eklendi!")

    def _on_paste_clicked(self, btn):
        """Paste from clipboard"""
        clipboard = Gdk.Display.get_default().get_clipboard()
        clipboard.read_text_async(None, self._on_paste_finish)

    def _on_paste_finish(self, clipboard, result):
        try:
            text = clipboard.read_text_finish(result)
            if text:
                self.search_entry.set_text(text)
                self._on_search_activate(self.search_entry)
        except Exception as e:
            print(f"Paste error: {e}")

    def _on_txt_clicked(self, btn):
        """Load TXT file"""
        dialog = Gtk.FileDialog()
        dialog.set_title("İndirme Listesi Seç (.txt)")

        filter_list = Gio.ListStore.new(Gtk.FileFilter)
        f = Gtk.FileFilter()
        f.set_name("Metin Dosyaları")
        f.add_mime_type("text/plain")
        f.add_pattern("*.txt")
        filter_list.append(f)
        dialog.set_filters(filter_list)

        dialog.open(self.main_window, None, self._on_txt_selected)

    def _on_txt_selected(self, dialog, result):
        try:
            file = dialog.open_finish(result)
            if file:
                path = file.get_path()
                threading.Thread(target=self._process_txt, args=(path,), daemon=True).start()
        except Exception as e:
            print(f"File selection error: {e}")

    def _process_txt(self, path):
        """Process TXT file"""
        if not path or not os.path.exists(path):
            return

        count = 0
        try:
            with open(path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            GLib.idle_add(lambda: self.stack.set_visible_child_name("loading"))

            # İlk link için kuyruğu temizle, sonrakiler için eklemeye devam et
            first_link = True

            for line in lines:
                link = line.strip()
                if not link or link.startswith("#"):
                    continue

                if "http" in link:
                    if self.main_window.queue_manager:
                        # İlk link: kuyruğu temizle, sonrakiler: ekle
                        self.main_window.queue_manager.add_url_to_queue(
                            link,
                            clear_queue=first_link,
                            batch_name="TXT Batch"
                        )
                        first_link = False
                        count += 1
                        time.sleep(0.1)

            print(f"Loaded {count} links from TXT")
            GLib.idle_add(self._show_toast, f"✅ {count} link kuyruğa eklendi!")
            GLib.idle_add(lambda: self.stack.set_visible_child_name("empty"))

        except Exception as e:
            print(f"TXT error: {e}")
            GLib.idle_add(self._show_toast, "TXT okuma hatası!")
            GLib.idle_add(lambda: self.stack.set_visible_child_name("empty"))

    def _show_toast(self, message):
        """Show toast"""
        if hasattr(self.main_window, 'show_toast'):
            self.main_window.show_toast(message)
        else:
            print(f"[TOAST] {message}")
