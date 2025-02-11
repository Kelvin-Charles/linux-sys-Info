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