# System Info _a2a

A user-friendly Python application that displays comprehensive information about your computer system in an easy-to-understand format. Developed by PealK Tech.

## Motivation

This project was inspired by and dedicated to "swadeONLINE" and his commitment to teaching Linux fundamentals to students. His teaching methods and passion for Linux education motivated the creation of this tool to help students better understand their systems.

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
git clone https://github.com/Kelvin-Charles/_a2a
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

We warmly welcome contributions from everyone! Whether you're fixing bugs, adding new features, improving documentation, or suggesting ideas, your help is appreciated.

### How to Contribute

1. Fork the repository
2. Create your feature branch:
```bash
git checkout -b feature/YourFeature
```

3. Commit your changes:
```bash
git commit -m 'Add some feature'
```

4. Push to the branch:
```bash
git push origin feature/YourFeature
```

5. Open a Pull Request

### Contribution Guidelines

- Keep code clean and well-documented
- Test your changes thoroughly
- Update documentation if needed
- Follow existing code style
- Add comments for complex logic
- Include descriptive commit messages

### Areas for Improvement

- Additional hardware detection methods
- Support for more Linux distributions
- New system information metrics
- Performance optimizations
- UI/UX enhancements
- Additional export formats
- Localization support

We believe in the power of community-driven development and look forward to your contributions!

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Contact

- Developer: Kelvin Charles
- Email: pearlktech@gmail.com
- Phone: +255623391284
- GitHub: https://github.com/Kelvin-Charles

## About

Developed by PealK Tech  
Version: 1.0.0  
Copyright © 2024 PealK Tech. All rights reserved.

## Acknowledgments

Special thanks to:
- swadeONLINE for inspiring this project through his Linux fundamentals teaching
- All contributors who help improve this tool
- The open-source community for providing the amazing libraries used in this project

