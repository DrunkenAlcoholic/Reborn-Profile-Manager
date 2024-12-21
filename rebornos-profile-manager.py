#!/usr/bin/env python3
import gi
import os
import tarfile
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

# Constants
LOGO_PATH = "/usr/share/pixmaps/rebornos.svg"
OPERATION_BACKUP = "backup"
OPERATION_RESTORE = "restore"
COLOR_ABORT = "red"
COLOR_START = "green"

# Backup Items
BACKUP_ITEMS = {
    ".bashrc": None,
    ".bash_profile": None,
    ".ssh": None,
    ".gnupg": None,
    ".profile": None,
    ".config": "recursive",
    ".local": "recursive",
    "Documents": None,
    "Pictures": None,
}

EXCLUDED_ITEMS = [
    "gtk-2.0",
    "gtk-3.0",
    "some_file"
]

class RebornProfileManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="Backup and Restore")
        self.set_default_size(600, 400)

        # Default settings
        self.default_save_location = Path.home() / "Downloads"
        self.compression_enabled = True

        self.backup_in_progress = False
        self.abort_event = Event()

        # Track selected recursive items
        self.selected_recursive_items = set()

        # Main container with padding
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_box.set_margin_top(10)
        self.main_box.set_margin_bottom(10)
        self.main_box.set_margin_start(10)
        self.main_box.set_margin_end(10)
        self.add(self.main_box)

        # Header Bar
        self.create_header_bar()

        # Notebook (Tabs)
        self.notebook = Gtk.Notebook()
        self.main_box.pack_start(self.notebook, True, True, 0)

        # Tabs
        self.create_backup_tab()
        self.create_restore_tab()
        self.create_settings_tab()

        # Status Bar
        self.statusbar = Gtk.Statusbar()
        self.main_box.pack_end(self.statusbar, False, True, 0)

    def safe_repack_widget(self, container, widget, expand=False, fill=False, padding=0):
        """Safely repacks a widget into a container by removing it from its parent if necessary."""
        if widget.get_parent() is not None:
            #print(f"Removing widget from parent: {widget}")
            widget.get_parent().remove(widget)
        container.pack_start(widget, expand, fill, padding)
        #print(f"Packed widget: {widget}, parent now: {container}")

    def create_header_bar(self):
        header = Gtk.HeaderBar(title="RebornOS Profile Manager")
        header.set_subtitle("Manage your profiles efficiently")
        header.props.show_close_button = True

        if Path(LOGO_PATH).exists():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(LOGO_PATH, 32, 32, True)
            logo_image = Gtk.Image.new_from_pixbuf(pixbuf)
            header.pack_start(logo_image)

        self.set_titlebar(header)

    def create_backup_tab(self):
        backup_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(backup_box, Gtk.Label(label="Backup"))    

        # Backup Items Frame
        frame = Gtk.Frame(label="Select Backup Items")
        frame.set_shadow_type(Gtk.ShadowType.ETCHED_IN)
        frame_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=6)
        frame.add(frame_box)
        backup_box.pack_start(frame, True, True, 0) 

        self.backup_toggles = {}    

        for item, recursive in BACKUP_ITEMS.items():
            full_path = Path.home() / item
            if full_path.exists():
                if recursive == "recursive" and full_path.is_dir():
                    label = Gtk.Label(label=f"{item}/")
                    frame_box.pack_start(label, False, False, 0)    

                    # Create TreeStore
                    tree_store = Gtk.TreeStore(str, bool)
                    tree_view = Gtk.TreeView(model=tree_store)  

                    # Add toggle column
                    toggle_renderer = Gtk.CellRendererToggle()
                    toggle_renderer.set_activatable(True)
                    toggle_renderer.connect("toggled", self.on_tree_item_toggled, tree_store, item)
                    toggle_column = Gtk.TreeViewColumn("Include", toggle_renderer, active=1)
                    tree_view.append_column(toggle_column)  

                    # Add name column
                    text_renderer = Gtk.CellRendererText()
                    name_column = Gtk.TreeViewColumn("Name", text_renderer, text=0)
                    tree_view.append_column(name_column)    

                    # Populate tree and initialize selected items
                    self.populate_tree_store(tree_store, full_path, item)   

                    scrolled_window = Gtk.ScrolledWindow()
                    scrolled_window.add(tree_view)
                    frame_box.pack_start(scrolled_window, True, True, 0)    

                    # Track the tree store for this recursive directory
                    self.backup_toggles[item] = tree_store
                else:
                    toggle = Gtk.CheckButton(label=item)
                    toggle.set_active(True)
                    self.backup_toggles[item] = toggle
                    frame_box.pack_start(toggle, False, False, 0)   

        # Progress Bar and Spinner
        self.progress_bar = Gtk.ProgressBar()
        self.spinner = Gtk.Spinner()
        backup_box.pack_start(self.progress_bar, False, False, 0)
        backup_box.pack_start(self.spinner, False, False, 0)    

        # Backup Button
        self.backup_button = self.create_button("Start Backup", "backup-button", backup_box)
        self.backup_button.connect("clicked", self.on_backup_button_clicked)

    def populate_tree_store(self, tree_store, path, root_key):
        for sub_item in sorted(path.iterdir()):
            if sub_item.is_dir() and sub_item.name not in EXCLUDED_ITEMS:
                full_path = str(sub_item)
                display_name = sub_item.name  # Show just the folder name in the tree view
                tree_store.append(None, [display_name, False])  # Default to unchecked

    def on_tree_item_toggled(self, widget, path, tree_store, root_key):
        tree_iter = tree_store.get_iter(path)
        current_value = tree_store[tree_iter][1]
        tree_store[tree_iter][1] = not current_value  # Toggle the checkbox state   

        # Retrieve folder name and map it to the full path
        folder_name = tree_store[tree_iter][0]
        full_path = str(Path.home() / root_key / folder_name)   

        if not current_value:
            self.selected_recursive_items.add(full_path)  # Add full path to set
        else:
            self.selected_recursive_items.discard(full_path)  # Remove full path from set   

        print(f"Updated selected recursive items: {self.selected_recursive_items}")

    def create_restore_tab(self):
        restore_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(restore_box, Gtk.Label(label="Restore"))  

        # Dropdown and Progress
        label = self.create_label("Select Backup to Restore:", restore_box)
        self.profile_dropdown = Gtk.ComboBoxText()
        self.populate_restore_dropdown()
        self.safe_repack_widget(restore_box, self.profile_dropdown, False, False, 0) 

        # Add Refresh Button
        self.refresh_button = self.create_button("Refresh List", None, restore_box)
        self.refresh_button.connect("clicked", self.on_refresh_button_clicked)
        self.safe_repack_widget(restore_box, self.refresh_button, False, False, 0)   

        self.restore_progress_bar = Gtk.ProgressBar()
        self.restore_spinner = Gtk.Spinner()
        self.safe_repack_widget(restore_box, self.restore_progress_bar, False, False, 0)
        self.safe_repack_widget(restore_box, self.restore_spinner, False, False, 0)  

        # Restore Button
        self.restore_button = self.create_button("Start Restore", None, restore_box)
        self.restore_button.connect("clicked", self.on_restore_button_clicked)
        self.safe_repack_widget(restore_box, self.restore_button, False, False, 0)

    def create_settings_tab(self):
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(settings_box, Gtk.Label(label="Settings"))

        # Folder Selection
        folder_frame = Gtk.Frame(label="Default Backup/Restore Folder")
        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.folder_label = Gtk.Label(label=f"Current Folder: {self.default_save_location}")
        folder_box.pack_start(self.folder_label, True, True, 0)

        select_folder_button = self.create_button("Select Folder", None, folder_box)
        select_folder_button.connect("clicked", self.on_select_backup_folder)
        folder_frame.add(folder_box)
        settings_box.pack_start(folder_frame, False, False, 0)

        # Compression Toggle
        compression_toggle = Gtk.CheckButton(label="Enable Compression")
        compression_toggle.set_active(self.compression_enabled)
        compression_toggle.connect("toggled", self.on_toggle_compression)
        settings_box.pack_start(compression_toggle, False, False, 0)

    def create_toggle(self, label, container):
        toggle = Gtk.CheckButton(label=label)
        toggle.set_active(True)
        container.pack_start(toggle, False, False, 0)
        return toggle

    def create_label(self, text, container):
        label = Gtk.Label(label=text)
        container.pack_start(label, False, False, 0)
        return label

    def create_button(self, label, css_name, container):
        button = Gtk.Button(label=label)
        if css_name:
            button.set_name(css_name)
        container.pack_start(button, False, False, 0)
        return button

    def on_refresh_button_clicked(self, widget):
        print("Refreshing restore dropdown...")
        self.populate_restore_dropdown()
        print("Restore dropdown refreshed.")

    def on_backup_button_clicked(self, widget):
        if self.backup_in_progress:
            print("Backup aborted by user.")
            self.abort_event.set()
            self.reset_backup_state()
        else:
            # Collect non-recursive items
            selected_items = [
                str(Path.home() / item)
                for item, toggle in self.backup_toggles.items()
                if isinstance(toggle, Gtk.CheckButton) and toggle.get_active()
            ]   

            # Collect recursive items
            for item, recursive in BACKUP_ITEMS.items():
                if recursive == "recursive" and item in self.backup_toggles:
                    tree_store = self.backup_toggles[item]
                    selected_items.extend(self.get_checked_recursive_items(tree_store, item))   

            print(f"Final selected items for backup: {selected_items}") 

            if not selected_items:
                self.show_message_dialog("Error", "No items selected for backup!")
                return  

            self.abort_event.clear()
            self.backup_in_progress = True
            self.update_backup_button("Abort", COLOR_ABORT)
            self.spinner.start()
            Thread(target=self.perform_backup, args=(selected_items,), daemon=True).start()

    def get_checked_recursive_items(self, tree_store, root_key):
        checked_items = []
        tree_iter = tree_store.get_iter_first() 

        while tree_iter:
            if tree_store[tree_iter][1]:  # If checked
                folder_name = tree_store[tree_iter][0]
                full_path = str(Path.home() / root_key / folder_name)
                checked_items.append(full_path)
            tree_iter = tree_store.iter_next(tree_iter) 

        return checked_items

    def perform_backup(self, items):
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        file_extension = "tar.gz" if self.compression_enabled else "tar"
        backup_file = self.default_save_location / f"backup_{timestamp}.{file_extension}"   

        try:
            mode = "w:gz" if self.compression_enabled else "w"
            total_files = self.count_files(items)
            processed_files = 0 

            with tarfile.open(backup_file, mode) as tar:
                for item in items:
                    if self.abort_event.is_set():
                        print("Backup aborted by user.")
                        GLib.idle_add(self.show_message_dialog, "Aborted", "Backup was aborted!")
                        GLib.idle_add(self.reset_backup_state)
                        return  

                    full_path = Path(item)
                    if not full_path.exists():
                        print(f"Skipping non-existent item: {item}")
                        continue    

                    if full_path.is_dir():
                        print(f"Backing up directory: {item}")
                        for root, _, files in os.walk(full_path):
                            for file in files:
                                file_path = os.path.join(root, file)
                                tar.add(file_path, arcname=os.path.relpath(file_path, Path.home()))
                                processed_files += 1
                                GLib.idle_add(self.update_progress_bar, processed_files / total_files, OPERATION_BACKUP)
                    elif full_path.is_file():
                        print(f"Backing up file: {item}")
                        tar.add(full_path, arcname=os.path.basename(item))
                        processed_files += 1
                        GLib.idle_add(self.update_progress_bar, processed_files / total_files, OPERATION_BACKUP)    

            GLib.idle_add(self.show_message_dialog, "Success", f"Backup completed: {backup_file}")
        except Exception as e:
            print(f"Error during backup: {e}")
            GLib.idle_add(self.show_message_dialog, "Error", f"Backup failed: {str(e)}")
        finally:
            GLib.idle_add(self.reset_backup_state)

    def reset_backup_state(self):
        self.backup_in_progress = False
        self.spinner.stop()
        self.update_progress_bar(0.0, OPERATION_BACKUP)
        self.update_backup_button("Start Backup", COLOR_START)

    def update_backup_button(self, label, color):
        self.backup_button.set_label(label)

        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(
            f"""
            #backup-button {{
                background-color: {color};
                color: white;
            }}
            """.encode("utf-8")
        )
        style_context = self.backup_button.get_style_context()
        style_context.add_provider(css_provider, Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)
        style_context.add_class("backup-button")

    def update_progress_bar(self, fraction, operation):
        bar = self.progress_bar if operation == OPERATION_BACKUP else self.restore_progress_bar
        bar.set_fraction(fraction)
        bar.set_text(f"{int(fraction * 100)}%")
        bar.set_show_text(True)

    def on_restore_button_clicked(self, widget):
        profile = self.profile_dropdown.get_active_text()
        if not profile:
            self.show_message_dialog("Error", "No backup profile selected!")
            return
        # Create a warning dialog 
        dialog = Gtk.MessageDialog(
            parent=self,
            flags=Gtk.DialogFlags.MODAL,
            type=Gtk.MessageType.WARNING,  # Warning icon
            buttons=Gtk.ButtonsType.YES_NO,
            message_format="⚠️ Warning: This will overwrite existing configurations with the ones from the backup. Do you want to proceed?",
        )
        response = dialog.run()
        dialog.destroy()

        if response != Gtk.ResponseType.YES:
            print("Restore aborted by the user.")
            return

        backup_file = self.default_save_location / profile
        self.restore_spinner.start()
        Thread(target=self.perform_restore, args=(backup_file,), daemon=True).start()

    def perform_restore(self, backup_file):
        try:
            with tarfile.open(backup_file, "r:*") as tar:
                members = tar.getmembers()
                total_members = len(members)

                for i, member in enumerate(members):
                    tar.extract(member, path=Path.home())
                    GLib.idle_add(self.update_progress_bar, (i + 1) / total_members, OPERATION_RESTORE)

            GLib.idle_add(self.show_message_dialog, "Success", "Restore completed!")
        except Exception as e:
            GLib.idle_add(self.show_message_dialog, "Error", f"Restore failed: {str(e)}")
        finally:
            GLib.idle_add(self.restore_spinner.stop)

    def on_select_backup_folder(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Default Backup/Restore Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if dialog.run() == Gtk.ResponseType.OK:
            self.default_save_location = Path(dialog.get_filename())
            self.folder_label.set_text(f"Current Folder: {self.default_save_location}")
            self.populate_restore_dropdown()

        dialog.destroy()

    def populate_restore_dropdown(self):
        self.profile_dropdown.remove_all()
        if self.default_save_location.exists():
            for file in self.default_save_location.glob("*.tar*"):
                self.profile_dropdown.append_text(file.name)

    def on_toggle_compression(self, widget):
        self.compression_enabled = widget.get_active()
        print(f"Compression enabled: {self.compression_enabled}")

    def show_message_dialog(self, title, message):
        dialog = Gtk.Dialog(title=title, transient_for=self, flags=0)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        if Path(LOGO_PATH).exists():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(LOGO_PATH, 64, 64, True)
            logo_image = Gtk.Image.new_from_pixbuf(pixbuf)
            content_box.pack_start(logo_image, False, False, 10)

        message_label = Gtk.Label(label=message)
        message_label.set_xalign(0)
        content_box.pack_start(message_label, True, True, 10)

        content_area.add(content_box)
        content_box.show_all()

        dialog.run()
        dialog.destroy()

    def count_files(self, paths):
        count = 0
        for path in paths:
            if os.path.isfile(path):
                count += 1
            elif os.path.isdir(path):
                for _, _, files in os.walk(path):
                    count += len(files)
        return count

if __name__ == "__main__":
    app = RebornProfileManager()
    app.connect("destroy", Gtk.main_quit)
    app.show_all()
    Gtk.main()