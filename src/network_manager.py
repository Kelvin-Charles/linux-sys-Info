import subprocess
import netifaces
import socket
from rich.console import Console
from rich.table import Table
from rich import box
from src.utils import get_sudo_password
import re
import os
import time

console = Console()

class NetworkManager:
    def __init__(self):
        self.console = Console()
        self.sudo_password = None

    def ensure_sudo(self):
        if not self.sudo_password:
            self.sudo_password = get_sudo_password()
        return self.sudo_password is not None

    def run_sudo_command(self, cmd, input_data=None):
        if not self.ensure_sudo():
            return False
        
        sudo_cmd = ['sudo', '-S'] + cmd
        process = subprocess.Popen(
            sudo_cmd,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        input_text = self.sudo_password + '\n'
        if input_data:
            input_text += input_data
        
        stdout, stderr = process.communicate(input_text.encode())
        return process.returncode == 0, stdout, stderr

    def list_interfaces(self):
        table = Table(
            title="Network Interfaces",
            box=box.DOUBLE,
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("Interface", style="green")
        table.add_column("Status", style="yellow")
        table.add_column("IP Address", style="cyan")
        table.add_column("MAC Address", style="magenta")
        table.add_column("Type", style="blue")
        
        try:
            interfaces = netifaces.interfaces()
            for iface in interfaces:
                # Get IP address
                try:
                    addrs = netifaces.ifaddresses(iface)
                    ip = addrs.get(netifaces.AF_INET, [{'addr': 'Not assigned'}])[0]['addr']
                    mac = addrs.get(netifaces.AF_LINK, [{'addr': 'Unknown'}])[0]['addr']
                except:
                    ip = "Not assigned"
                    mac = "Unknown"
                
                # Get interface status
                try:
                    status = "Up" if os.path.exists(f"/sys/class/net/{iface}/carrier") else "Down"
                except:
                    status = "Unknown"
                
                # Determine interface type
                if iface.startswith('wl'):
                    type_ = "Wireless"
                elif iface.startswith('en') or iface.startswith('eth'):
                    type_ = "Ethernet"
                elif iface == 'lo':
                    type_ = "Loopback"
                else:
                    type_ = "Other"
                
                table.add_row(iface, status, ip, mac, type_)
        
        except Exception as e:
            console.print(f"[red]Error listing interfaces: {str(e)}[/red]")
        
        return table

    def configure_interface(self, interface):
        try:
            console.print(f"\n[bold cyan]Configure {interface}:[/bold cyan]")
            console.print("[1] Set Static IP")
            console.print("[2] Enable DHCP")
            console.print("[3] Enable/Disable Interface")
            console.print("[4] Set DNS Servers")
            console.print("[0] Back")
            
            choice = input("\nEnter your choice (0-4): ")
            
            if choice == "1":
                ip = input("Enter IP address (e.g., 192.168.1.100): ")
                netmask = input("Enter netmask (e.g., 255.255.255.0): ")
                gateway = input("Enter gateway (e.g., 192.168.1.1): ")
                
                cmd = ['ip', 'addr', 'add', f"{ip}/{self._netmask_to_cidr(netmask)}", 'dev', interface]
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    cmd = ['ip', 'route', 'add', 'default', 'via', gateway]
                    success, _, stderr = self.run_sudo_command(cmd)
                    if success:
                        console.print(f"[green]Successfully configured static IP for {interface}[/green]")
                    else:
                        console.print(f"[red]Error setting gateway: {stderr.decode()}[/red]")
                else:
                    console.print(f"[red]Error setting IP: {stderr.decode()}[/red]")
            
            elif choice == "2":
                cmd = ['dhclient', '-r', interface]
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    cmd = ['dhclient', interface]
                    success, _, stderr = self.run_sudo_command(cmd)
                    if success:
                        console.print(f"[green]Successfully enabled DHCP on {interface}[/green]")
                    else:
                        console.print(f"[red]Error enabling DHCP: {stderr.decode()}[/red]")
            
            elif choice == "3":
                status = input("Enter status (up/down): ").lower()
                if status in ['up', 'down']:
                    cmd = ['ip', 'link', 'set', interface, status]
                    success, _, stderr = self.run_sudo_command(cmd)
                    if success:
                        console.print(f"[green]Successfully set {interface} {status}[/green]")
                    else:
                        console.print(f"[red]Error setting interface status: {stderr.decode()}[/red]")
                else:
                    console.print("[red]Invalid status. Use 'up' or 'down'[/red]")
            
            elif choice == "4":
                dns_servers = input("Enter DNS servers (comma-separated, e.g., 8.8.8.8,8.8.4.4): ")
                nameservers = [f"nameserver {server.strip()}" for server in dns_servers.split(',')]
                resolv_conf = '\n'.join(nameservers) + '\n'
                
                cmd = ['tee', '/etc/resolv.conf']
                success, _, stderr = self.run_sudo_command(cmd, resolv_conf)
                if success:
                    console.print("[green]Successfully updated DNS servers[/green]")
                else:
                    console.print(f"[red]Error updating DNS servers: {stderr.decode()}[/red]")

        except Exception as e:
            console.print(f"[red]Error configuring interface: {str(e)}[/red]")

    def configure_wifi(self):
        try:
            if not self.ensure_sudo():
                return
            
            console.print("\n[bold cyan]WiFi Configuration:[/bold cyan]")
            console.print("[1] Scan Networks")
            console.print("[2] Connect to Network")
            console.print("[3] Disconnect from Network")
            console.print("[4] Show Saved Networks")
            console.print("[5] Show Current Connection")
            console.print("[0] Back")
            
            choice = input("\nEnter your choice (0-5): ")
            
            if choice == "1":
                cmd = ['nmcli', 'device', 'wifi', 'list', '--rescan', 'yes']
                success, stdout, _ = self.run_sudo_command(cmd)
                if success:
                    console.print(stdout.decode())
                else:
                    console.print("[red]Error scanning WiFi networks[/red]")
            
            elif choice == "2":
                ssid = input("Enter network name (SSID): ")
                password = input("Enter password (leave blank for open networks): ")
                
                cmd = ['nmcli', 'device', 'wifi', 'connect', ssid]
                if password:
                    cmd.extend(['password', password])
                
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully connected to {ssid}[/green]")
                else:
                    console.print(f"[red]Error connecting to network: {stderr.decode()}[/red]")
            
            elif choice == "3":
                cmd = ['nmcli', 'device', 'disconnect', 'wlan0']
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print("[green]Successfully disconnected from WiFi[/green]")
                else:
                    console.print(f"[red]Error disconnecting: {stderr.decode()}[/red]")
            
            elif choice == "4":
                cmd = ['nmcli', 'connection', 'show']
                success, stdout, _ = self.run_sudo_command(cmd)
                if success:
                    console.print(stdout.decode())
                else:
                    console.print("[red]Error showing saved networks[/red]")
            
            elif choice == "5":
                cmd = ['nmcli', 'device', 'wifi', 'show-password']
                success, stdout, _ = self.run_sudo_command(cmd)
                if success:
                    console.print(stdout.decode())
                else:
                    console.print("[red]Error showing current connection[/red]")

        except Exception as e:
            console.print(f"[red]Error configuring WiFi: {str(e)}[/red]")

    def _netmask_to_cidr(self, netmask):
        return sum([bin(int(x)).count('1') for x in netmask.split('.')])

def run_network_manager():
    network_manager = NetworkManager()
    
    while True:
        console.clear()
        console.print("\n[bold cyan]Network Management[/bold cyan]")
        console.print(network_manager.list_interfaces())
        
        console.print("\n[bold cyan]Options:[/bold cyan]")
        console.print("[1] Configure Interface")
        console.print("[2] Configure WiFi")
        console.print("[3] Show Network Status")
        console.print("[4] Test Connection")
        console.print("[0] Exit")
        
        choice = input("\nEnter your choice (0-4): ")
        
        if choice == "0":
            break
        elif choice == "1":
            interfaces = netifaces.interfaces()
            console.print("\nAvailable interfaces:")
            for i, iface in enumerate(interfaces, 1):
                console.print(f"[{i}] {iface}")
            
            try:
                idx = int(input("\nSelect interface number: ")) - 1
                if 0 <= idx < len(interfaces):
                    network_manager.configure_interface(interfaces[idx])
                else:
                    console.print("[red]Invalid interface number[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number[/red]")
        
        elif choice == "2":
            network_manager.configure_wifi()
        
        elif choice == "3":
            cmd = ['nmcli', 'device', 'status']
            success, stdout, _ = network_manager.run_sudo_command(cmd)
            if success:
                console.print(stdout.decode())
        
        elif choice == "4":
            host = input("Enter host to test (default: 8.8.8.8): ") or "8.8.8.8"
            try:
                console.print(f"\nPinging {host}...")
                cmd = ['ping', '-c', '4', host]
                success, stdout, _ = network_manager.run_sudo_command(cmd)
                if success:
                    console.print(stdout.decode())
                else:
                    console.print("[red]Connection test failed[/red]")
            except Exception as e:
                console.print(f"[red]Error testing connection: {str(e)}[/red]")
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    if os.geteuid() != 0:
        console.print("[red]This script must be run as root![/red]")
        exit(1)
    run_network_manager() 