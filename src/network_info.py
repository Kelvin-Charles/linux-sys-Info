import psutil
import socket
import requests
import speedtest
from rich.table import Table
import subprocess
import platform
import netifaces
from rich.console import Console

console = Console()

def get_network_interfaces():
    table = Table(title="Network Interfaces")
    table.add_column("Interface", style="cyan")
    table.add_column("IP Address", style="green")
    table.add_column("MAC Address", style="blue")
    table.add_column("Netmask", style="yellow")
    table.add_column("Gateway", style="magenta")
    table.add_column("Status", style="red")
    table.add_column("Speed", style="green")
    table.add_column("Bytes Sent", style="yellow")
    table.add_column("Bytes Received", style="yellow")
    
    net_io = psutil.net_io_counters(pernic=True)
    addrs = psutil.net_if_addrs()
    stats = psutil.net_if_stats()
    
    for interface, addresses in addrs.items():
        ip_addr = "N/A"
        mac_addr = "N/A"
        netmask = "N/A"
        gateway = "N/A"
        
        # Get interface information
        for addr in addresses:
            if addr.family == socket.AF_INET:
                ip_addr = addr.address
                netmask = addr.netmask
            elif addr.family == psutil.AF_LINK:
                mac_addr = addr.address
        
        # Get gateway
        try:
            gws = netifaces.gateways()
            default_gw = gws.get('default', {}).get(netifaces.AF_INET, [None])[0]
            if default_gw:
                gateway = default_gw
        except:
            pass
        
        # Get interface statistics
        if interface in stats:
            status = "Up" if stats[interface].isup else "Down"
            speed = f"{stats[interface].speed} Mb/s" if stats[interface].speed > 0 else "N/A"
        else:
            status = "Unknown"
            speed = "N/A"
        
        # Get I/O statistics
        if interface in net_io:
            io_stats = net_io[interface]
            bytes_sent = f"{io_stats.bytes_sent / (1024**2):.2f} MB"
            bytes_recv = f"{io_stats.bytes_recv / (1024**2):.2f} MB"
        else:
            bytes_sent = "N/A"
            bytes_recv = "N/A"
        
        table.add_row(
            interface,
            ip_addr,
            mac_addr,
            netmask,
            gateway,
            status,
            speed,
            bytes_sent,
            bytes_recv
        )
    
    return table

def get_network_speed():
    table = Table(title="Network Speed Test")
    table.add_column("Test", style="cyan")
    table.add_column("Value", style="green")
    
    try:
        console.print("[yellow]Starting speed test (this may take 15-20 seconds)...[/yellow]")
        st = speedtest.Speedtest()
        
        with console.status("[bold blue]Testing download speed...") as status:
            download_speed = st.download() / 1_000_000  # Convert to Mbps
        
        with console.status("[bold blue]Testing upload speed...") as status:
            upload_speed = st.upload() / 1_000_000  # Convert to Mbps
        
        with console.status("[bold blue]Finding best server...") as status:
            ping = st.results.ping
        
        table.add_row("Download Speed", f"{download_speed:.2f} Mbps")
        table.add_row("Upload Speed", f"{upload_speed:.2f} Mbps")
        table.add_row("Ping", f"{ping:.2f} ms")
    except Exception as e:
        table.add_row("Error", f"Unable to perform speed test: {str(e)}")
    
    return table

def get_public_ip():
    table = Table(title="Public IP Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    try:
        response = requests.get('https://ipapi.co/json/')
        data = response.json()
        
        table.add_row("Public IP", data.get('ip', 'N/A'))
        table.add_row("City", data.get('city', 'N/A'))
        table.add_row("Region", data.get('region', 'N/A'))
        table.add_row("Country", data.get('country_name', 'N/A'))
        table.add_row("ISP", data.get('org', 'N/A'))
        table.add_row("Latitude", str(data.get('latitude', 'N/A')))
        table.add_row("Longitude", str(data.get('longitude', 'N/A')))
        table.add_row("Timezone", data.get('timezone', 'N/A'))
    except:
        table.add_row("Public IP Info", "Unable to fetch")
    
    return table

def get_active_connections():
    table = Table(title="Active Network Connections")
    table.add_column("Local Address", style="cyan")
    table.add_column("Local Port", style="green")
    table.add_column("Remote Address", style="blue")
    table.add_column("Remote Port", style="yellow")
    table.add_column("Status", style="magenta")
    table.add_column("PID", style="red")
    
    for conn in psutil.net_connections():
        try:
            if conn.status == 'ESTABLISHED':
                local_addr = f"{conn.laddr.ip}"
                local_port = str(conn.laddr.port)
                remote_addr = f"{conn.raddr.ip}"
                remote_port = str(conn.raddr.port)
                status = conn.status
                pid = str(conn.pid) if conn.pid else "N/A"
                
                table.add_row(
                    local_addr,
                    local_port,
                    remote_addr,
                    remote_port,
                    status,
                    pid
                )
        except:
            continue
    
    return table

def get_wifi_info():
    table = Table(title="WiFi Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    if platform.system() == "Windows":
        try:
            output = subprocess.check_output(['netsh', 'wlan', 'show', 'interfaces']).decode('utf-8')
            for line in output.split('\n'):
                if ':' in line:
                    key, value = line.split(':', 1)
                    table.add_row(key.strip(), value.strip())
        except:
            table.add_row("WiFi Info", "Unable to fetch on Windows")
    else:
        try:
            output = subprocess.check_output(['iwconfig']).decode('utf-8')
            for line in output.split('\n'):
                if len(line.strip()) > 0:
                    if ':' in line:
                        key, value = line.split(':', 1)
                    else:
                        key, value = line.split(' ', 1)
                    table.add_row(key.strip(), value.strip())
        except:
            table.add_row("WiFi Info", "Unable to fetch on Linux")
    
    return table

def get_network_statistics():
    table = Table(title="Network Statistics")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    stats = psutil.net_io_counters()
    
    table.add_row("Bytes Sent", f"{stats.bytes_sent / (1024**3):.2f} GB")
    table.add_row("Bytes Received", f"{stats.bytes_recv / (1024**3):.2f} GB")
    table.add_row("Packets Sent", str(stats.packets_sent))
    table.add_row("Packets Received", str(stats.packets_recv))
    table.add_row("Errors In", str(stats.errin))
    table.add_row("Errors Out", str(stats.errout))
    table.add_row("Drops In", str(stats.dropin))
    table.add_row("Drops Out", str(stats.dropout))
    
    return table

def get_dns_info():
    table = Table(title="DNS Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    try:
        with open('/etc/resolv.conf', 'r') as f:
            for line in f:
                if line.startswith('nameserver'):
                    table.add_row("DNS Server", line.split()[1])
    except:
        try:
            output = subprocess.check_output(['ipconfig', '/all']).decode('utf-8')
            dns_servers = []
            for line in output.split('\n'):
                if 'DNS Servers' in line:
                    dns_servers.append(line.split(':')[1].strip())
            for server in dns_servers:
                table.add_row("DNS Server", server)
        except:
            table.add_row("DNS Info", "Unable to fetch")
    
    return table

def get_route_table():
    table = Table(title="Routing Table")
    table.add_column("Destination", style="cyan")
    table.add_column("Gateway", style="green")
    table.add_column("Interface", style="yellow")
    table.add_column("Metric", style="magenta")
    
    try:
        if platform.system() == "Windows":
            output = subprocess.check_output(['route', 'print']).decode('utf-8')
            routes = False
            for line in output.split('\n'):
                if 'Active Routes:' in line:
                    routes = True
                    continue
                if routes and len(line.strip()) > 0:
                    parts = line.split()
                    if len(parts) >= 4:
                        table.add_row(parts[0], parts[1], parts[2], parts[3])
        else:
            output = subprocess.check_output(['route', '-n']).decode('utf-8')
            for line in output.split('\n')[2:]:
                if len(line.strip()) > 0:
                    parts = line.split()
                    if len(parts) >= 8:
                        table.add_row(parts[0], parts[1], parts[7], parts[5])
    except:
        table.add_row("Route Table", "Unable to fetch", "", "")
    
    return table 