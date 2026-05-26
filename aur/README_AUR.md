# HWSonnet — AUR Package

This directory contains the Arch User Repository (AUR) package files.

## Publishing to AUR

### Prerequisites

```bash
# Install AUR submission tools
sudo pacman -S git openssh

# Create an AUR account at https://aur.archlinux.org/register
# Add your SSH key at https://aur.archlinux.org/account/Varionetzwerk/edit
```

### Steps to publish

```bash
# 1. Clone the (empty) AUR repository
git clone ssh://aur@aur.archlinux.org/hwsonnet.git aur-hwsonnet
cd aur-hwsonnet

# 2. Copy package files
cp ../aur/PKGBUILD .
cp ../aur/.SRCINFO .

# 3. Edit PKGBUILD — replace Varionetzwerk and RookDash
#    Also update the GitHub URL to your real repo

# 4. Regenerate .SRCINFO (always do this after editing PKGBUILD)
makepkg --printsrcinfo > .SRCINFO

# 5. Test the package locally
makepkg -si

# 6. Push to AUR
git add PKGBUILD .SRCINFO
git commit -m "Initial upload: hwsonnet v1.0.0"
git push

# Done! Your package is now available via:
# yay -S hwsonnet
```

### Updating the package

```bash
# 1. Update pkgver in PKGBUILD
# 2. Update sha256sums (use 'updpkgsums' from pacman-contrib)
updpkgsums

# 3. Increment pkgrel if same version, reset to 1 for new version
# 4. Regenerate .SRCINFO
makepkg --printsrcinfo > .SRCINFO

# 5. Test
makepkg -si

# 6. Push
git add -A && git commit -m "Update to v1.x.x" && git push
```

### GitHub Actions CI for AUR (optional)

Create `.github/workflows/aur.yml` in your main repo to auto-update the AUR
package when you tag a new release.

## Installation (users)

```bash
# Via yay
yay -S hwsonnet

# Via paru
paru -S hwsonnet

# Manual
git clone https://aur.archlinux.org/hwsonnet.git
cd hwsonnet
makepkg -si
```
