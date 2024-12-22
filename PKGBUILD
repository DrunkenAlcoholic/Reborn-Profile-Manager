pkgname='rebornos-profile-manager'
pkgver=1.0.1
pkgrel=1
pkgdesc='A user-friendly tool for creating and restoring backups of user profiles on Arch-based Linux systems.'
arch=('any')
url='https://github.com/DrunkenAlcoholic/Reborn-Profile-Manager'
license=('GPL3')
groups=('rebornos')
depends=('python' 'python-gobject' 'gtk3')
provides=("${pkgname}")
conflicts=("${pkgname}")
backup=()
source=('rebornos-profile-manager.py')
sha256sums=('28fafa048f57f1601d45e4fba14f36608179023c3ad76e0d8f9c18ee1681b39c')
          

package() {
    (
        # Install the main Python script
        install -D -m 755 "${srcdir}/rebornos-profile-manager.py" "${pkgdir}/usr/bin/rebornos-profile-manager"

        # TODO: Install the desktop entry for GUI integration
        #install -D -m 644 "${srcdir}/rebornos-profile-manager.desktop" "${pkgdir}/usr/share/applications/rebornos-profile-manager.desktop"

        # TODO: Install the application icon
        # install -D -m 644 "${srcdir}/rebornos-profile-manager.svg" "${pkgdir}/usr/share/icons/hicolor/scalable/apps/rebornos-profile-manager.svg"
    )
}
