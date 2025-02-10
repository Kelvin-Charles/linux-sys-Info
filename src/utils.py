import os
import json
from datetime import datetime
from rich.console import Console
import subprocess
import getpass

console = Console()

def export_to_file(data, format='txt'):
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if format == 'txt':
        filename = f"system_info_{timestamp}.txt"
        with open(filename, 'w') as f:
            f.write(data)
    elif format == 'html':
        filename = f"system_info_{timestamp}.html"
        with open(filename, 'w') as f:
            f.write(f"""
            <html>
            <head>
                <title>System Information Report</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .section {{ margin-bottom: 20px; }}
                    .title {{ color: #333; }}
                </style>
            </head>
            <body>
                {data}
            </body>
            </html>
            """)
    
    console.print(f"[green]Information exported to {filename}[/green]")

def format_bytes(bytes):
    """Convert bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024:
            return f"{bytes:.2f} {unit}"
        bytes /= 1024 

def get_sudo_password():
    try:
        password = getpass.getpass("[yellow]Root privileges required. Enter sudo password: [/yellow]")
        # Test the password
        cmd = ['sudo', '-S', 'true']
        process = subprocess.Popen(cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
        process.communicate(password.encode())
        
        if process.returncode == 0:
            return password
        else:
            console.print("[red]Incorrect password![/red]")
            return None
    except Exception as e:
        console.print(f"[red]Error getting sudo password: {str(e)}[/red]")
        return None 