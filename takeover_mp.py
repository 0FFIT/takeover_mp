import os
import shutil
import requests
import time
import ctypes
import subprocess
import sys
import glob
from pathlib import Path

# ANSI color codes for terminal output
class Colors:
    RED = '\033[91m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RESET = '\033[0m'

def clear_screen():
    os.system('cls')

def print_title():
    art = f'''{Colors.RED}
{Colors.RESET}
'''
    print(art)

class SimpleProgressBar:
    def __init__(self, total, desc="Processing", bar_length=40):
        self.total = total
        self.desc = desc
        self.count = 0
        self.bar_length = bar_length
        self.start_time = time.time()
        self.completed = False
        # Enable Windows ANSI color support
        os.system('')

    def update(self, increment=1):
        self.count += increment
        percent = min(float(self.count) / self.total, 1.0)
        
        # Calculate progress bar
        filled_len = int(self.bar_length * percent)
        
        # Use red for incomplete, blue for complete
        if self.completed:
            bar = Colors.BLUE + '█' * self.bar_length + Colors.RESET
            percent = 1.0
            count_display = self.total
        else:
            bar = Colors.RED + '█' * filled_len + Colors.RESET + '░' * (self.bar_length - filled_len)
            count_display = self.count
        
        # Calculate elapsed time
        elapsed = time.time() - self.start_time
        
        # Output the progress bar
        sys.stdout.write(f'\r{self.desc}: [{bar}] {count_display}/{self.total} ({percent:.1%})')
        sys.stdout.flush()

    def complete(self):
        """Force progress bar to 100%"""
        self.completed = True
        self.update(0)  # Update display without incrementing
        self.close()

    def close(self):
        elapsed = time.time() - self.start_time
        
        # If not already completed, set to 100%
        if not self.completed:
            self.completed = True
            self.update(0)
            
        print(f"\n{Colors.GREEN}Completed in {elapsed:.2f} seconds.{Colors.RESET}")

def create_progress_bar(total, desc="Processing"):
    return SimpleProgressBar(total, desc)

def find_rust_path():
    drives = ['C', 'D', 'E', 'F', 'G']
    common_paths = [
        ":\\Program Files (x86)\\Steam\\steamapps\\content\\app_252490",
        ":\\Steam\\steamapps\\content\\app_252490"
    ]
    
    print("Searching for Rust installation...")
    progress = create_progress_bar(len(drives) * len(common_paths), "Searching drives")
    
    # Check common paths first
    for drive in drives:
        for path in common_paths:
            full_path = f"{drive}{path}"
            progress.update(1)
            if os.path.exists(full_path):
                # Force progress to 100% when found
                progress.complete()
                return full_path
    
    progress.close()
    
    # Deep search for Rust files
    print("Deep searching all drives - this may take a minute...")
    
    progress = create_progress_bar(len([d for d in drives if os.path.exists(f"{d}:")]), "Deep scanning")
    
    for drive in drives:
        if os.path.exists(f"{drive}:"):
            try:
                # Use glob to find folders containing app_252490
                matches = glob.glob(f"{drive}:\\**\\*app_252490*", recursive=True)
                for match in matches:
                    if os.path.isdir(match):
                        # Force progress to 100% when found
                        progress.complete()
                        return match
                progress.update(1)
            except Exception:
                progress.update(1)
                continue
    
    progress.close()
    return None

def copy_files(rust_path, dest_folder):
    # Check and copy files from depot_252494\bundles if it exists
    bundles_path = os.path.join(rust_path, "depot_252494", "bundles")
    if os.path.exists(bundles_path):
        files_count = sum([len(files) for _, _, files in os.walk(bundles_path)])
        print(f"Copying bundles from depot_252494 ({files_count} files)...")
        
        progress = create_progress_bar(files_count, "Copying bundles")
        
        # Ensure destination folder exists
        os.makedirs(os.path.join(dest_folder, "bundles"), exist_ok=True)
        
        # Copy files with progress tracking
        current_count = 0
        for root, _, files in os.walk(bundles_path):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, bundles_path)
                dst_file = os.path.join(dest_folder, "bundles", rel_path)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)
                current_count += 1
                progress.update(1)
        
        # Ensure progress bar completes even if file count was off
        progress.complete()
    
    # Check and copy files from depot_252495 if it exists
    depot_path = os.path.join(rust_path, "depot_252495")
    if os.path.exists(depot_path):
        files_count = sum([len(files) for _, _, files in os.walk(depot_path)])
        print(f"Copying files from depot_252495 ({files_count} files)...")
        
        progress = create_progress_bar(files_count, "Copying depot files")
        
        # Copy files with progress tracking
        current_count = 0
        for root, _, files in os.walk(depot_path):
            for file in files:
                src_file = os.path.join(root, file)
                rel_path = os.path.relpath(src_file, depot_path)
                dst_file = os.path.join(dest_folder, rel_path)
                os.makedirs(os.path.dirname(dst_file), exist_ok=True)
                shutil.copy2(src_file, dst_file)
                current_count += 1
                progress.update(1)
        
        # Ensure progress bar completes even if file count was off
        progress.complete()
    
    return True

def download_icon(icon_url, icon_file):
    print("Downloading custom icon...")
    try:
        progress = create_progress_bar(1, "Downloading icon")
        response = requests.get(icon_url, stream=True)
        if response.status_code == 200:
            with open(icon_file, 'wb') as f:
                f.write(response.content)
            progress.complete()
            return True
        else:
            progress.close()
            print(f"Failed to download icon: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"Error downloading icon: {e}")
        return False

def apply_icon(dest_folder, icon_file):
    print("Applying custom icon to folder...")
    progress = create_progress_bar(3, "Setting icon")
    
    # Make sure folder is not read-only
    if os.path.exists(dest_folder):
        try:
            # Clear read-only attribute if set
            ctypes.windll.kernel32.SetFileAttributesW(dest_folder, 0)
            progress.update(1)
        except Exception:
            progress.update(1)
            pass
    
    # Create desktop.ini file
    desktop_ini_path = os.path.join(dest_folder, "desktop.ini")
    
    # Remove existing desktop.ini if it exists
    if os.path.exists(desktop_ini_path):
        try:
            # Clear system and hidden attributes if set
            ctypes.windll.kernel32.SetFileAttributesW(desktop_ini_path, 0)
            os.remove(desktop_ini_path)
        except Exception:
            pass
    
    # Create new desktop.ini file
    try:
        with open(desktop_ini_path, 'w') as f:
            f.write("[.ShellClassInfo]\n")
            f.write(f"IconFile={icon_file}\n")
            f.write("IconIndex=0\n")
            f.write(f"IconResource={icon_file},0\n")
            f.write("[ViewState]\n")
            f.write("Mode=\n")
            f.write("Vid=\n")
            f.write("FolderType=Generic\n")
        progress.update(1)
        
        # Set required attributes
        ctypes.windll.kernel32.SetFileAttributesW(desktop_ini_path, 0x06)  # Hidden + System
        ctypes.windll.kernel32.SetFileAttributesW(dest_folder, 0x01)  # Read-only
        progress.update(1)
        
        progress.complete()
        
        # Refresh icon cache (restart explorer)
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], 
                      stdout=subprocess.DEVNULL, 
                      stderr=subprocess.DEVNULL)
        time.sleep(1)
        subprocess.Popen("explorer.exe")
        
        return True
    except Exception as e:
        progress.close()
        print(f"Error applying icon: {e}")
        return False

def main():
    try:
        clear_screen()
        print_title()
        
        # Set up paths
        dest_folder = os.path.join(os.path.expanduser("~"), "Desktop", "takeover")
        script_dir = os.path.dirname(os.path.abspath(__file__))
        
        # First check if we have a local icon
        icon_path = os.path.join(script_dir, "takeover.ico")
        if os.path.exists(icon_path):
            icon_url = None  # Will use local icon
        else:
            icon_url = "https://raw.githubusercontent.com/0FFIT/takeover_mp/main/takeover.ico"
        
        icon_file = os.path.join(dest_folder, "folder.ico")
        
        # Create destination folder if it doesn't exist
        os.makedirs(dest_folder, exist_ok=True)
        
        # Find Rust installation
        rust_path = find_rust_path()
        files_copied = False
        
        if (rust_path):
            print(f"Found Rust files at: {rust_path}")
            files_copied = copy_files(rust_path, dest_folder)
        else:
            print("Could not find Rust files. Steam or Rust may not be installed.")
        
        # Apply icon - either from local file or downloaded
        if icon_url:
            downloaded = download_icon(icon_url, icon_file)
        else:
            # Copy local icon to destination
            print("Using local icon file...")
            shutil.copy2(icon_path, icon_file)
            downloaded = True
        
        if downloaded:
            icon_applied = apply_icon(dest_folder, icon_file)
        else:
            print("Failed to set up icon")
            icon_applied = False
        
        # Final status
        print("")
        if files_copied:
            print(f"All files copied to: {dest_folder}")
        
        if icon_applied:
            print("Custom icon applied to folder.")
            print("You may need to refresh your desktop to see the icon.")
        
        input("\nPress Enter to exit...")
        
    except Exception as e:
        print(f"An error occurred: {e}")
        input("\nPress Enter to exit...")

if __name__ == "__main__":
    main()