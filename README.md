# HWSonnet

**Modern hardware information and monitoring tool for Linux — built with Python 3 + PyQt6.**

Fast, beautiful, and accurate. Think HWiNFO meets Neofetch, with a clean dark UI.

---

## Screenshots (UI Layout)

```
┌─────────┬──────────────────────────────────────────────────────────────┐
│ ⬡ HWSon │  Overview                           ⟳ Live  [JSON] [TXT] [PDF] │
│─────────│──────────────────────────────────────────────────────────────│
│ ⊞ Over  │                                                              │
│ ⬡ CPU   │  [ CPU Gauge ]  [ GPU Gauge ]  [ RAM Gauge ]  [ Temp Gauge ]  │
│ ▦ GPU   │                                                              │
│ ≡ RAM   │  ┌──────────────┐ ┌──────────────┐ ┌──────┐ ┌────────────┐  │
│ ⊟ Store │  │ CPU: i7-…    │ │ GPU: RTX …   │ │ 16GB │ │ 3.6 GHz    │  │
│ ⊕ Net   │  └──────────────┘ └──────────────┘ └──────┘ └────────────┘  │
│ ◎ Sens  │                                                              │
│ ⚙ Sys   │  ┌─────────────────────┐  ┌─────────────────────┐           │
│         │  │   CPU Usage Chart   │  │   RAM Usage Chart   │           │
│         │  │   ___/\___/\        │  │   /‾‾\___/‾\        │           │
│  ◀      │  └─────────────────────┘  └─────────────────────┘           │
└─────────┴──────────────────────────────────────────────────────────────┘
```

---

## Features

| Category | Details |
|----------|---------|
| **CPU** | Name, cores/threads, frequency (live), temperature, cache, per-core usage bars |
| **GPU** | NVIDIA / AMD / Intel, VRAM, utilization, temperature, driver, clocks |
| **RAM** | Total/used/available, swap, type, speed, slots |
| **Storage** | SSD/HDD/NVMe detection, SMART status, read/write speed, partitions |
| **Network** | All interfaces, IPv4/IPv6, WiFi SSID/signal, live bandwidth charts |
| **Sensors** | Temperatures, fan RPM, battery (via lm_sensors / hwmon) |
| **System** | OS, kernel, DE, shell, uptime, mainboard, BIOS, package count |
| **Export** | JSON, TXT, PDF |
| **Live charts** | Smooth rolling charts, no external chart library needed |

---

## Requirements

### System packages (Arch Linux)

```bash
sudo pacman -S python python-pyqt6 python-psutil lm_sensors smartmontools \
               mesa-utils vulkan-tools pciutils usbutils dmidecode
```

### Python packages

```bash
pip install -r requirements.txt
```

---

## Installation

```bash
git clone https://github.com/yourname/hwsonnet
cd hwsonnet
./install.sh
```

The installer:
- Checks for missing pacman packages
- Installs Python dependencies via pip
- Creates a `.desktop` file for your app launcher
- Creates a `hwsonnet` command in `~/.local/bin`

---

## Running

```bash
python main.py
# or after install:
hwsonnet
```

---

## Optional setup

### lm_sensors

For accurate temperature and fan data:

```bash
sudo sensors-detect   # follow prompts, then reboot or modprobe the suggested modules
sensors               # verify output
```

### NVIDIA GPU support

Requires the proprietary NVIDIA driver (not `nouveau`):

```bash
sudo pacman -S nvidia nvidia-utils
# nvidia-smi should be available after driver installation
```

### AMD GPU support

Works out of the box via `/sys/class/drm` — no extra packages needed.

### SMART disk data

```bash
sudo pacman -S smartmontools
# Run HWSonnet as root, or add yourself to the 'disk' group:
sudo usermod -aG disk $USER
```

---

## Project Structure

```
hwsonnet/
├── main.py                    # Entry point
├── requirements.txt
├── install.sh
├── src/
│   ├── app.py                 # QApplication setup + theme
│   ├── core/
│   │   ├── workers.py         # Background QThread workers
│   │   └── collectors/        # One collector per subsystem
│   │       ├── cpu_collector.py
│   │       ├── gpu_collector.py
│   │       ├── ram_collector.py
│   │       ├── storage_collector.py
│   │       ├── network_collector.py
│   │       ├── sensors_collector.py
│   │       └── system_collector.py
│   ├── ui/
│   │   ├── main_window.py     # Master window
│   │   ├── sidebar.py         # Collapsible nav sidebar
│   │   ├── styles/
│   │   │   └── dark_theme.py  # Global QSS stylesheet + palette
│   │   ├── widgets/
│   │   │   ├── info_card.py   # InfoCard / KeyValueCard
│   │   │   ├── live_chart.py  # Custom QPainter rolling chart
│   │   │   └── gauge_widget.py # Circular gauge + mini bar gauge
│   │   └── pages/
│   │       ├── overview_page.py
│   │       ├── cpu_page.py
│   │       ├── gpu_page.py
│   │       ├── ram_page.py
│   │       ├── storage_page.py
│   │       ├── network_page.py
│   │       ├── sensors_page.py
│   │       └── system_page.py
│   └── utils/
│       ├── format.py          # Value formatting helpers
│       ├── export.py          # JSON / TXT / PDF export
│       └── logger.py          # Centralized logging
```

---

## Architecture

- **MVVM-inspired**: collectors = Model, pages = View+ViewModel, workers = async binding
- **No blocking UI**: all I/O and subprocess calls run in `QThread` workers
- **No external chart library**: live charts drawn entirely with `QPainter`
- **Graceful degradation**: missing tools (nvidia-smi, dmidecode, smartctl) → "N/A"

---

## Build (AppImage / Flatpak)

### AppImage via PyInstaller

```bash
pip install pyinstaller
pyinstaller --onefile --windowed --name HWSonnet main.py
# Then package with appimagetool
```

### AUR PKGBUILD (skeleton)

```
pkgname=hwsonnet
pkgver=1.0.0
pkgrel=1
pkgdesc="Modern hardware info tool for Linux"
arch=('x86_64')
depends=('python' 'python-pyqt6' 'python-psutil')
optdepends=('lm_sensors' 'smartmontools' 'nvidia-utils')
source=("git+https://github.com/yourname/hwsonnet.git")
```

---

## License

MIT
