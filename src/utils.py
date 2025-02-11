import os
import json
from datetime import datetime
from rich.console import Console
import subprocess
import getpass
from pathlib import Path

console = Console()

def export_to_file(data, format='txt'):
    try:
        # Ask for save location
        default_dir = str(Path.home() / "Documents")
        while True:
            save_dir = input(f"Enter save directory (default: {default_dir}): ") or default_dir
            
            # Expand user path and make absolute
            save_dir = os.path.expanduser(save_dir)
            save_dir = os.path.abspath(save_dir)
            
            # Check if directory exists or can be created
            if not os.path.exists(save_dir):
                try:
                    os.makedirs(save_dir, exist_ok=True)
                except PermissionError:
                    console.print(f"[red]No permission to create directory: {save_dir}[/red]")
                    continue
            
            # Check if directory is writable
            if not os.access(save_dir, os.W_OK):
                console.print(f"[red]No write permission for directory: {save_dir}[/red]")
                continue
            
            break
        
        # Generate filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        default_filename = f"system_info_{timestamp}"
        
        while True:
            filename = input(f"Enter filename (default: {default_filename}): ") or default_filename
            
            # Add extension if not provided
            if format == 'txt' and not filename.endswith('.txt'):
                filename += '.txt'
            elif format == 'html' and not filename.endswith('.html'):
                filename += '.html'
            
            # Combine path
            filepath = os.path.join(save_dir, filename)
            
            # Check if file exists
            if os.path.exists(filepath):
                overwrite = input("File already exists. Overwrite? (y/n): ").lower()
                if overwrite != 'y':
                    continue
            
            try:
                # Test write permission with a temporary file
                test_file = os.path.join(save_dir, '.test_write')
                with open(test_file, 'w') as f:
                    f.write('test')
                os.remove(test_file)
                break
            except PermissionError:
                console.print(f"[red]No write permission for file: {filepath}[/red]")
                continue
        
        # Format the data based on the chosen format
        if format == 'html':
            formatted_data = f"""
<!DOCTYPE html>
<html>
<head>
    <title>System Information Report</title>
    <meta charset="utf-8">
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 20px;
            background-color: #f5f5f5;
            color: #333;
            line-height: 1.6;
        }}
        .container {{
            max-width: 1200px;
            margin: 0 auto;
            background-color: white;
            padding: 20px;
            border-radius: 5px;
            box-shadow: 0 0 10px rgba(0,0,0,0.1);
        }}
        .section {{
            margin-bottom: 20px;
            padding: 15px;
            border: 1px solid #ddd;
            border-radius: 4px;
        }}
        .title {{
            color: #333;
            border-bottom: 2px solid #007bff;
            padding-bottom: 5px;
            margin-bottom: 15px;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 15px 0;
            background-color: white;
        }}
        th, td {{
            padding: 12px 8px;
            text-align: left;
            border: 1px solid #ddd;
        }}
        th {{
            background-color: #f8f9fa;
            font-weight: bold;
        }}
        tr:nth-child(even) {{
            background-color: #f9f9f9;
        }}
        tr:hover {{
            background-color: #f5f5f5;
        }}
        pre {{
            background-color: #f8f9fa;
            padding: 10px;
            border-radius: 4px;
            overflow-x: auto;
            white-space: pre-wrap;
            word-wrap: break-word;
        }}
        .timestamp {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .footer {{
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #ddd;
            text-align: center;
            color: #666;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1 class="title">System Information Report</h1>
        <p class="timestamp">Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <div class="section">
            {data}
        </div>
        
    </div>
</body>
</html>
"""
        else:
            formatted_data = f"""
System Information Report
Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
----------------------------------------

{data}

Generated by Linux System Info Tool
"""
        
        # Write the actual file
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(formatted_data)
        
        console.print(f"[green]Information exported to {filepath}[/green]")
        
        # Ask if user wants to open the file
        if input("Would you like to open the exported file? (y/n): ").lower() == 'y':
            try:
                if os.name == 'nt':  # Windows
                    os.startfile(filepath)
                else:  # Linux/Mac
                    subprocess.run(['xdg-open', filepath])
            except Exception as e:
                console.print(f"[yellow]Could not open file: {str(e)}[/yellow]")
                
    except Exception as e:
        console.print(f"[red]Error exporting information: {str(e)}[/red]")
        console.print("[yellow]Make sure you have write permissions in the selected directory.[/yellow]")

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