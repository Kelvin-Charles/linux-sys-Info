# System Info _a2a

A user-friendly Python application that displays comprehensive information about your computer system in an easy-to-understand format. Developed by PealK Tech.

## Features

- 🖥️ Hardware Information
  - CPU details (model, cores, speed, usage, temperature)
  - RAM usage and specifications
  - Storage information (drives, capacity, free space, HDD/SSD type)
  - GPU details with temperature and usage
  - Motherboard and BIOS information
  - USB and PCI devices
  - Sound devices

- 🌐 Network Information
  - Network interfaces with speeds
  - WiFi details and signal strength
  - Public IP and geolocation
  - Network statistics and usage
  - DNS configuration
  - Routing table
  - Active connections

- 💻 System Information
  - Operating System details
  - Linux distribution detection
  - Running processes
  - Installed software and updates
  - System uptime and boot time
  - Security settings (firewall, SELinux)

## Project Structure

```bash
_a2a/
├── __init__.py
├── hardware_info.py
├── network_info.py
├── system_info.py
├── utils.py
└── README.md
```

## Installation

1. Clone this repository:
```bash
git clone https://github.com/PealKTech/_a2a
cd _a2a
```

2. Install required packages:
```bash
pip install -r requirements.txt
```

## Usage

Run the application:
```bash
python run.py
```

The information will be displayed in an organized, easy-to-read format with options to:
- View all system information
- View specific categories
- Export information to HTML or TXT file
- Refresh information in real-time

## Features

- 🚀 Cross-platform support (Windows and Linux)
- 📊 Beautiful console output using Rich
- 💾 Comprehensive hardware detection
- 🔍 Detailed error handling
- 🐧 Distribution-agnostic on Linux
- 📤 Export capabilities
- 🎨 User-friendly interface

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## About

Developed by PealK Tech  
Version: 1.0.0  
GitHub: https://github.com/PealKTech

