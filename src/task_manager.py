import psutil
from rich.table import Table
from rich.console import Console
from datetime import datetime
import os
import signal
from rich import box
from rich.panel import Panel
from rich.layout import Layout
import time

console = Console()

class TaskManager:
    def __init__(self):
        self.console = Console()
        self.refresh_rate = 2  # seconds
        
    def get_process_list(self, sort_by='cpu', show_all=False):
        table = Table(
            title="Task Manager",
            box=box.DOUBLE,
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("PID", justify="right", style="cyan", no_wrap=True)
        table.add_column("Name", style="green", no_wrap=True)
        table.add_column("CPU %", justify="right", style="yellow", no_wrap=True)
        table.add_column("Memory %", justify="right", style="red", no_wrap=True)
        table.add_column("Status", style="magenta", no_wrap=True)
        table.add_column("Priority", style="blue", no_wrap=True)
        table.add_column("Threads", style="green", no_wrap=True)
        table.add_column("User", style="cyan", no_wrap=True)
        
        processes = []
        for proc in psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent', 
                                       'status', 'username', 'nice', 'num_threads']):
            try:
                pinfo = proc.info
                processes.append(pinfo)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        
        # Sort processes based on criteria
        if sort_by == 'cpu':
            processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        elif sort_by == 'memory':
            processes.sort(key=lambda x: x['memory_percent'], reverse=True)
        elif sort_by == 'pid':
            processes.sort(key=lambda x: x['pid'])
        elif sort_by == 'name':
            processes.sort(key=lambda x: x['name'].lower())
        
        # Show all processes or just top 20
        display_processes = processes if show_all else processes[:20]
        
        for proc in display_processes:
            try:
                table.add_row(
                    str(proc['pid']),
                    proc['name'][:30],
                    f"{proc['cpu_percent']:.1f}",
                    f"{proc['memory_percent']:.1f}",
                    proc['status'],
                    str(proc['nice']),
                    str(proc['num_threads']),
                    proc.get('username', 'N/A')
                )
            except:
                continue
        
        # Add system resource summary
        self.add_system_summary()
        return table

    def add_system_summary(self):
        cpu_percent = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        
        summary = Table(box=box.SIMPLE)
        summary.add_column("Resource", style="cyan")
        summary.add_column("Usage", style="yellow")
        
        summary.add_row("CPU Usage", f"{cpu_percent}%")
        summary.add_row("Memory Usage", f"{memory.percent}%")
        summary.add_row("Swap Usage", f"{swap.percent}%")
        
        console.print(Panel(summary, title="System Summary", border_style="green"))

    def kill_process(self, pid, force=False):
        try:
            process = psutil.Process(pid)
            process_name = process.name()
            
            if force:
                process.kill()  # Force kill
                msg = "forcefully terminated"
            else:
                process.terminate()  # Graceful termination
                msg = "terminated"
            
            console.print(f"[green]Successfully {msg} process {process_name} (PID: {pid})[/green]")
        except psutil.NoSuchProcess:
            console.print(f"[red]Process with PID {pid} not found[/red]")
        except psutil.AccessDenied:
            console.print(f"[red]Access denied to terminate process with PID {pid}[/red]")
            console.print("[yellow]Try running with administrative privileges[/yellow]")
        except Exception as e:
            console.print(f"[red]Error terminating process: {str(e)}[/red]")

    def change_priority(self, pid, priority):
        try:
            process = psutil.Process(pid)
            process.nice(priority)
            console.print(f"[green]Successfully changed priority of PID {pid} to {priority}[/green]")
        except Exception as e:
            console.print(f"[red]Error changing priority: {str(e)}[/red]")

    def show_process_details(self, pid):
        try:
            process = psutil.Process(pid)
            table = Table(title=f"Process Details - {process.name()} (PID: {pid})")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            # Basic Info
            table.add_row("Name", process.name())
            table.add_row("Status", process.status())
            table.add_row("Created", datetime.fromtimestamp(process.create_time()).strftime("%Y-%m-%d %H:%M:%S"))
            table.add_row("CPU Usage", f"{process.cpu_percent()}%")
            table.add_row("Memory Usage", f"{process.memory_percent():.1f}%")
            table.add_row("User", process.username())
            table.add_row("Priority", str(process.nice()))
            table.add_row("Threads", str(process.num_threads()))
            
            # Memory Details
            memory_info = process.memory_info()
            table.add_row("RSS Memory", f"{memory_info.rss / (1024*1024):.2f} MB")
            table.add_row("VMS Memory", f"{memory_info.vms / (1024*1024):.2f} MB")
            
            # IO Counters
            try:
                io_counters = process.io_counters()
                table.add_row("Read Bytes", f"{io_counters.read_bytes / (1024*1024):.2f} MB")
                table.add_row("Write Bytes", f"{io_counters.write_bytes / (1024*1024):.2f} MB")
            except:
                pass
            
            # Network Connections
            try:
                connections = process.connections()
                if connections:
                    table.add_row("Network Connections", str(len(connections)))
            except:
                pass
            
            # Command Line
            try:
                table.add_row("Command", " ".join(process.cmdline()))
            except:
                pass
            
            return table
        except psutil.NoSuchProcess:
            console.print(f"[red]Process with PID {pid} not found[/red]")
        except psutil.AccessDenied:
            console.print(f"[red]Access denied to process with PID {pid}[/red]")
        except Exception as e:
            console.print(f"[red]Error getting process details: {str(e)}[/red]")

def run_task_manager():
    task_manager = TaskManager()
    show_all = False
    sort_by = 'cpu'
    auto_refresh = False
    
    while True:
        console.clear()
        console.print(task_manager.get_process_list(sort_by=sort_by, show_all=show_all))
        
        console.print("\n[bold cyan]Task Manager Commands:[/bold cyan]")
        console.print("[1] Refresh Process List")
        console.print("[2] Toggle Auto-Refresh (Current: {})".format("On" if auto_refresh else "Off"))
        console.print("[3] Sort by CPU Usage")
        console.print("[4] Sort by Memory Usage")
        console.print("[5] Sort by PID")
        console.print("[6] Sort by Name")
        console.print("[7] Toggle Show All (Current: {})".format("All" if show_all else "Top 20"))
        console.print("[8] Kill Process")
        console.print("[9] Force Kill Process")
        console.print("[10] Change Process Priority")
        console.print("[11] Process Details")
        console.print("[12] Exit")
        
        if auto_refresh:
            console.print("\n[yellow]Auto-refreshing every 2 seconds. Press any key to stop.[/yellow]")
            time.sleep(2)
            continue
        
        choice = input("\nEnter your choice (1-12): ")
        
        if choice == "1":
            continue
        elif choice == "2":
            auto_refresh = not auto_refresh
        elif choice == "3":
            sort_by = 'cpu'
        elif choice == "4":
            sort_by = 'memory'
        elif choice == "5":
            sort_by = 'pid'
        elif choice == "6":
            sort_by = 'name'
        elif choice == "7":
            show_all = not show_all
        elif choice == "8":
            pid = input("Enter PID to terminate: ")
            try:
                task_manager.kill_process(int(pid))
            except ValueError:
                console.print("[red]Invalid PID format[/red]")
        elif choice == "9":
            pid = input("Enter PID to force kill: ")
            try:
                task_manager.kill_process(int(pid), force=True)
            except ValueError:
                console.print("[red]Invalid PID format[/red]")
        elif choice == "10":
            try:
                pid = int(input("Enter PID: "))
                priority = int(input("Enter priority (-20 to 19, lower = higher priority): "))
                task_manager.change_priority(pid, priority)
            except ValueError:
                console.print("[red]Invalid input format[/red]")
        elif choice == "11":
            pid = input("Enter PID for details: ")
            try:
                details = task_manager.show_process_details(int(pid))
                if details:
                    console.print(details)
            except ValueError:
                console.print("[red]Invalid PID format[/red]")
        elif choice == "12":
            break
        
        if not auto_refresh:
            input("\nPress Enter to continue...")

if __name__ == "__main__":
    run_task_manager() 