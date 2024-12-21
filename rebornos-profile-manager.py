#!/usr/bin/env python
import gi
import os
import tarfile
from pathlib import Path
from datetime import datetime
from threading import Thread, Event

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GdkPixbuf, GLib

# Define backup items
BACKUP_ITEMS = [
    ".bashrc",
    ".bash_profile",
    ".ssh",
    ".gnupg",
    ".profile",
    ".config",
    ".local",
    "Documents",
    "Pictures",
]

# Define logo location
LOGO_PATH = "/usr/share/pixmaps/rebornos.svg"

class RebornProfileManager(Gtk.Window):
    def __init__(self):
        super().__init__(title="Backup and Restore")
        self.set_default_size(600, 400)

        # Default settings
        self.default_save_location = Path.home() / "Downloads"
        self.compression_enabled = True

        self.backup_in_progress = False
        self.abort_event = Event()
        self.restore_folder = self.default_save_location

        # Main container with padding
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.main_box.set_margin_top(10)
        self.main_box.set_margin_bottom(10)
        self.main_box.set_margin_start(10)
        self.main_box.set_margin_end(10)
        self.add(self.main_box)

        # Header Bar with Logo
        self.create_header_bar()

        # Notebook (Tabs)
        self.notebook = Gtk.Notebook()
        self.main_box.pack_start(self.notebook, True, True, 0)

        # Create Tabs
        self.create_backup_tab()
        self.create_restore_tab()
        self.create_settings_tab()

        # Status Bar
        self.statusbar = Gtk.Statusbar()
        self.main_box.pack_end(self.statusbar, False, True, 0)

    def create_header_bar(self):
        header = Gtk.HeaderBar(title="RebornOS Profile Manager")
        header.set_subtitle("Manage your profiles efficiently")
        header.props.show_close_button = True

        # Load the logo image
        logo_path = LOGO_PATH
        if Path(logo_path).exists():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 32, 32, True)
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

        # Toggle Switches for Items
        self.backup_toggles = {}
        for item in BACKUP_ITEMS:
            toggle = Gtk.CheckButton(label=item)
            toggle.set_active(True)
            self.backup_toggles[item] = toggle
            frame_box.pack_start(toggle, False, False, 0)

        # Progress Bar
        self.progress_bar = Gtk.ProgressBar()
        backup_box.pack_start(self.progress_bar, False, False, 0)

        # Spinner
        self.spinner = Gtk.Spinner()
        backup_box.pack_start(self.spinner, False, False, 0)

        # Backup Button
        self.backup_button = Gtk.Button(label="Start Backup")
        self.backup_button.set_name("backup-button")
        self.backup_button.connect("clicked", self.on_backup_button_clicked)
        backup_box.pack_start(self.backup_button, False, False, 0)

    def create_restore_tab(self):
        restore_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(restore_box, Gtk.Label(label="Restore"))

        # Dropdown for Backups
        restore_dropdown_label = Gtk.Label(label="Select Backup to Restore:")
        restore_box.pack_start(restore_dropdown_label, False, False, 0)

        self.profile_dropdown = Gtk.ComboBoxText()
        self.populate_restore_dropdown()
        restore_box.pack_start(self.profile_dropdown, False, False, 0)

        # Progress Bar
        self.restore_progress_bar = Gtk.ProgressBar()
        restore_box.pack_start(self.restore_progress_bar, False, False, 0)

        # Spinner
        self.restore_spinner = Gtk.Spinner()
        restore_box.pack_start(self.restore_spinner, False, False, 0)

        # Restore Button
        restore_button = Gtk.Button(label="Start Restore")
        restore_button.connect("clicked", self.on_restore_button_clicked)
        restore_box.pack_start(restore_button, False, False, 0)

    def create_settings_tab(self):
        settings_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=10)
        self.notebook.append_page(settings_box, Gtk.Label(label="Settings"))

        # Backup/Restore Folder Selection
        folder_frame = Gtk.Frame(label="Default Backup/Restore Folder")
        folder_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)
        self.folder_label = Gtk.Label(label=f"Current Folder: {self.default_save_location}")
        select_folder_button = Gtk.Button(label="Select Folder")
        select_folder_button.connect("clicked", self.on_select_backup_folder)

        folder_box.pack_start(self.folder_label, True, True, 0)
        folder_box.pack_end(select_folder_button, False, False, 0)
        folder_frame.add(folder_box)
        settings_box.pack_start(folder_frame, False, False, 0)

        # Compression Toggle
        compression_toggle = Gtk.CheckButton(label="Enable Compression")
        compression_toggle.set_active(self.compression_enabled)
        compression_toggle.connect("toggled", self.on_toggle_compression)
        settings_box.pack_start(compression_toggle, False, False, 0)

    def on_select_backup_folder(self, widget):
        dialog = Gtk.FileChooserDialog(
            title="Select Default Backup/Restore Folder",
            parent=self,
            action=Gtk.FileChooserAction.SELECT_FOLDER,
        )
        dialog.add_buttons(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL, Gtk.STOCK_OPEN, Gtk.ResponseType.OK)

        if dialog.run() == Gtk.ResponseType.OK:
            self.default_save_location = Path(dialog.get_filename())
            self.restore_folder = self.default_save_location
            self.folder_label.set_text(f"Current Folder: {self.default_save_location}")
            self.populate_restore_dropdown()

        dialog.destroy()

    def populate_restore_dropdown(self):
        self.profile_dropdown.remove_all()
        if self.restore_folder.exists():
            for file in self.restore_folder.glob("*.tar*"):
                self.profile_dropdown.append_text(file.name)

    def on_toggle_compression(self, widget):
        self.compression_enabled = widget.get_active()
        print(f"Compression enabled: {self.compression_enabled}")

    def on_backup_button_clicked(self, widget):
        if self.backup_in_progress:
            print("Backup aborted by user.")
            self.abort_event.set()
            self.reset_backup_state()
        else:
            selected_items = [
                str(Path.home() / item)
                for item, toggle in self.backup_toggles.items()
                if toggle.get_active()
            ]

            if not selected_items:
                self.show_message_dialog("Error", "No items selected for backup!")
                return

            self.abort_event.clear()
            self.backup_in_progress = True
            self.update_backup_button("Abort", "red")
            self.spinner.start()
            Thread(target=self.perform_backup, args=(selected_items,), daemon=True).start()

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
                        GLib.idle_add(self.show_message_dialog, "Aborted", "Backup was aborted!")
                        GLib.idle_add(self.reset_backup_state)
                        return

                    if os.path.isfile(item):
                        tar.add(item, arcname=os.path.basename(item))
                        processed_files += 1
                        GLib.idle_add(self.update_progress_bar, processed_files / total_files)
                    elif os.path.isdir(item):
                        for root, _, files in os.walk(item):
                            for file in files:
                                file_path = os.path.join(root, file)
                                tar.add(file_path, arcname=os.path.relpath(file_path, Path.home()))
                                processed_files += 1
                                GLib.idle_add(self.update_progress_bar, processed_files / total_files)

            GLib.idle_add(self.populate_restore_dropdown)
            GLib.idle_add(self.show_message_dialog, "Success", f"Backup completed: {backup_file}")
        except Exception as e:
            GLib.idle_add(self.show_message_dialog, "Error", f"Backup failed: {str(e)}")
        finally:
            GLib.idle_add(self.reset_backup_state)

    def reset_backup_state(self):
        self.backup_in_progress = False
        self.spinner.stop()
        self.update_progress_bar(0.0)
        self.update_backup_button("Start Backup", "green")

    def update_backup_button(self, label, color):
        self.backup_button.set_label(label)

        # Apply color using CSS
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

    def update_progress_bar(self, fraction):
        self.progress_bar.set_fraction(fraction)
        self.progress_bar.set_text(f"{int(fraction * 100)}%")
        self.progress_bar.set_show_text(True)

    def on_restore_button_clicked(self, widget):
        profile = self.profile_dropdown.get_active_text()
        if not profile:
            self.show_message_dialog("Error", "No backup profile selected!")
            return

        backup_file = self.restore_folder / profile
        self.restore_spinner.start()
        Thread(target=self.perform_restore, args=(backup_file,), daemon=True).start()

    def perform_restore(self, backup_file):
        try:
            with tarfile.open(backup_file, "r:*") as tar:
                members = tar.getmembers()
                total_members = len(members)
            
                # Define a safe filter
                def is_safe_path(base_path, target_path):
                    abs_base_path = os.path.abspath(base_path)
                    abs_target_path = os.path.abspath(target_path)
                    return abs_target_path.startswith(abs_base_path)

                safe_members = []
                for member in members:
                    target_path = Path.home() / member.name
                    if is_safe_path(Path.home(), target_path):
                        safe_members.append(member)
                    else:
                        print(f"Skipping unsafe member: {member.name}")

                # Extract only safe members
                for i, member in enumerate(safe_members):
                    tar.extract(member, path=Path.home())
                    GLib.idle_add(self.update_restore_progress, (i + 1) / total_members)
                
                GLib.idle_add(self.show_message_dialog, "Success", "Restore completed!")
        except Exception as e:
            GLib.idle_add(self.show_message_dialog, "Error", f"Restore failed: {str(e)}")
        finally:
            GLib.idle_add(self.restore_spinner.stop)


    # def perform_restore(self, backup_file):
    #     try:
    #         with tarfile.open(backup_file, "r:*") as tar:
    #             members = tar.getmembers()
    #             total_members = len(members)
    #             for i, member in enumerate(members):
    #                 tar.extract(member, path=Path.home())
    #                 GLib.idle_add(self.update_restore_progress, (i + 1) / total_members)
    #         GLib.idle_add(self.show_message_dialog, "Success", "Restore completed!")
    #     except Exception as e:
    #         GLib.idle_add(self.show_message_dialog, "Error", f"Restore failed: {str(e)}")
    #     finally:
    #         GLib.idle_add(self.restore_spinner.stop)

    def update_restore_progress(self, fraction):
        self.restore_progress_bar.set_fraction(fraction)
        self.restore_progress_bar.set_text(f"{int(fraction * 100)}%")
        self.restore_progress_bar.set_show_text(True)

    def show_message_dialog(self, title, message):
        dialog = Gtk.Dialog(title=title, transient_for=self, flags=0)
        dialog.add_button(Gtk.STOCK_OK, Gtk.ResponseType.OK)

        content_area = dialog.get_content_area()
        content_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=10)

        # Add Logo
        logo_path = LOGO_PATH
        if Path(logo_path).exists():
            pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(logo_path, 64, 64, True)
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
