import pwd
import grp
import subprocess
import crypt
import os
from rich.table import Table
from rich.console import Console
from rich.panel import Panel
from rich import box
from datetime import datetime
import spwd
from src.utils import get_sudo_password

console = Console()

class UserManager:
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
        
        # Send password first, then any input data
        input_text = self.sudo_password + '\n'
        if input_data:
            input_text += input_data
        
        stdout, stderr = process.communicate(input_text.encode())
        return process.returncode == 0, stdout, stderr

    def list_users(self, show_all=True):
        table = Table(
            title="User Management",
            box=box.DOUBLE,
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("Username", style="green")
        table.add_column("UID", style="cyan")
        table.add_column("GID", style="yellow")
        table.add_column("Home Directory", style="blue")
        table.add_column("Shell", style="magenta")
        table.add_column("Groups", style="red")
        table.add_column("Last Login", style="cyan")
        
        try:
            nologin_shells = ['/sbin/nologin', '/usr/sbin/nologin', '/bin/false', 'false', '/bin/sync']
            
            for user in pwd.getpwall():
                # Skip system users if show_all is False
                if not show_all and (user.pw_shell in nologin_shells or user.pw_uid < 1000):
                    continue
                
                # Get groups for user
                groups = [g.gr_name for g in grp.getgrall() if user.pw_name in g.gr_mem]
                if grp.getgrgid(user.pw_gid).gr_name not in groups:
                    groups.append(grp.getgrgid(user.pw_gid).gr_name)
                
                # Get last login
                try:
                    last_login = subprocess.check_output(['lastlog', '-u', user.pw_name]).decode()
                    last_login = last_login.split('\n')[1].split()[-4:]
                    last_login = ' '.join(last_login) if len(last_login) > 0 else "Never"
                except:
                    last_login = "Unknown"
                
                table.add_row(
                    user.pw_name,
                    str(user.pw_uid),
                    str(user.pw_gid),
                    user.pw_dir,
                    user.pw_shell,
                    ', '.join(groups),
                    last_login
                )
        except Exception as e:
            console.print(f"[red]Error listing users: {str(e)}[/red]")
        
        return table

    def list_groups(self):
        table = Table(
            title="Group Management",
            box=box.DOUBLE,
            header_style="bold cyan",
            border_style="blue"
        )
        table.add_column("Group Name", style="green")
        table.add_column("GID", style="cyan")
        table.add_column("Members", style="yellow")
        
        try:
            for group in grp.getgrall():
                table.add_row(
                    group.gr_name,
                    str(group.gr_gid),
                    ', '.join(group.gr_mem)
                )
        except Exception as e:
            console.print(f"[red]Error listing groups: {str(e)}[/red]")
        
        return table

    def add_user(self, username, password=None, create_home=True, shell="/bin/bash"):
        try:
            if not self.ensure_sudo():
                return
            
            cmd = ['useradd']
            if create_home:
                cmd.append('-m')
            cmd.extend(['-s', shell, username])
            
            success, _, stderr = self.run_sudo_command(cmd)
            if success:
                if password:
                    self.change_password(username, password)
                console.print(f"[green]Successfully created user {username}[/green]")
            else:
                console.print(f"[red]Error creating user: {stderr.decode()}[/red]")
        except Exception as e:
            console.print(f"[red]Error creating user: {str(e)}[/red]")

    def delete_user(self, username, remove_home=False):
        try:
            if not self.ensure_sudo():
                return
            
            cmd = ['userdel']
            if remove_home:
                cmd.append('-r')
            cmd.append(username)
            
            success, _, stderr = self.run_sudo_command(cmd)
            if success:
                console.print(f"[green]Successfully deleted user {username}[/green]")
            else:
                console.print(f"[red]Error deleting user: {stderr.decode()}[/red]")
        except Exception as e:
            console.print(f"[red]Error deleting user: {str(e)}[/red]")

    def change_password(self, username, password):
        try:
            subprocess.run(['chpasswd'], input=f"{username}:{password}".encode(), check=True)
            console.print(f"[green]Successfully changed password for {username}[/green]")
        except Exception as e:
            console.print(f"[red]Error changing password: {str(e)}[/red]")

    def add_group(self, groupname):
        try:
            subprocess.run(['groupadd', groupname], check=True)
            console.print(f"[green]Successfully created group {groupname}[/green]")
        except Exception as e:
            console.print(f"[red]Error creating group: {str(e)}[/red]")

    def delete_group(self, groupname):
        try:
            subprocess.run(['groupdel', groupname], check=True)
            console.print(f"[green]Successfully deleted group {groupname}[/green]")
        except Exception as e:
            console.print(f"[red]Error deleting group: {str(e)}[/red]")

    def add_user_to_group(self, username, groupname):
        try:
            subprocess.run(['usermod', '-a', '-G', groupname, username], check=True)
            console.print(f"[green]Successfully added {username} to group {groupname}[/green]")
        except Exception as e:
            console.print(f"[red]Error adding user to group: {str(e)}[/red]")

    def remove_user_from_group(self, username, groupname):
        try:
            # Get all groups for user
            groups = [g.gr_name for g in grp.getgrall() if username in g.gr_mem]
            if groupname in groups:
                groups.remove(groupname)
            
            # Set new groups
            subprocess.run(['usermod', '-G', ','.join(groups), username], check=True)
            console.print(f"[green]Successfully removed {username} from group {groupname}[/green]")
        except Exception as e:
            console.print(f"[red]Error removing user from group: {str(e)}[/red]")

    def get_real_users(self):
        """Get list of real users (non-system users with real shells)"""
        real_users = []
        nologin_shells = ['/sbin/nologin', '/usr/sbin/nologin', '/bin/false', 'false', '/bin/sync']
        
        try:
            for user in pwd.getpwall():
                if user.pw_shell not in nologin_shells and user.pw_uid >= 1000:
                    real_users.append(user.pw_name)
        except Exception as e:
            console.print(f"[red]Error getting real users: {str(e)}[/red]")
        
        return real_users

    def select_user(self, action="modify"):
        """Show list of real users and let user select one"""
        real_users = self.get_real_users()
        
        if not real_users:
            console.print("[yellow]No real users found in the system[/yellow]")
            return None
            
        console.print(f"\n[bold cyan]Available Users to {action}:[/bold cyan]")
        for i, username in enumerate(real_users, 1):
            console.print(f"[{i}] {username}")
        
        while True:
            try:
                choice = input("\nSelect user number (or 0 to cancel): ")
                if choice == "0":
                    return None
                    
                index = int(choice) - 1
                if 0 <= index < len(real_users):
                    return real_users[index]
                else:
                    console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                console.print("[red]Please enter a valid number.[/red]")

    def show_user_details(self, username=None):
        if not self.ensure_sudo():
            return
            
        if username is None:
            username = self.select_user(action="view")
            if not username:
                return
        
        try:
            # Get basic user info
            user = pwd.getpwnam(username)
            
            # Get shadow info using sudo
            shadow_cmd = ['sudo', 'getent', 'shadow', username]
            shadow_output = subprocess.check_output(shadow_cmd, text=True)
            shadow_fields = shadow_output.strip().split(':')
            
            table = Table(title=f"User Details - {username}")
            table.add_column("Property", style="cyan")
            table.add_column("Value", style="green")
            
            table.add_row("Username", user.pw_name)
            table.add_row("UID", str(user.pw_uid))
            table.add_row("GID", str(user.pw_gid))
            table.add_row("Home Directory", user.pw_dir)
            table.add_row("Shell", user.pw_shell)
            
            # Get groups using sudo
            groups_cmd = ['sudo', 'groups', username]
            groups_output = subprocess.check_output(groups_cmd, text=True)
            groups = groups_output.split(':')[1].strip().split()
            table.add_row("Groups", ', '.join(groups))
            
            # Password status
            if shadow_fields[1].startswith('!'):
                pwd_status = "Locked"
            elif shadow_fields[1].startswith('*'):
                pwd_status = "Disabled"
            else:
                pwd_status = "Active"
            table.add_row("Password Status", pwd_status)
            
            # Last password change
            last_change = int(shadow_fields[2])
            if last_change > 0:
                change_date = datetime.fromtimestamp(last_change * 86400).strftime("%Y-%m-%d")
                table.add_row("Last Password Change", change_date)
            else:
                table.add_row("Last Password Change", "Never")
            
            # Add password aging information
            if len(shadow_fields) >= 8:
                min_days = shadow_fields[3]
                max_days = shadow_fields[4]
                warn_days = shadow_fields[5]
                inactive_days = shadow_fields[6]
                expire_date = shadow_fields[7]
                
                if min_days and min_days != "0":
                    table.add_row("Minimum Password Age", f"{min_days} days")
                if max_days and max_days != "99999":
                    table.add_row("Maximum Password Age", f"{max_days} days")
                if warn_days and warn_days != "7":
                    table.add_row("Password Warning Period", f"{warn_days} days")
                if inactive_days and inactive_days != "-1":
                    table.add_row("Password Inactivity Period", f"{inactive_days} days")
                if expire_date and expire_date != "-1":
                    expire = datetime.fromtimestamp(int(expire_date) * 86400).strftime("%Y-%m-%d")
                    table.add_row("Account Expiration Date", expire)
            
            # Get last login info using sudo
            try:
                lastlog_cmd = ['sudo', 'lastlog', '-u', username]
                lastlog_output = subprocess.check_output(lastlog_cmd, text=True)
                last_login = lastlog_output.split('\n')[1].strip()
                if last_login and "**Never logged in**" not in last_login:
                    table.add_row("Last Login", last_login)
                else:
                    table.add_row("Last Login", "Never")
            except:
                table.add_row("Last Login", "Unknown")
            
            return table
        except subprocess.CalledProcessError as e:
            console.print(f"[red]Error executing sudo command: {e.stderr if hasattr(e, 'stderr') else str(e)}[/red]")
        except Exception as e:
            console.print(f"[red]Error getting user details: {str(e)}[/red]")

    def modify_user(self, username=None, new_shell=None, new_home=None, new_groups=None):
        if not self.ensure_sudo():
            return
            
        if username is None:
            username = self.select_user(action="modify")
            if not username:
                return
        
        try:
            console.print("\n[bold cyan]What would you like to modify?[/bold cyan]")
            console.print("[1] Full Name (GECOS)")
            console.print("[2] Password")
            console.print("[3] Login Shell")
            console.print("[4] Home Directory")
            console.print("[5] Account Expiry Date")
            console.print("[6] Group Membership")
            console.print("[7] Lock/Unlock Account")
            console.print("[0] Cancel")
            
            choice = input("\nEnter your choice (0-7): ")
            
            if choice == "0":
                return
            elif choice == "1":
                full_name = input("Enter new full name: ")
                cmd = ['chfn', '-f', full_name, username]
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully updated full name for {username}[/green]")
                else:
                    console.print(f"[red]Error updating full name: {stderr.decode()}[/red]")
            
            elif choice == "2":
                password = input("Enter new password: ")
                if password:
                    cmd = ['chpasswd']
                    success, _, stderr = self.run_sudo_command(cmd, f"{username}:{password}")
                    if success:
                        console.print(f"[green]Successfully changed password for {username}[/green]")
                    else:
                        console.print(f"[red]Error changing password: {stderr.decode()}[/red]")
            
            elif choice == "3":
                available_shells = ['/bin/bash', '/bin/sh', '/bin/zsh', '/bin/fish']
                console.print("\nAvailable shells:")
                for i, shell in enumerate(available_shells, 1):
                    console.print(f"[{i}] {shell}")
                console.print("[8] Other")
                
                shell_choice = input("\nSelect shell (1-8): ")
                if shell_choice == "8":
                    new_shell = input("Enter shell path: ")
                else:
                    try:
                        new_shell = available_shells[int(shell_choice) - 1]
                    except:
                        console.print("[red]Invalid selection[/red]")
                        return
                
                cmd = ['usermod', '-s', new_shell, username]
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully changed shell to {new_shell}[/green]")
                else:
                    console.print(f"[red]Error changing shell: {stderr.decode()}[/red]")
            
            elif choice == "4":
                new_home = input("Enter new home directory path: ")
                move_files = input("Move files to new location? (y/n): ").lower() == 'y'
                
                cmd = ['usermod']
                if move_files:
                    cmd.append('-m')
                cmd.extend(['-d', new_home, username])
                
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully changed home directory to {new_home}[/green]")
                else:
                    console.print(f"[red]Error changing home directory: {stderr.decode()}[/red]")
            
            elif choice == "5":
                expiry_date = input("Enter expiry date (YYYY-MM-DD) or 'never': ")
                if expiry_date.lower() == 'never':
                    cmd = ['usermod', '-e', '', username]
                else:
                    cmd = ['usermod', '-e', expiry_date, username]
                
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully updated expiry date[/green]")
                else:
                    console.print(f"[red]Error updating expiry date: {stderr.decode()}[/red]")
            
            elif choice == "6":
                # Show current groups first
                groups_cmd = ['groups', username]
                groups_output = subprocess.check_output(groups_cmd).decode()
                console.print(f"\nCurrent groups: {groups_output}")
                
                print("\nModify groups:")
                print("1. Add to new group")
                print("2. Remove from group")
                print("3. Set all groups")
                
                group_choice = input("\nEnter choice (1-3): ")
                
                if group_choice == "1":
                    group = input("Enter group name to add: ")
                    cmd = ['usermod', '-a', '-G', group, username]
                elif group_choice == "2":
                    group = input("Enter group name to remove: ")
                    current_groups = groups_output.split(':')[1].strip().split()
                    if group in current_groups:
                        current_groups.remove(group)
                    cmd = ['usermod', '-G', ','.join(current_groups), username]
                elif group_choice == "3":
                    groups = input("Enter all groups (comma-separated): ")
                    cmd = ['usermod', '-G', groups, username]
                else:
                    console.print("[red]Invalid choice[/red]")
                    return
                
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully updated group membership[/green]")
                else:
                    console.print(f"[red]Error updating groups: {stderr.decode()}[/red]")
            
            elif choice == "7":
                print("\n1. Lock account")
                print("2. Unlock account")
                lock_choice = input("\nEnter choice (1-2): ")
                
                if lock_choice == "1":
                    cmd = ['usermod', '-L', username]
                    action = "locked"
                elif lock_choice == "2":
                    cmd = ['usermod', '-U', username]
                    action = "unlocked"
                else:
                    console.print("[red]Invalid choice[/red]")
                    return
                
                success, _, stderr = self.run_sudo_command(cmd)
                if success:
                    console.print(f"[green]Successfully {action} account[/green]")
                else:
                    console.print(f"[red]Error {action} account: {stderr.decode()}[/red]")
            
        except Exception as e:
            console.print(f"[red]Error modifying user: {str(e)}[/red]")

def run_user_manager():
    user_manager = UserManager()
    show_all_users = True
    
    # Get sudo password at startup
    if not user_manager.ensure_sudo():
        console.print("[red]Root privileges required to manage users and groups![/red]")
        return
    
    while True:
        console.clear()
        console.print("\n[bold cyan]User and Group Management[/bold cyan]")
        console.print("[1] List All Users")
        console.print("[2] List Real Users Only")
        console.print("[3] List All Groups")
        console.print("[4] Add User")
        console.print("[5] Delete User")
        console.print("[6] Change User Password")
        console.print("[7] Add Group")
        console.print("[8] Delete Group")
        console.print("[9] Add User to Group")
        console.print("[10] Remove User from Group")
        console.print("[11] Modify User")
        console.print("[12] Show User Details")
        console.print("[13] Exit")
        
        choice = input("\nEnter your choice (1-13): ")
        
        if choice == "1":
            console.print(user_manager.list_users(show_all=True))
        elif choice == "2":
            console.print(user_manager.list_users(show_all=False))
        elif choice == "3":
            console.print(user_manager.list_groups())
        elif choice == "4":
            username = input("Enter username: ")
            password = input("Enter password (leave blank for none): ")
            create_home = input("Create home directory? (y/n): ").lower() == 'y'
            shell = input("Enter shell (default: /bin/bash): ") or "/bin/bash"
            user_manager.add_user(username, password, create_home, shell)
        elif choice == "5":
            username = input("Enter username: ")
            remove_home = input("Remove home directory? (y/n): ").lower() == 'y'
            user_manager.delete_user(username, remove_home)
        elif choice == "6":
            username = input("Enter username: ")
            password = input("Enter new password: ")
            user_manager.change_password(username, password)
        elif choice == "7":
            groupname = input("Enter group name: ")
            user_manager.add_group(groupname)
        elif choice == "8":
            groupname = input("Enter group name: ")
            user_manager.delete_group(groupname)
        elif choice == "9":
            username = input("Enter username: ")
            groupname = input("Enter group name: ")
            user_manager.add_user_to_group(username, groupname)
        elif choice == "10":
            username = input("Enter username: ")
            groupname = input("Enter group name: ")
            user_manager.remove_user_from_group(username, groupname)
        elif choice == "11":
            username = user_manager.select_user(action="modify")
            if username:
                new_shell = input("Enter new shell (leave blank to skip): ")
                new_home = input("Enter new home directory (leave blank to skip): ")
                new_groups = input("Enter new groups (comma-separated, leave blank to skip): ")
                if new_groups:
                    new_groups = new_groups.split(',')
                user_manager.modify_user(username, new_shell or None, new_home or None, new_groups)
        elif choice == "12":
            username = user_manager.select_user(action="view")
            if username:
                details = user_manager.show_user_details(username)
                if details:
                    console.print(details)
        elif choice == "13":
            break
        
        input("\nPress Enter to continue...")

if __name__ == "__main__":
    if os.geteuid() != 0:
        console.print("[red]This script must be run as root![/red]")
        exit(1)
    run_user_manager() 