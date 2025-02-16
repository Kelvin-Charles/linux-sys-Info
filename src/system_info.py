import os
import platform
import sys
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich import print as rprint
import psutil
from datetime import datetime
import subprocess
from src import hardware_info
from src import network_info
from src import utils
from rich.live import Live
from rich.align import Align
from rich import box
import time
from rich.text import Text
from src import task_manager
from src import user_manager
from src import network_manager
import re
from src.utils import get_sudo_password

console = Console()

class SystemInfoViewer:
    def __init__(self):
        self.console = Console()
        self.sudo_password = None
        
    def ensure_sudo(self):
        """Ensure sudo access is available and get password if needed"""
        if self.sudo_password is None:
            self.console.print("[yellow]Some operations require administrative privileges.[/yellow]")
            self.sudo_password = get_sudo_password()
        return self.sudo_password is not None

    def run_sudo_command(self, cmd, input_data=None):
        """Run a command with sudo"""
        if not self.ensure_sudo():
            return False, None, "No sudo access"
        
        sudo_cmd = ['sudo', '-S'] + (cmd if isinstance(cmd, list) else cmd.split())
        process = subprocess.Popen(
            sudo_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        # Send password first, then any input data
        input_text = f"{self.sudo_password}\n"
        if input_data:
            input_text += input_data
        
        stdout, stderr = process.communicate(input_text.encode())
        return process.returncode == 0, stdout, stderr

    def display_menu(self):
        console.print(Panel.fit(
            "[bold blue]System Information Viewer[/bold blue]\n"
            "1. View All Information\n"
            "2. Hardware Information\n"
            "3. Network Information\n"
            "4. System Information\n"
            "5. Task Manager\n"
            "6. User Manager\n"
            "7. Network Manager\n"
            "8. Export Information\n"
            "9. Exit",
            title="Menu"
        ))
        
    def get_basic_system_info(self):
        table = Table(title="Basic System Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # Basic OS Information
        table.add_row("OS", platform.system())
        table.add_row("OS Version", platform.version())
        table.add_row("OS Release", platform.release())
        table.add_row("Machine", platform.machine())
        table.add_row("Processor", platform.processor())
        table.add_row("Hostname", platform.node())
        
        # Get Linux Distribution info if on Linux
        if platform.system() == "Linux":
            try:
                # Try different distribution info files
                if os.path.exists("/etc/os-release"):
                    with open("/etc/os-release") as f:
                        for line in f:
                            if line.startswith("PRETTY_NAME="):
                                distro = line.split("=")[1].strip().strip('"')
                                table.add_row("Distribution", distro)
                                break
                elif os.path.exists("/etc/lsb-release"):
                    with open("/etc/lsb-release") as f:
                        for line in f:
                            if line.startswith("DISTRIB_DESCRIPTION="):
                                distro = line.split("=")[1].strip().strip('"')
                                table.add_row("Distribution", distro)
                                break
            except:
                table.add_row("Distribution", "Unknown")
        
        return table

    def get_detailed_system_info(self):
        table = Table(title="Detailed System Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        # System uptime
        uptime = datetime.now() - datetime.fromtimestamp(psutil.boot_time())
        table.add_row("System Uptime", str(uptime).split('.')[0])
        table.add_row("Boot Time", datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S"))
        
        # Python Version
        table.add_row("Python Version", sys.version.split()[0])
        
        # User Information
        table.add_row("Current User", os.getlogin())
        table.add_row("Home Directory", os.path.expanduser("~"))
        
        # Process Information
        table.add_row("Total Processes", str(len(psutil.pids())))
        table.add_row("CPU Count", str(psutil.cpu_count()))
        
        return table

    def get_process_info(self):
        table = Table(title="Top Processes (by CPU Usage)")
        table.add_column("PID", style="cyan")
        table.add_column("Name", style="green")
        table.add_column("CPU %", style="yellow")
        table.add_column("Memory %", style="red")
        table.add_column("Status", style="blue")
        table.add_column("Created", style="magenta")
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 'status', 'create_time']):
            try:
                pinfo = proc.info
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
        
        # Sort by CPU usage and get top 10
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        for proc in processes[:10]:
            try:
                create_time = datetime.fromtimestamp(proc['create_time']).strftime("%Y-%m-%d %H:%M:%S")
                table.add_row(
                    str(proc['pid']),
                    proc['name'],
                    f"{proc['cpu_percent']:.1f}",
                    f"{proc['memory_percent']:.1f}",
                    proc['status'],
                    create_time
                )
            except:
                continue
        
        return table

    def get_distro_info(self):
        """Detect Linux distribution and package manager"""
        try:
            # Try reading os-release file first
            if os.path.exists("/etc/os-release"):
                with open("/etc/os-release") as f:
                    os_info = {}
                    for line in f:
                        if "=" in line:
                            key, value = line.rstrip().split("=", 1)
                            os_info[key] = value.strip('"')
                    
                    if "ID" in os_info:
                        distro_id = os_info["ID"].lower()
                        if distro_id in ["ubuntu", "debian", "linuxmint"]:
                            return "debian", "apt"
                        elif distro_id in ["fedora", "rhel", "centos"]:
                            return "redhat", "dnf"
                        elif distro_id in ["arch", "manjaro", "endeavouros", "garuda"]:
                            return "arch", "pacman"
                        elif distro_id in ["opensuse", "suse"]:
                            return "suse", "zypper"
            
            # Fallback to checking specific files
            if os.path.exists("/etc/debian_version"):
                return "debian", "apt"
            elif os.path.exists("/etc/fedora-release"):
                return "redhat", "dnf"
            elif os.path.exists("/etc/arch-release"):
                return "arch", "pacman"
            elif os.path.exists("/etc/SuSE-release"):
                return "suse", "zypper"
            
            return "unknown", None
        except:
            return "unknown", None

    def get_installed_packages(self):
        table = Table(title="Installed Package Managers and Updates")
        table.add_column("Package Manager", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Updates Available", style="yellow")
        
        if platform.system() == "Linux":
            distro_family, pkg_manager = self.get_distro_info()
            
            # Package manager commands based on distribution
            package_managers = {
                "apt": {
                    "updates": ["apt", "list", "--upgradable"],
                    "fallback": ["dpkg", "--get-selections"],
                    "needs_sudo": True,
                    "parse": lambda x: len([l for l in x.split('\n') if '/' in l])  # Count only package lines
                },
                "dnf": {
                    "updates": ["dnf", "check-update", "--quiet"],
                    "fallback": ["rpm", "-qa"],
                    "needs_sudo": True,
                    "parse": lambda x: len([l for l in x.split('\n') if l.strip()])
                },
                "pacman": {
                    "updates": ["pacman", "-Qu"],
                    "fallback": ["pacman", "-Q"],
                    "needs_sudo": False,
                    "parse": lambda x: len([l for l in x.split('\n') if l.strip()])
                },
                "zypper": {
                    "updates": ["zypper", "list-updates"],
                    "fallback": ["rpm", "-qa"],
                    "needs_sudo": True,
                    "parse": lambda x: len([l for l in x.split('\n') if l.strip() and not l.startswith('[')])
                }
            }
            
            if pkg_manager in package_managers:
                commands = package_managers[pkg_manager]
                try:
                    if commands.get("needs_sudo", False):
                        success, output, _ = self.run_sudo_command(commands["updates"])
                        if success:
                            updates = commands["parse"](output.decode())
                        else:
                            # Try fallback without counting updates
                            output = subprocess.check_output(
                                commands["fallback"],
                                stderr=subprocess.DEVNULL
                            )
                            packages = len(output.decode().strip().split('\n'))
                            table.add_row(pkg_manager, f"Installed ({packages} packages)", "Unknown (no sudo)")
                            return table
                    else:
                        output = subprocess.check_output(
                            commands["updates"],
                            stderr=subprocess.DEVNULL
                        )
                        updates = commands["parse"](output.decode())
                    
                    table.add_row(pkg_manager, "Installed", str(updates))
                except Exception as e:
                    # Try fallback command
                    try:
                        output = subprocess.check_output(
                            commands["fallback"],
                            stderr=subprocess.DEVNULL
                        )
                        packages = len(output.decode().strip().split('\n'))
                        table.add_row(pkg_manager, f"Installed ({packages} packages)", "Unknown")
                    except:
                        table.add_row(pkg_manager, "Installed", "Error checking updates")
            else:
                table.add_row("Package Manager", f"Unknown distribution: {distro_family}", "N/A")
        
        elif platform.system() == "Windows":
            try:
                # Check for Windows Update using PowerShell
                ps_cmd = "Get-WmiObject -Class Win32_QuickFixEngineering | Measure-Object | Select-Object -ExpandProperty Count"
                updates = subprocess.check_output(["powershell", "-Command", ps_cmd], text=True).strip()
                table.add_row("Windows Update", "Installed", updates)
                
                # Check for Windows Package Manager (winget)
                try:
                    subprocess.run(["winget", "--version"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                    updates = subprocess.check_output(["winget", "upgrade", "--count"], text=True).strip()
                    table.add_row("Windows Package Manager", "Installed", updates)
                except:
                    pass
            except:
                table.add_row("Windows Update", "Unable to check", "N/A")
        
        elif platform.system() == "Darwin":  # macOS
            try:
                # Check for Homebrew
                brew_check = subprocess.run(["which", "brew"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if brew_check.returncode == 0:
                    updates = subprocess.check_output(["brew", "outdated", "--quiet"], text=True).count('\n')
                    table.add_row("Homebrew", "Installed", str(updates))
                
                # Check for Mac App Store updates
                mas_check = subprocess.run(["which", "mas"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                if mas_check.returncode == 0:
                    updates = subprocess.check_output(["mas", "outdated"], text=True).count('\n')
                    table.add_row("Mac App Store", "Installed", str(updates))
            except:
                table.add_row("Package Manager", "Unable to check", "N/A")
        
        return table

    def get_security_info(self):
        table = Table(title="Security Information")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")
        
        if platform.system() == "Linux":
            try:
                # Check SELinux status
                if os.path.exists("/etc/selinux/config"):
                    with open("/etc/selinux/config") as f:
                        for line in f:
                            if line.startswith("SELINUX="):
                                table.add_row("SELinux Status", line.split("=")[1].strip())
                
                # Get distro info to determine default firewall
                distro_family, _ = self.get_distro_info()
                
                # Define firewall checks based on distribution
                firewall_checks = []
                
                # Check for installed firewalls silently first
                if os.path.exists("/usr/sbin/ufw") or os.path.exists("/sbin/ufw"):
                    firewall_checks.append(("UFW", ["ufw", "status"], "inactive"))
                if os.path.exists("/usr/sbin/firewalld") or os.path.exists("/sbin/firewalld"):
                    firewall_checks.append(("FirewallD", ["firewall-cmd", "--state"], "not running"))
                
                # Always check iptables last as a fallback
                if os.path.exists("/usr/sbin/iptables") or os.path.exists("/sbin/iptables"):
                    firewall_checks.append(("IPTables", ["iptables", "-L", "-n"], "no rules"))
                
                # If no firewalls detected, check distribution default
                if not firewall_checks:
                    if distro_family == "debian":
                        table.add_row("Firewall", "UFW not installed")
                    elif distro_family == "redhat":
                        table.add_row("Firewall", "FirewallD not installed")
                    elif distro_family == "arch":
                        table.add_row("Firewall", "No firewall configured")
                    else:
                        table.add_row("Firewall", "No firewall detected")
                    return table
                
                # Get sudo access once for all firewall checks
                if not self.ensure_sudo():
                    table.add_row("Firewall Status", "Cannot check (no sudo access)")
                    return table
                
                firewall_found = False
                for name, cmd, default in firewall_checks:
                    try:
                        success, output, _ = self.run_sudo_command(cmd)
                        if success:
                            if name == "UFW":
                                status = "active" if "Status: active" in output.decode() else "inactive"
                            elif name == "FirewallD":
                                status = "running" if "running" in output.decode() else "not running"
                            elif name == "IPTables":
                                # Parse iptables output to determine if any rules exist
                                iptables_output = output.decode().strip()
                                if iptables_output and "Chain" in iptables_output:
                                    status = "active with rules"
                                else:
                                    status = "active (no rules)"
                            else:
                                status = "active" if output else default
                            
                            table.add_row(f"{name} Status", status)
                            firewall_found = True
                    except Exception as e:
                        continue
                
                if not firewall_found:
                    table.add_row("Firewall Status", "No active firewall detected")
            
            except Exception as e:
                table.add_row("Security Info", "Unable to fetch security information")
        
        elif platform.system() == "Windows":
            try:
                # Check Windows Defender status using PowerShell
                ps_cmd = "Get-MpComputerStatus | Select-Object -ExpandProperty RealTimeProtectionEnabled"
                defender_status = subprocess.check_output(["powershell", "-Command", ps_cmd], text=True).strip()
                table.add_row("Windows Defender", "Enabled" if defender_status.lower() == "true" else "Disabled")
                
                # Check Windows Firewall status
                ps_cmd = "Get-NetFirewallProfile | Select-Object -ExpandProperty Enabled"
                firewall_status = subprocess.check_output(["powershell", "-Command", ps_cmd], text=True).strip()
                table.add_row("Windows Firewall", "Enabled" if "True" in firewall_status else "Disabled")
            except:
                table.add_row("Security Info", "Unable to fetch Windows security information")
        
        elif platform.system() == "Darwin":  # macOS
            try:
                # Check macOS Firewall status
                cmd = ["defaults", "read", "/Library/Preferences/com.apple.alf", "globalstate"]
                firewall_status = subprocess.check_output(cmd, text=True).strip()
                table.add_row("Firewall", "Enabled" if firewall_status != "0" else "Disabled")
                
                # Check System Integrity Protection (SIP)
                cmd = ["csrutil", "status"]
                sip_status = subprocess.check_output(cmd, text=True).strip()
                table.add_row("System Integrity Protection", "Enabled" if "enabled" in sip_status.lower() else "Disabled")
            except:
                table.add_row("Security Info", "Unable to fetch macOS security information")
        
        return table

    def show_startup_banner(self):
        console = Console()
        
        # Clear the screen
        console.clear()
        
        # Create the banner text with capital letters
        banner = """
              _     ___   _    
             / \\  |__ \\/ \\   
            / _ \\   ) |/ _ \\  
    ______ / ___ \\ / // ___ \\ 
   |_____ /_/   \\/_//_/   \\_\\
        SYSTEM INFO VIEWER
        """
        
        company = """
         ____  _____    _    ____  _     _  __   _____ _____ ____ _   _ 
        |  _ \\| ____|  / \\  |  _ \\| |   | |/ /  |_   _| ____/ ___| | | |
        | |_) |  _|   / _ \\ | |_) | |   | ' /     | | |  _|| |   | |_| |
        |  __/| |___ / ___ \\|  _ <| |___| . \\     | | | |__| |___|  _  |
        |_|   |_____/_/   \\_\\_| \\_\\_____|_|\\_\\    |_| |_____|\\____|_| |_|
        """
        
        # Animation frames for loading
        frames = ["⠋", "⠙", "⠹", "⠸", "⠼", "⠴", "⠦", "⠧", "⠇", "⠏"]
        
        # Colors for animation
        colors = ["red", "yellow", "green", "blue", "magenta", "cyan","white",]
        company_colors = ["bright_red", "bright_yellow", "bright_magenta"]
        
        with Live(refresh_per_second=7) as live:
            for i in range(60):  # Show animation for 6 seconds
                color = colors[i % len(colors)]
                company_color = company_colors[i % len(company_colors)]
                frame = frames[i % len(frames)]
                
                # Create styled text with gradient effect for company name
                styled_banner = Text(banner, style=f"bold {color}")
                styled_company = Text()
                
                # Add gradient effect to company name
                lines = company.split('\n')
                for line in lines:
                    styled_company.append(line + '\n', style=f"bold {company_color}")
                
                # Create loading text
                loading_text = Text(f"\n{frame} LOADING SYSTEM INFORMATION...", style=f"bold {color}")
                
                # Combine all elements
                all_text = Text.assemble(
                    styled_banner, "\n",
                    styled_company, "\n",
                    loading_text
                )
                
                # Center everything with a glowing effect
                panel = Panel(
                    Align.center(all_text),
                    box=box.DOUBLE,
                    border_style=color,
                    padding=(1, 2),
                    title=" _A2A ",
                    title_align="center",
                    subtitle="[ PearlK Tech ]",
                    subtitle_align="center"
                )
                
                live.update(panel)
                time.sleep(0.3)
        
        # Clear screen after animation
        console.clear()

    def run(self):
        self.show_startup_banner()
        
        while True:
            self.display_menu()
            choice = input("Enter your choice (1-9): ")
            
            if choice == "1":
                self.show_all_info()
            elif choice == "2":
                self.show_hardware_info()
            elif choice == "3":
                self.show_network_info()
            elif choice == "4":
                self.show_system_info()
            elif choice == "5":
                task_manager.run_task_manager()
            elif choice == "6":
                if os.geteuid() == 0:
                    user_manager.run_user_manager()
                else:
                    password = utils.get_sudo_password()
                    if password:
                        user_manager.run_user_manager()
                    else:
                        console.print("[red]User management requires root privileges![/red]")
            elif choice == "7":
                if os.geteuid() == 0:
                    network_manager.run_network_manager()
                else:
                    password = utils.get_sudo_password()
                    if password:
                        network_manager.run_network_manager()
                    else:
                        console.print("[red]Network management requires root privileges![/red]")
            elif choice == "8":
                self.export_info()
            elif choice == "9":
                console.print("[yellow]Thank you for using _a2a![/yellow]")
                break
            else:
                console.print("[red]Invalid choice. Please try again.[/red]")
            
            input("\nPress Enter to continue...")

    def show_all_info(self):
        console.print("\n[bold blue]System Information[/bold blue]")
        console.print(self.get_basic_system_info())
        console.print(self.get_detailed_system_info())
        console.print(self.get_process_info())
        console.print(self.get_installed_packages())
        console.print(self.get_security_info())
        
        console.print("\n[bold blue]Hardware Information[/bold blue]")
        self.show_hardware_info()
        
        console.print("\n[bold blue]Network Information[/bold blue]")
        self.show_network_info()

    def show_loading_message(self, message):
        with console.status(f"[bold blue]{message}...", spinner="dots"):
            time.sleep(0.5)  # Give user time to see the message

    def show_hardware_info(self):
        self.show_loading_message("Fetching CPU information")
        console.print(hardware_info.get_cpu_info())
        
        self.show_loading_message("Fetching memory information")
        console.print(hardware_info.get_memory_info())
        
        self.show_loading_message("Fetching GPU information")
        console.print(hardware_info.get_gpu_info())
        
        self.show_loading_message("Analyzing disk drives")
        console.print(hardware_info.get_disk_info())
        
        self.show_loading_message("Fetching motherboard information")
        console.print(hardware_info.get_motherboard_info())
        
        self.show_loading_message("Scanning USB devices")
        console.print(hardware_info.get_usb_devices())
        
        self.show_loading_message("Scanning PCI devices")
        console.print(hardware_info.get_pci_devices())
        
        self.show_loading_message("Detecting sound devices")
        console.print(hardware_info.get_sound_devices())

    def show_network_info(self):
        self.show_loading_message("Analyzing network interfaces")
        console.print(network_info.get_network_interfaces())
        
        self.show_loading_message("Testing network speed")
        console.print(network_info.get_network_speed())
        
        self.show_loading_message("Fetching public IP information")
        console.print(network_info.get_public_ip())
        
        self.show_loading_message("Scanning WiFi networks")
        console.print(network_info.get_wifi_info())
        
        self.show_loading_message("Collecting network statistics")
        console.print(network_info.get_network_statistics())
        
        self.show_loading_message("Fetching DNS information")
        console.print(network_info.get_dns_info())
        
        self.show_loading_message("Reading routing table")
        console.print(network_info.get_route_table())
        
        self.show_loading_message("Analyzing active connections")
        console.print(network_info.get_active_connections())

    def show_system_info(self):
        self.show_loading_message("Fetching basic system information")
        console.print(self.get_basic_system_info())
        
        self.show_loading_message("Collecting detailed system information")
        console.print(self.get_detailed_system_info())
        
        self.show_loading_message("Analyzing running processes")
        console.print(self.get_process_info())
        
        self.show_loading_message("Checking installed packages")
        console.print(self.get_installed_packages())
        
        self.show_loading_message("Verifying security settings")
        console.print(self.get_security_info())

    def _format_info_to_html_table(self, title, info):
        """Convert any information into a proper HTML table"""
        html = f'<h3 class="subsection-header">{title}</h3>\n'
        html += '<div class="table-responsive">\n<table class="info-table">\n'
        
        # If it's a Rich Table object
        if hasattr(info, 'row_count'):
            # Create a temporary console to capture the table output
            temp_console = Console(record=True, force_terminal=False)
            with temp_console.capture() as capture:
                temp_console.print(info)
            table_str = capture.get()
            return self._convert_text_table_to_html(table_str)
        
        # If it's a string with key-value pairs
        elif isinstance(info, str) and ':' in info:
            html += '<thead>\n<tr>\n<th>Property</th>\n<th>Value</th>\n</tr>\n</thead>\n<tbody>\n'
            for line in info.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    html += f'<tr>\n<td>{key.strip()}</td>\n<td>{value.strip()}</td>\n</tr>\n'
            html += '</tbody>\n'
        
        # If it's a dictionary
        elif isinstance(info, dict):
            html += '<thead>\n<tr>\n<th>Property</th>\n<th>Value</th>\n</tr>\n</thead>\n<tbody>\n'
            for key, value in info.items():
                html += f'<tr>\n<td>{key}</td>\n<td>{value}</td>\n</tr>\n'
            html += '</tbody>\n'
        
        # If it's a list
        elif isinstance(info, list):
            html += '<thead>\n<tr>\n<th>Item</th>\n</tr>\n</thead>\n<tbody>\n'
            for item in info:
                html += f'<tr>\n<td>{item}</td>\n</tr>\n'
            html += '</tbody>\n'
        
        # For any other type
        else:
            html += '<tbody>\n<tr>\n<td>' + str(info).replace('\n', '<br>') + '</td>\n</tr>\n</tbody>\n'
        
        html += '</table>\n</div>\n'
        return html

    def export_info(self):
        try:
            # Ask for export format
            format_choice = input("Export format (txt/html): ").lower()
            if format_choice not in ['txt', 'html']:
                console.print("[red]Invalid format. Using txt as default.[/red]")
                format_choice = 'txt'
            
            # Collect all available categories
            categories = {
                '1': ('System Information', [
                    ("Basic System Information", self.get_basic_system_info),
                    ("Detailed System Information", self.get_detailed_system_info),
                    ("Running Processes", self.get_process_info),
                    ("Installed Packages", self.get_installed_packages),
                    ("Security Settings", self.get_security_info)
                ]),
                '2': ('Hardware Information', [
                    ("CPU Information", hardware_info.get_cpu_info),
                    ("Memory Information", hardware_info.get_memory_info),
                    ("GPU Information", hardware_info.get_gpu_info),
                    ("Disk Information", hardware_info.get_disk_info),
                    ("Motherboard Information", hardware_info.get_motherboard_info),
                    ("USB Devices", hardware_info.get_usb_devices),
                    ("PCI Devices", hardware_info.get_pci_devices),
                    ("Sound Devices", hardware_info.get_sound_devices)
                ]),
                '3': ('Network Information', [
                    ("Network Interfaces", network_info.get_network_interfaces),
                    ("Network Speed", network_info.get_network_speed),
                    ("Public IP Information", network_info.get_public_ip),
                    ("WiFi Information", network_info.get_wifi_info),
                    ("Network Statistics", network_info.get_network_statistics),
                    ("DNS Information", network_info.get_dns_info),
                    ("Routing Table", network_info.get_route_table),
                    ("Active Connections", network_info.get_active_connections)
                ])
            }
            
            # Ask user which categories to export
            console.print("\nAvailable categories:")
            for key, (name, _) in categories.items():
                console.print(f"{key}. {name}")
            console.print("4. All Categories")
            
            choice = input("\nEnter category numbers to export (comma-separated, e.g., 1,2): ")
            selected_categories = []
            
            if choice == '4':
                selected_categories = list(categories.values())
            else:
                for num in choice.split(','):
                    num = num.strip()
                    if num in categories:
                        selected_categories.append(categories[num])
                    else:
                        console.print(f"[yellow]Warning: Invalid category number '{num}' ignored[/yellow]")
            
            if not selected_categories:
                console.print("[red]No valid categories selected. Exporting all categories.[/red]")
                selected_categories = list(categories.values())
            
            # Get metadata
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            username = os.getlogin()
            hostname = platform.node()
            
            if format_choice == 'txt':
                # Text format
                content = "System Information Report\n"
                content += f"Generated on: {timestamp}\n"
                content += f"Generated by: {username}\n"
                content += f"Hostname: {hostname}\n"
                content += "="*50 + "\n\n"
                
                # Add selected categories
                for category_name, items in selected_categories:
                    content += f"\n{category_name}\n"
                    content += "="*len(category_name) + "\n\n"
                    
                    for title, func in items:
                        self.show_loading_message(f"Formatting {title}")
                        info = func()
                        if info:
                            content += f"{title}\n"
                            content += "-"*len(title) + "\n"
                            content += str(info) + "\n\n"
                
                content += "\nGenerated by _a2a (Linux System Info Tool) | © PearlK Tech"
                
            else:
                # HTML format
                # ... (previous HTML header code) ...
                
                # Add selected categories
                content = ""
                for category_name, items in selected_categories:
                    section_id = category_name.lower().replace(' ', '-')
                    content += f'<div class="section" id="{section_id}">\n'
                    content += f'<h2 class="section-header">{category_name}</h2>\n'
                    content += '<div class="section-content">\n'
                    
                    for title, func in items:
                        self.show_loading_message(f"Formatting {title}")
                        info = func()
                        if info:
                            content += self._format_info_to_html_table(title, info)
                    
                    content += '</div>\n</div>\n'
            
            # Export the data
            utils.export_to_file(content, format_choice)
            
        except Exception as e:
            console.print(f"[red]Error during export: {str(e)}[/red]")
            import traceback
            console.print(traceback.format_exc())

    def _convert_text_table_to_html(self, text_table):
        """Convert text-based table to HTML table with proper formatting"""
        if not text_table:
            return ""
        
        def clean_cell(cell):
            """Clean cell content and handle special characters"""
            cell = cell.strip()
            cell = cell.replace('│', '').replace('┃', '')
            cell = cell.replace('└', '').replace('┘', '')
            cell = cell.replace('┌', '').replace('┐', '')
            cell = cell.replace('├', '').replace('┤', '')
            cell = cell.replace('┬', '').replace('┴', '')
            cell = cell.replace('─', '').replace('━', '')
            return cell.strip()
        
        def split_header(header_text):
            """Split header text into columns based on multiple spaces"""
            # Split by 2 or more spaces
            headers = [h.strip() for h in re.split(r'\s{2,}', header_text) if h.strip()]
            return headers
        
        # If it's a table format (contains box-drawing characters)
        if '│' in text_table or '┃' in text_table or '\t' in text_table:
            lines = [line for line in text_table.split('\n') if line.strip()]
            
            # Get table title from the first line if it exists
            title = lines[0] if lines else ""
            if title and not ('│' in title or '┃' in title or '\t' in title):
                lines = lines[1:]  # Remove title from lines as we'll handle it separately
            else:
                title = None
            
            html = '<div class="table-responsive">\n'
            html += '<table class="info-table">\n'
            
            # Add title row if exists
            if title:
                html += '<thead>\n'
                html += f'<tr>\n<th colspan="100%" class="table-title">{title.strip()}</th>\n</tr>\n'
            
            # Handle header and data
            if lines:
                # Find the header line
                header_line = None
                data_lines = []
                for line in lines:
                    if '━' in line or '─' in line:
                        continue
                    if header_line is None:
                        header_line = line
                    else:
                        data_lines.append(line)
                
                # Extract and add headers
                if header_line:
                    # Split header into columns
                    if '│' in header_line:
                        headers = [clean_cell(h) for h in header_line.split('│') if clean_cell(h)]
                        # For each header, split by multiple spaces if it contains them
                        final_headers = []
                        for header in headers:
                            if re.search(r'\s{2,}', header):
                                final_headers.extend(split_header(header))
                            else:
                                final_headers.append(header)
                        headers = final_headers
                    else:
                        headers = split_header(clean_cell(header_line))
                    
                    if not title:
                        html += '<thead>\n'
                    html += '<tr>\n'
                    for header in headers:
                        html += f'<th>{header}</th>\n'
                    html += '</tr>\n</thead>\n'
                
                # Add data rows
                html += '<tbody>\n'
                for line in data_lines:
                    if not any(c in line for c in '│┃'):
                        continue
                    cells = [clean_cell(c) for c in line.split('│') if clean_cell(c)]
                    if cells:
                        html += '<tr>\n'
                        # Split each cell if it contains multiple spaces
                        for cell in cells:
                            if re.search(r'\s{2,}', cell):
                                subcells = split_header(cell)
                                for subcell in subcells:
                                    html += f'<td>{subcell}</td>\n'
                            else:
                                html += f'<td>{cell}</td>\n'
                        html += '</tr>\n'
                html += '</tbody>\n'
            
            html += '</table>\n</div>\n'
            return html

def main():
    viewer = SystemInfoViewer()
    viewer.run()

if __name__ == "__main__":
    main() 