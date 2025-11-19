#!/usr/bin/env python3
"""
Desktop Application Duplicate Cleaner for Fedora Linux
Universal script to remove duplicate desktop applications from "Open With" dialogs.

Copyright (C) 2024 Your Name

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import os
import re
import shutil
import glob
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Set, Tuple
import argparse
import logging


class DesktopDuplicateCleaner:
    """Main class for cleaning duplicate desktop applications"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False):
        self.dry_run = dry_run
        self.verbose = verbose
        self.setup_logging()
        
        # Standard paths for desktop files
        self.user_apps_dir = Path.home() / ".local/share/applications"
        self.system_apps_dir = Path("/usr/share/applications")
        self.user_mime_file = self.user_apps_dir / "mimeapps.list" 
        self.config_mime_file = Path.home() / ".config/mimeapps.list"
        
        # Ensure user directories exist
        self.user_apps_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics
        self.stats = {
            'wine_files_removed': 0,
            'duplicates_hidden': 0,
            'mime_duplicates_cleaned': 0,
            'backups_created': 0
        }

    def setup_logging(self):
        """Setup logging configuration"""
        level = logging.DEBUG if self.verbose else logging.INFO
        logging.basicConfig(
            level=level,
            format='%(levelname)s: %(message)s'
        )
        self.logger = logging.getLogger(__name__)

    def find_desktop_files(self) -> List[Path]:
        """Find all .desktop files in system and user directories"""
        desktop_files = []
        
        # System desktop files
        if self.system_apps_dir.exists():
            desktop_files.extend(self.system_apps_dir.glob("*.desktop"))
            
        # User desktop files  
        if self.user_apps_dir.exists():
            desktop_files.extend(self.user_apps_dir.glob("*.desktop"))
            
        return desktop_files

    def parse_desktop_file(self, filepath: Path) -> Dict[str, str]:
        """Parse a .desktop file and extract key information"""
        info = {}
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('Name='):
                        info['name'] = line.split('=', 1)[1]
                    elif line.startswith('NoDisplay='):
                        info['no_display'] = line.split('=', 1)[1].lower() == 'true'
                    elif line.startswith('Type='):
                        info['type'] = line.split('=', 1)[1]
                        
        except Exception as e:
            self.logger.warning(f"Error reading {filepath}: {e}")
            
        return info

    def remove_wine_files(self):
        """Remove Wine extension and protocol files that cause duplicates"""
        self.logger.info("🍷 Removing Wine duplicate files...")
        
        wine_patterns = [
            "wine-extension-*.desktop",
            "wine-protocol-*.desktop"  
        ]
        
        removed_count = 0
        
        for pattern in wine_patterns:
            files = list(self.user_apps_dir.glob(pattern))
            for filepath in files:
                self.logger.debug(f"Removing Wine file: {filepath.name}")
                if not self.dry_run:
                    filepath.unlink()
                removed_count += 1
                
        # Also remove backup directories with wine files
        backup_dirs = list(self.user_apps_dir.glob("backup_*"))
        for backup_dir in backup_dirs:
            if backup_dir.is_dir():
                wine_files_in_backup = list(backup_dir.glob("wine-*.desktop"))
                if wine_files_in_backup:
                    self.logger.debug(f"Removing backup directory with wine files: {backup_dir}")
                    if not self.dry_run:
                        shutil.rmtree(backup_dir)
                    removed_count += len(wine_files_in_backup)
        
        self.stats['wine_files_removed'] = removed_count
        self.logger.info(f"Removed {removed_count} Wine-related files")

    def find_duplicate_applications(self) -> Dict[str, List[Path]]:
        """Find applications with duplicate names"""
        self.logger.info("🔍 Finding duplicate applications...")
        
        name_to_files = defaultdict(list)
        desktop_files = self.find_desktop_files()
        
        for filepath in desktop_files:
            info = self.parse_desktop_file(filepath)
            if 'name' in info and info.get('type') == 'Application':
                # Skip already hidden files
                if not info.get('no_display', False):
                    name_to_files[info['name']].append(filepath)
        
        # Keep only entries with duplicates
        duplicates = {name: files for name, files in name_to_files.items() 
                     if len(files) > 1}
        
        self.logger.info(f"Found {len(duplicates)} applications with duplicates")
        return duplicates

    def hide_duplicate_applications(self, duplicates: Dict[str, List[Path]]):
        """Hide duplicate applications by creating local overrides"""
        self.logger.info("👁️  Hiding duplicate applications...")
        
        hidden_count = 0
        
        for app_name, files in duplicates.items():
            # Sort files: prefer system files over user files as "primary"
            files_sorted = sorted(files, key=lambda f: (
                str(f).startswith(str(self.user_apps_dir)),  # User files last
                str(f)  # Alphabetical within same directory type
            ))
            
            # Keep the first (system) file visible, hide the rest
            primary_file = files_sorted[0]
            duplicate_files = files_sorted[1:]
            
            self.logger.debug(f"App '{app_name}':")
            self.logger.debug(f"  Primary: {primary_file}")
            
            for duplicate_file in duplicate_files:
                self.logger.debug(f"  Hiding: {duplicate_file}")
                
                # If it's a system file, create a local override
                if str(duplicate_file).startswith(str(self.system_apps_dir)):
                    local_override = self.user_apps_dir / duplicate_file.name
                    self.create_hide_override(duplicate_file, local_override, app_name)
                    hidden_count += 1
                    
                # If it's already a user file, modify it directly
                elif str(duplicate_file).startswith(str(self.user_apps_dir)):
                    self.add_no_display(duplicate_file)
                    hidden_count += 1
        
        self.stats['duplicates_hidden'] = hidden_count
        self.logger.info(f"Hidden {hidden_count} duplicate applications")

    def create_hide_override(self, system_file: Path, local_file: Path, app_name: str):
        """Create a local .desktop file to hide a system application"""
        if not self.dry_run:
            content = f"""[Desktop Entry]
Type=Application
Name={app_name}
NoDisplay=true
"""
            with open(local_file, 'w') as f:
                f.write(content)

    def add_no_display(self, filepath: Path):
        """Add NoDisplay=true to an existing desktop file"""
        if self.dry_run:
            return
            
        try:
            # Read current content
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Remove existing NoDisplay lines
            lines = [line for line in lines if not line.strip().startswith('NoDisplay=')]
            
            # Add NoDisplay=true after [Desktop Entry]
            new_lines = []
            added_no_display = False
            
            for line in lines:
                new_lines.append(line)
                if line.strip() == '[Desktop Entry]' and not added_no_display:
                    new_lines.append('NoDisplay=true\n')
                    added_no_display = True
            
            # If no [Desktop Entry] section found, add it
            if not added_no_display:
                new_lines.append('[Desktop Entry]\n')
                new_lines.append('NoDisplay=true\n')
            
            # Write back
            with open(filepath, 'w', encoding='utf-8') as f:
                f.writelines(new_lines)
                
        except Exception as e:
            self.logger.error(f"Error modifying {filepath}: {e}")

    def clean_mime_duplicates(self):
        """Clean duplicate entries from mimeapps.list files"""
        self.logger.info("📄 Cleaning MIME association duplicates...")
        
        cleaned_count = 0
        
        mime_files = [self.user_mime_file, self.config_mime_file]
        
        for mime_file in mime_files:
            if mime_file.exists():
                cleaned_count += self.clean_mime_file(mime_file)
        
        self.stats['mime_duplicates_cleaned'] = cleaned_count
        self.logger.info(f"Cleaned {cleaned_count} MIME files")

    def clean_mime_file(self, mime_file: Path) -> int:
        """Clean duplicates from a single mimeapps.list file"""
        try:
            # Create backup
            backup_file = mime_file.with_suffix('.list.bak')
            if not self.dry_run:
                shutil.copy2(mime_file, backup_file)
                self.stats['backups_created'] += 1
                self.logger.debug(f"Backup created: {backup_file}")
            
            # Read and clean content
            with open(mime_file, 'r') as f:
                content = f.read()
            
            # Remove duplicates from association lines
            lines = content.split('\n')
            cleaned_lines = []
            
            for line in lines:
                if '=' in line and '.desktop' in line:
                    # Extract the key=value part
                    key, value = line.split('=', 1)
                    
                    # Split desktop applications and remove duplicates
                    apps = value.split(';')
                    # Remove empty strings and duplicates while preserving order
                    seen = set()
                    unique_apps = []
                    for app in apps:
                        if app and app not in seen:
                            unique_apps.append(app)
                            seen.add(app)
                    
                    # Rebuild line
                    cleaned_value = ';'.join(unique_apps)
                    if cleaned_value and not cleaned_value.endswith(';'):
                        cleaned_value += ';'
                    
                    cleaned_lines.append(f"{key}={cleaned_value}")
                else:
                    cleaned_lines.append(line)
            
            # Write cleaned content
            if not self.dry_run:
                with open(mime_file, 'w') as f:
                    f.write('\n'.join(cleaned_lines))
            
            return 1
            
        except Exception as e:
            self.logger.error(f"Error cleaning {mime_file}: {e}")
            return 0

    def update_caches(self):
        """Update desktop and MIME databases"""
        self.logger.info("🔄 Updating system caches...")
        
        if not self.dry_run:
            # Update desktop database
            os.system(f"update-desktop-database {self.user_apps_dir} 2>/dev/null")
            
            # Update MIME database if it exists
            mime_dir = Path.home() / ".local/share/mime"
            if mime_dir.exists():
                os.system(f"update-mime-database {mime_dir} 2>/dev/null")

    def print_summary(self):
        """Print operation summary"""
        self.logger.info("\n📊 Operation Summary:")
        self.logger.info(f"   Wine files removed: {self.stats['wine_files_removed']}")
        self.logger.info(f"   Duplicates hidden: {self.stats['duplicates_hidden']}")
        self.logger.info(f"   MIME files cleaned: {self.stats['mime_duplicates_cleaned']}")
        self.logger.info(f"   Backups created: {self.stats['backups_created']}")
        
        if self.dry_run:
            self.logger.info("\n⚠️  DRY RUN MODE - No changes were made")
        else:
            self.logger.info("\n✅ Cleanup completed successfully!")

    def run(self):
        """Execute the complete cleanup process"""
        self.logger.info("🧹 Starting desktop application duplicate cleanup...")
        
        try:
            self.remove_wine_files()
            duplicates = self.find_duplicate_applications()
            self.hide_duplicate_applications(duplicates)
            self.clean_mime_duplicates()
            
            if not self.dry_run:
                self.update_caches()
                
            self.print_summary()
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            raise


def main():
    """Command line interface"""
    parser = argparse.ArgumentParser(
        description="Clean duplicate desktop applications from Fedora Linux 'Open With' dialogs",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                    # Clean duplicates (interactive)
  %(prog)s --dry-run          # Show what would be cleaned
  %(prog)s --verbose          # Detailed output
  %(prog)s --auto             # Clean without confirmation
        """
    )
    
    parser.add_argument(
        '--dry-run', '-n',
        action='store_true',
        help='Show what would be done without making changes'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true', 
        help='Show detailed output'
    )
    
    parser.add_argument(
        '--auto', '-y',
        action='store_true',
        help='Run without confirmation prompt'
    )
    
    args = parser.parse_args()
    
    # Show warning and get confirmation unless --auto is specified
    if not args.auto and not args.dry_run:
        print("⚠️  This script will modify desktop application files.")
        print("   Backups will be created automatically.")
        print("   Continue? (y/N): ", end="")
        
        response = input().lower()
        if response not in ['y', 'yes']:
            print("Operation cancelled.")
            return 1
    
    # Run the cleaner
    cleaner = DesktopDuplicateCleaner(
        dry_run=args.dry_run,
        verbose=args.verbose
    )
    
    try:
        cleaner.run()
        return 0
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit(main())