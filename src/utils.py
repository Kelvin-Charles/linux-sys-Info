import os
import json
from datetime import datetime
from rich.console import Console

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