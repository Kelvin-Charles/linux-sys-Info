import psutil
import cpuinfo
import GPUtil
import platform
import os
import subprocess
from rich.table import Table
from datetime import datetime
from rich.console import Console

console = Console()

def get_cpu_info():
    table = Table(title="CPU Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    try:
        cpu_info = cpuinfo.get_cpu_info()
        cpu_freq = psutil.cpu_freq()
        
        table.add_row("CPU Model", str(cpu_info.get('brand_raw', 'N/A')))
        table.add_row("Architecture", str(cpu_info.get('arch', 'N/A')))
        table.add_row("Physical Cores", str(psutil.cpu_count(logical=False)))
        table.add_row("Total Cores", str(psutil.cpu_count(logical=True)))
        table.add_row("Max Frequency", f"{cpu_freq.max:.2f}MHz" if cpu_freq else "N/A")
        table.add_row("Current Frequency", f"{cpu_freq.current:.2f}MHz" if cpu_freq else "N/A")
        table.add_row("Min Frequency", f"{cpu_freq.min:.2f}MHz" if cpu_freq else "N/A")
        table.add_row("CPU Usage", f"{psutil.cpu_percent()}%")
        table.add_row("Cache Size", str(cpu_info.get('l3_cache_size', 'N/A')))
        table.add_row("Stepping", str(cpu_info.get('stepping', 'N/A')))
        table.add_row("Vendor ID", str(cpu_info.get('vendor_id_raw', 'N/A')))
        
        # CPU Temperature (if available)
        try:
            temperatures = psutil.sensors_temperatures()
            if temperatures:
                for name, entries in temperatures.items():
                    for entry in entries:
                        table.add_row(f"Temperature ({name})", f"{entry.current}°C")
        except:
            pass
    except Exception as e:
        table.add_row("Error", f"Unable to fetch CPU info: {str(e)}")
    
    return table

def get_memory_info():
    table = Table(title="Memory Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    try:
        virtual_memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        # RAM Information
        table.add_row("Total RAM", f"{virtual_memory.total / (1024**3):.2f} GB")
        table.add_row("Available RAM", f"{virtual_memory.available / (1024**3):.2f} GB")
        table.add_row("Used RAM", f"{virtual_memory.used / (1024**3):.2f} GB")
        table.add_row("RAM Usage", f"{virtual_memory.percent}%")
        table.add_row("RAM Speed", str(get_ram_speed()))
        
        # Swap Information
        table.add_row("Total Swap", f"{swap.total / (1024**3):.2f} GB")
        table.add_row("Used Swap", f"{swap.used / (1024**3):.2f} GB")
        table.add_row("Free Swap", f"{swap.free / (1024**3):.2f} GB")
        table.add_row("Swap Usage", f"{swap.percent}%")
    except Exception as e:
        table.add_row("Error", f"Unable to fetch memory info: {str(e)}")
    
    return table

def get_gpu_info():
    table = Table(title="GPU Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    try:
        gpus = GPUtil.getGPUs()
        if gpus:
            for i, gpu in enumerate(gpus):
                table.add_row(f"GPU {i+1} Name", str(gpu.name))
                table.add_row(f"GPU {i+1} Driver", str(gpu.driver))
                table.add_row(f"GPU {i+1} Memory Total", f"{gpu.memoryTotal} MB")
                table.add_row(f"GPU {i+1} Memory Used", f"{gpu.memoryUsed} MB")
                table.add_row(f"GPU {i+1} Memory Free", f"{gpu.memoryFree} MB")
                table.add_row(f"GPU {i+1} Temperature", f"{gpu.temperature} °C")
                table.add_row(f"GPU {i+1} Load", f"{gpu.load * 100:.1f}%")
        else:
            # Try to get GPU info using lspci on Linux
            if platform.system() == "Linux":
                try:
                    gpu_info = subprocess.check_output("lspci | grep -i 'vga\|3d\|2d'", shell=True).decode()
                    for line in gpu_info.split('\n'):
                        if line.strip():
                            table.add_row("GPU", line.split(': ')[1] if ': ' in line else line)
                except:
                    table.add_row("GPU Information", "No GPU information available")
            else:
                table.add_row("GPU Information", "No GPU information available")
    except Exception as e:
        table.add_row("Error", f"Unable to fetch GPU info: {str(e)}")
    
    return table

def get_disk_info():
    table = Table(title="Disk Information")
    table.add_column("Device", style="cyan")
    table.add_column("Mount Point", style="green")
    table.add_column("File System", style="yellow")
    table.add_column("Type", style="magenta")
    table.add_column("Total", style="blue")
    table.add_column("Used", style="red")
    table.add_column("Free", style="green")
    table.add_column("Read Speed", style="yellow")
    table.add_column("Write Speed", style="yellow")
    
    try:
        console.print("[yellow]Analyzing disk drives (this may take a few moments)...[/yellow]")
        # Get disk I/O counters
        disk_io = psutil.disk_io_counters(perdisk=True)
        
        for partition in psutil.disk_partitions():
            try:
                with console.status(f"[bold blue]Analyzing {partition.device}..."):
                    usage = psutil.disk_usage(partition.mountpoint)
                
                # Determine if disk is SSD or HDD
                disk_type = get_disk_type(partition.device)
                
                # Get disk I/O speeds
                disk_name = partition.device.split('/')[-1] if '/' in partition.device else partition.device
                io_info = disk_io.get(disk_name, None)
                
                read_speed = "N/A"
                write_speed = "N/A"
                if io_info:
                    read_speed = f"{io_info.read_bytes / (1024**2):.2f} MB/s"
                    write_speed = f"{io_info.write_bytes / (1024**2):.2f} MB/s"
                
                table.add_row(
                    str(partition.device),
                    str(partition.mountpoint),
                    str(partition.fstype),
                    str(disk_type),
                    f"{usage.total / (1024**3):.2f} GB",
                    f"{usage.used / (1024**3):.2f} GB",
                    f"{usage.free / (1024**3):.2f} GB",
                    str(read_speed),
                    str(write_speed)
                )
            except:
                continue
    except Exception as e:
        table.add_row("Error", f"Unable to fetch disk info: {str(e)}", "", "", "", "", "", "", "")
    
    return table

def get_disk_type(device):
    """Determine if disk is SSD or HDD"""
    if platform.system() == "Linux":
        try:
            # Remove partition numbers to get base device
            base_device = ''.join([i for i in device if not i.isdigit()])
            rotational = open(f"/sys/block/{os.path.basename(base_device)}/queue/rotational").read().strip()
            return "HDD" if rotational == "1" else "SSD"
        except:
            return "Unknown"
    elif platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for disk in c.Win32_DiskDrive():
                if disk.DeviceID.lower() in device.lower():
                    return "SSD" if disk.MediaType and "SSD" in disk.MediaType else "HDD"
        except:
            return "Unknown"
    return "Unknown"

def get_ram_speed():
    """Get RAM speed if possible"""
    if platform.system() == "Linux":
        try:
            with open("/proc/cpuinfo") as f:
                for line in f:
                    if "MHz" in line:
                        return line.split(":")[1].strip()
        except:
            return "N/A"
    elif platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for mem in c.Win32_PhysicalMemory():
                return f"{mem.Speed} MHz"
        except:
            return "N/A"
    return "N/A"

def get_motherboard_info():
    table = Table(title="Motherboard Information")
    table.add_column("Property", style="cyan")
    table.add_column("Value", style="green")
    
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            board = c.Win32_BaseBoard()[0]
            bios = c.Win32_BIOS()[0]
            
            table.add_row("Manufacturer", board.Manufacturer)
            table.add_row("Model", board.Product)
            table.add_row("Serial Number", board.SerialNumber)
            table.add_row("BIOS Version", bios.Version)
            table.add_row("BIOS Vendor", bios.Manufacturer)
            table.add_row("BIOS Date", bios.ReleaseDate.split('.')[0])
        except:
            table.add_row("Motherboard Info", "Unable to fetch on Windows")
    else:
        try:
            with open('/sys/class/dmi/id/board_vendor') as f:
                table.add_row("Manufacturer", f.read().strip())
            with open('/sys/class/dmi/id/board_name') as f:
                table.add_row("Model", f.read().strip())
            with open('/sys/class/dmi/id/bios_version') as f:
                table.add_row("BIOS Version", f.read().strip())
            with open('/sys/class/dmi/id/bios_date') as f:
                table.add_row("BIOS Date", f.read().strip())
        except:
            table.add_row("Motherboard Info", "Unable to fetch on Linux")
    
    return table

def get_usb_devices():
    table = Table(title="USB Devices")
    table.add_column("Device", style="cyan")
    table.add_column("Vendor ID", style="green")
    table.add_column("Product ID", style="blue")
    table.add_column("Manufacturer", style="yellow")
    table.add_column("Product", style="magenta")
    
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for device in c.Win32_USBHub():
                table.add_row(
                    device.DeviceID,
                    device.DeviceID.split("\\")[-1].split("&")[0],
                    device.DeviceID.split("\\")[-1].split("&")[1],
                    device.Manufacturer,
                    device.Description
                )
        except:
            table.add_row("USB Devices", "Unable to fetch on Windows", "", "", "")
    else:
        try:
            usb_devices = subprocess.check_output(['lsusb']).decode().split('\n')
            for device in usb_devices:
                if device:
                    parts = device.split()
                    if len(parts) >= 6:
                        bus = parts[1]
                        device = parts[3][:-1]
                        id_parts = parts[5].split(':')
                        vendor = id_parts[0]
                        product = id_parts[1]
                        name = ' '.join(parts[6:])
                        table.add_row(f"Bus {bus} Device {device}", vendor, product, "", name)
        except:
            table.add_row("USB Devices", "Unable to fetch on Linux", "", "", "")
    
    return table

def get_pci_devices():
    table = Table(title="PCI Devices")
    table.add_column("Device", style="cyan")
    table.add_column("Vendor", style="green")
    table.add_column("Device ID", style="blue")
    table.add_column("Class", style="yellow")
    
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for device in c.Win32_PnPEntity():
                if device.PNPClass == "PCI":
                    table.add_row(
                        device.Name or "Unknown",
                        device.Manufacturer or "Unknown",
                        device.DeviceID or "Unknown",
                        device.PNPClass or "Unknown"
                    )
        except:
            table.add_row("PCI Devices", "Unable to fetch on Windows", "", "")
    else:
        try:
            pci_devices = subprocess.check_output(['lspci', '-vmm']).decode().split('\n\n')
            for device in pci_devices:
                if device:
                    lines = device.split('\n')
                    info = {}
                    for line in lines:
                        if ':' in line:
                            key, value = line.split(':', 1)
                            info[key.strip()] = value.strip()
                    
                    table.add_row(
                        info.get('Device', 'Unknown'),
                        info.get('Vendor', 'Unknown'),
                        info.get('SVendor', 'Unknown'),
                        info.get('Class', 'Unknown')
                    )
        except:
            table.add_row("PCI Devices", "Unable to fetch on Linux", "", "")
    
    return table

def get_sound_devices():
    table = Table(title="Sound Devices")
    table.add_column("Name", style="cyan")
    table.add_column("Manufacturer", style="green")
    table.add_column("Status", style="yellow")
    
    if platform.system() == "Windows":
        try:
            import wmi
            c = wmi.WMI()
            for device in c.Win32_SoundDevice():
                table.add_row(
                    device.Name or "Unknown",
                    device.Manufacturer or "Unknown",
                    "Enabled" if device.StatusInfo == 3 else "Disabled"
                )
        except:
            table.add_row("Sound Devices", "Unable to fetch on Windows", "")
    else:
        try:
            sound_devices = subprocess.check_output(['aplay', '-l']).decode().split('\n')
            for line in sound_devices:
                if line.startswith('card '):
                    parts = line.split(':')
                    if len(parts) >= 2:
                        name = parts[1].strip()
                        table.add_row(name, "N/A", "Available")
        except:
            table.add_row("Sound Devices", "Unable to fetch on Linux", "")
    
    return table 