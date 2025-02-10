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

console = Console()

class SystemInfoViewer:
    def __init__(self):
        self.console = Console()
        
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

    def get_installed_packages(self):
        table = Table(title="Installed Package Managers and Updates")
        table.add_column("Package Manager", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Updates Available", style="yellow")
        
        # Check for different package managers
        package_managers = {
            "apt": "apt list --upgradable 2>/dev/null | wc -l",
            "dnf": "dnf check-update --quiet | wc -l",
            "pacman": "pacman -Qu | wc -l",
            "zypper": "zypper list-updates | wc -l",
            "yum": "yum check-update --quiet | wc -l"
        }
        
        for pm, cmd in package_managers.items():
            try:
                if platform.system() == "Linux":
                    # Check if package manager exists
                    if subprocess.call(["which", pm], stdout=subprocess.DEVNULL) == 0:
                        updates = subprocess.check_output(cmd, shell=True).decode().strip()
                        table.add_row(pm, "Installed", updates)
                    else:
                        table.add_row(pm, "Not Installed", "N/A")
            except:
                continue
        
        # Check for Windows Update (if on Windows)
        if platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                updates = c.Win32_QuickFixEngineering()
                table.add_row("Windows Update", "Installed", str(len(updates)))
            except:
                table.add_row("Windows Update", "Unable to check", "N/A")
        
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
                
                # Check firewall status
                firewall_cmds = [
                    ("ufw", "ufw status"),
                    ("firewalld", "firewall-cmd --state"),
                    ("iptables", "iptables -L")
                ]
                
                for fw, cmd in firewall_cmds:
                    try:
                        if subprocess.call(["which", fw], stdout=subprocess.DEVNULL) == 0:
                            status = subprocess.check_output(cmd.split()).decode().strip()
                            table.add_row(f"{fw} Status", status)
                    except:
                        continue
            except:
                table.add_row("Security Info", "Unable to fetch")
        
        elif platform.system() == "Windows":
            try:
                import wmi
                c = wmi.WMI()
                
                # Check Windows Defender status
                defender = c.Win32_Service(Name="WinDefend")[0]
                table.add_row("Windows Defender", defender.State)
                
                # Check Windows Firewall status
                firewall = c.Win32_Service(Name="MpsSvc")[0]
                table.add_row("Windows Firewall", firewall.State)
            except:
                table.add_row("Security Info", "Unable to fetch")
        
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

    def export_info(self):
        format_choice = input("Export format (txt/html): ").lower()
        if format_choice not in ['txt', 'html']:
            console.print("[red]Invalid format. Using txt as default.[/red]")
            format_choice = 'txt'
        
        # Capture all information in a string
        console = Console(record=True)
        self.show_all_info()
        export_str = console.export_text() if format_choice == 'txt' else console.export_html()
        
        utils.export_to_file(export_str, format_choice)

def main():
    viewer = SystemInfoViewer()
    viewer.run()

if __name__ == "__main__":
    main() 