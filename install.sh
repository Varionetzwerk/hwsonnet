#!/usr/bin/env bash
# HWSonnet — Arch Linux installation script
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

info()    { echo -e "${CYAN}[INFO]${NC} $*"; }
success() { echo -e "${GREEN}[OK]${NC}   $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC} $*"; }
fail()    { echo -e "${RED}[FAIL]${NC} $*" >&2; exit 1; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

info "HWSonnet Installation Script"
echo "=============================="

# ── System packages (pacman) ──────────────────────────────────────────────── #
PACMAN_PKGS=(
    python
    python-pyqt6
    python-psutil
    lm_sensors
    smartmontools
    mesa-utils
    vulkan-tools
    usbutils
    pciutils
    dmidecode
)

info "Checking system packages..."
missing_pkgs=()
for pkg in "${PACMAN_PKGS[@]}"; do
    if ! pacman -Q "$pkg" &>/dev/null; then
        missing_pkgs+=("$pkg")
    fi
done

if [[ ${#missing_pkgs[@]} -gt 0 ]]; then
    warn "Missing packages: ${missing_pkgs[*]}"
    read -rp "Install missing packages with pacman? [Y/n] " answer
    if [[ "${answer,,}" != "n" ]]; then
        sudo pacman -S --needed "${missing_pkgs[@]}"
        success "Packages installed."
    else
        warn "Some features may be unavailable without these packages."
    fi
else
    success "All system packages present."
fi

# ── Python packages (pip) ─────────────────────────────────────────────────── #
info "Installing Python dependencies..."
if command -v pip &>/dev/null; then
    pip install --user -r "$SCRIPT_DIR/requirements.txt"
    success "Python packages installed."
else
    warn "pip not found — skipping Python package installation."
fi

# ── sensors-detect ────────────────────────────────────────────────────────── #
if command -v sensors-detect &>/dev/null; then
    info "lm_sensors detected. Run 'sudo sensors-detect' if sensors show N/A."
fi

# ── Desktop entry ─────────────────────────────────────────────────────────── #
DESKTOP_DIR="$HOME/.local/share/applications"
mkdir -p "$DESKTOP_DIR"

cat > "$DESKTOP_DIR/hwsonnet.desktop" << EOF
[Desktop Entry]
Name=HWSonnet
Comment=Hardware Information Tool
Exec=python3 ${SCRIPT_DIR}/main.py
Terminal=false
Type=Application
Categories=System;
Keywords=hardware;system;info;monitor;cpu;gpu;ram;
EOF

success "Desktop entry created: $DESKTOP_DIR/hwsonnet.desktop"

# ── Launch wrapper ─────────────────────────────────────────────────────────── #
cat > "$HOME/.local/bin/hwsonnet" << EOF
#!/bin/bash
exec python3 "${SCRIPT_DIR}/main.py" "\$@"
EOF
chmod +x "$HOME/.local/bin/hwsonnet"
success "Launcher created: ~/.local/bin/hwsonnet"

echo ""
success "Installation complete!"
echo -e "  Run with: ${CYAN}python3 ${SCRIPT_DIR}/main.py${NC}"
echo -e "  Or:       ${CYAN}hwsonnet${NC}  (if ~/.local/bin is in PATH)"
