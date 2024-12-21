pkgname='rebornos-profile-manager'
pkgver=1.0.0
pkgrel=1
pkgdesc='A user-friendly tool for creating and restoring backups of user profiles on Arch-based Linux systems.'
arch=('any')
url='https://github.com/DrunkenAlcoholic/Reborn-Profile-Manager'
license=('GPL3')
groups=('rebornos')
depends=('python' 'python-object' 'gtk3')
provides=("${pkgname}")
conflicts=("${pkgname}")
backup=()
source=('Rebornos_Profile_Manager.py')
sha256sums=('998cfa2d90edd5bc6d5d287958e9f43c2e050cc6820c11360b1de759c6bc782f')
          

package() {
    (
        # Install the main Python script
        install -D -m 755 "${srcdir}/Rebornos_Profile_Manager.py" "${pkgdir}/usr/bin/rebornos-profile-manager"

        # TODO: Install the desktop entry for GUI integration
        #install -D -m 644 "${srcdir}/rebornos-profile-manager.desktop" "${pkgdir}/usr/share/applications/rebornos-profile-manager.desktop"

        # TODO: Install the application icon
        # install -D -m 644 "${srcdir}/rebornos-profile-manager.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/rebornos-profile-manager.svg"
    )
}
