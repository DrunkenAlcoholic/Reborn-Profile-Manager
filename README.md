# RebornOS Profile Manager

RebornOS Profile Manager is a user-friendly tool for creating and restoring backups of important user profile data on Linux operating systems. Designed with simplicity and functionality in mind, making it easy to manage backups and restores of your most important files and directories with just a few clicks.

---

## Features

- **Backup User Profiles**:
  - Select specific files and folders like `.config`, `.bashrc`, `.ssh`, `.gnupg`, `Documents`, and more.
  - Toggle which items to include in the backup.
  - Compress backups for efficient storage (using `.tar.gz`).

- **Restore Profiles**:
  - Restore from previously created backups.
  - Automatically lists available backups for quick selection.
  - Handles both compressed (`.tar.gz`) and uncompressed (`.tar`) backups.

- **Settings Tab**:
  - Specify the default folder for backup and restore operations.
  - Enable or disable compression for backups.

- **Progress Indicators**:
  - Real-time progress bar updates for both backup and restore processes.
  - Spinner animation during operations to ensure responsiveness.

- **Visual Enhancements**:
  - Modern GTK-based interface that integrates with Linux system themes.

---

## Installation

### For Arch Linux and Arch-Based Distributions

#### Prerequisites
- **Python 3.12 or later**
- **Python PyGObject**
- **GTK 3**
  ```bash
  sudo pacman -S python python-gobject gtk3
  ```

#### Install Using the PKGBUILD File

1. Clone the repository:
   ```bash
   git clone https://github.com/DrunkenAlcoholic/Reborn-Profile-Manager.git
   cd Reborn-Profile-Manager
   ```

2. Build and install the package:
   ```bash
   makepkg -si
   ```

   This will:
   - Install the `rebornos-profile-manager` script to `/usr/bin/rebornos-profile-manager`.

3. Run the application:
   ```bash
   rebornos-profile-manager
   ```

### For Other Linux Distributions

#### Prerequisites
- **Python 3.12 or later**
- **GTK 3**
  - Install GTK and Python GObject bindings using your distribution's package manager.
    - Example for Debian-based systems:
      ```bash
      sudo apt install python3-gi gir1.2-gtk-3.0
      ```

#### Running the Application

1. Clone the repository:
   ```bash
   git clone https://github.com/DrunkenAlcoholic/Reborn-Profile-Manager.git
   cd Reborn-Profile-Manager
   ```

2. Make the Python script executable:
   ```bash
   chmod +x rebornos-profile-manager.py
   ```

3. Run the application:
   ```bash
   ./rebornos-profile-manager.py
   ```

---

## Usage

1. **Backup**:
   - Navigate to the `Backup` tab.
   - Toggle the items you want to include in the backup.
   - Click `Start Backup` to create a backup in the default folder.
   - A success dialog will confirm completion.

2. **Restore**:
   - Navigate to the `Restore` tab.
   - Select the backup file from the dropdown menu.
   - Click `Start Restore` to restore the selected backup.
   - A success dialog will confirm completion.

3. **Settings**:
   - Navigate to the `Settings` tab.
   - Set the default folder for backups and restores.
   - Enable or disable compression based on your preference.

---

## Screenshots

### Backup Tab

![Backup Tab Screenshot](img/rpm.backup.ss.jpg)

### Restore Tab

![Restore Tab Screenshot](img/rpm.restore.ss.jpg)

### Settings Tab

![Settings Tab Screenshot](img/rpm.settings.ss.jpg)

---

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add new feature"
   ```
4. Push to your branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.

---

## License

This project is licensed under the GPLv3 License. See the [LICENSE](LICENSE) file for details.


---

## Contact

For issues or feature requests, please open an issue in the [GitHub repository](https://github.com/DrunkenAlcoholic/Reborn-Profile-Manager/issues).




