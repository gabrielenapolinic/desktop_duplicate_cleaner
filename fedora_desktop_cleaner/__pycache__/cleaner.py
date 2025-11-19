"""
Desktop Application Duplicate Cleaner

Core functionality for cleaning duplicate desktop applications.
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict
from typing import Dict, List, Optional
import logging

from .exceptions import CleanerError, BackupError


class DesktopDuplicateCleaner:
    """Main class for cleaning duplicate desktop applications"""
    
    def __init__(self, dry_run: bool = False, verbose: bool = False, logger: Optional[logging.Logger] = None):
        """
        Initialize the cleaner.
        
        Args:
            dry_run: If True, only show what would be done without making changes
            verbose: If True, show detailed logging output
            logger: Optional custom logger instance
        """
        self.dry_run = dry_run
        self.verbose = verbose
        
        # Setup logging
        if logger:
            self.logger = logger
        else:
            self.logger = self._setup_default_logger()
        
        # Standard paths for desktop files
        self.user_apps_dir = Path.home() / ".local/share/applications"
        self.system_apps_dir = Path("/usr/share/applications")
        self.user_mime_file = self.user_apps_dir / "mimeapps.list" 
        self.config_mime_file = Path.home() / ".config/mimeapps.list"
        
        # Ensure user directories exist
        self.user_apps_dir.mkdir(parents=True, exist_ok=True)
        
        # Statistics tracking
        self.stats = {
            'wine_files_removed': 0,
            'duplicates_hidden': 0,
            'mime_duplicates_cleaned': 0,
            'backups_created': 0
        }

    def _setup_default_logger(self) -> logging.Logger:
        """Setup default logging configuration"""
        logger = logging.getLogger(__name__)
        
        # Avoid duplicate handlers
        if logger.handlers:
            return logger
            
        level = logging.DEBUG if self.verbose else logging.INFO
        logger.setLevel(level)
        
        handler = logging.StreamHandler()
        handler.setLevel(level)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        
        logger.addHandler(handler)
        return logger

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
        """
        Parse a .desktop file and extract key information.
        
        Args:
            filepath: Path to the .desktop file
            
        Returns:
            Dictionary with extracted information (name, no_display, type, etc.)
        """
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

    def remove_wine_files(self) -> int:
        """
        Remove Wine extension and protocol files that cause duplicates.
        
        Returns:
            Number of files removed
        """
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
                    try:
                        filepath.unlink()
                        removed_count += 1
                    except OSError as e:
                        self.logger.error(f"Failed to remove {filepath}: {e}")
                else:
                    removed_count += 1
                
        # Also remove backup directories with wine files
        backup_dirs = list(self.user_apps_dir.glob("backup_*"))
        for backup_dir in backup_dirs:
            if backup_dir.is_dir():
                wine_files_in_backup = list(backup_dir.glob("wine-*.desktop"))
                if wine_files_in_backup:
                    self.logger.debug(f"Removing backup directory with wine files: {backup_dir}")
                    if not self.dry_run:
                        try:
                            shutil.rmtree(backup_dir)
                            removed_count += len(wine_files_in_backup)
                        except OSError as e:
                            self.logger.error(f"Failed to remove directory {backup_dir}: {e}")
                    else:
                        removed_count += len(wine_files_in_backup)
        
        self.stats['wine_files_removed'] = removed_count
        self.logger.info(f"Removed {removed_count} Wine-related files")
        return removed_count

    def find_duplicate_applications(self) -> Dict[str, List[Path]]:
        """
        Find applications with duplicate names.
        
        Returns:
            Dictionary mapping application names to lists of duplicate files
        """
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

    def hide_duplicate_applications(self, duplicates: Dict[str, List[Path]]) -> int:
        """
        Hide duplicate applications by creating local overrides.
        
        Args:
            duplicates: Dictionary of duplicate applications from find_duplicate_applications()
            
        Returns:
            Number of duplicates hidden
        """
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
                
                try:
                    # If it's a system file, create a local override
                    if str(duplicate_file).startswith(str(self.system_apps_dir)):
                        local_override = self.user_apps_dir / duplicate_file.name
                        self._create_hide_override(duplicate_file, local_override, app_name)
                        hidden_count += 1
                        
                    # If it's already a user file, modify it directly
                    elif str(duplicate_file).startswith(str(self.user_apps_dir)):
                        self._add_no_display(duplicate_file)
                        hidden_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Failed to hide {duplicate_file}: {e}")
        
        self.stats['duplicates_hidden'] = hidden_count
        self.logger.info(f"Hidden {hidden_count} duplicate applications")
        return hidden_count

    def _create_hide_override(self, system_file: Path, local_file: Path, app_name: str):
        """Create a local .desktop file to hide a system application"""
        if not self.dry_run:
            content = f"""[Desktop Entry]
Type=Application
Name={app_name}
NoDisplay=true
"""
            try:
                with open(local_file, 'w', encoding='utf-8') as f:
                    f.write(content)
            except OSError as e:
                raise CleanerError(f"Failed to create override file {local_file}: {e}")

    def _add_no_display(self, filepath: Path):
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
                
        except OSError as e:
            raise CleanerError(f"Failed to modify {filepath}: {e}")

    def clean_mime_duplicates(self) -> int:
        """
        Clean duplicate entries from mimeapps.list files.
        
        Returns:
            Number of MIME files cleaned
        """
        self.logger.info("📄 Cleaning MIME association duplicates...")
        
        cleaned_count = 0
        mime_files = [self.user_mime_file, self.config_mime_file]
        
        for mime_file in mime_files:
            if mime_file.exists():
                try:
                    if self._clean_mime_file(mime_file):
                        cleaned_count += 1
                except Exception as e:
                    self.logger.error(f"Failed to clean {mime_file}: {e}")
        
        self.stats['mime_duplicates_cleaned'] = cleaned_count
        self.logger.info(f"Cleaned {cleaned_count} MIME files")
        return cleaned_count

    def _clean_mime_file(self, mime_file: Path) -> bool:
        """Clean duplicates from a single mimeapps.list file"""
        try:
            # Create backup
            backup_file = mime_file.with_suffix('.list.bak')
            if not self.dry_run:
                shutil.copy2(mime_file, backup_file)
                self.stats['backups_created'] += 1
                self.logger.debug(f"Backup created: {backup_file}")
            
            # Read and clean content
            with open(mime_file, 'r', encoding='utf-8') as f:
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
                with open(mime_file, 'w', encoding='utf-8') as f:
                    f.write('\n'.join(cleaned_lines))
            
            return True
            
        except OSError as e:
            raise BackupError(f"Failed to clean {mime_file}: {e}")

    def update_caches(self):
        """Update desktop and MIME databases"""
        self.logger.info("🔄 Updating system caches...")
        
        if not self.dry_run:
            # Update desktop database
            result = os.system(f"update-desktop-database {self.user_apps_dir} 2>/dev/null")
            if result != 0:
                self.logger.warning("Failed to update desktop database")
            
            # Update MIME database if it exists
            mime_dir = Path.home() / ".local/share/mime"
            if mime_dir.exists():
                result = os.system(f"update-mime-database {mime_dir} 2>/dev/null")
                if result != 0:
                    self.logger.warning("Failed to update MIME database")

    def get_stats(self) -> Dict[str, int]:
        """Get cleanup statistics"""
        return self.stats.copy()

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

    def run(self) -> Dict[str, int]:
        """
        Execute the complete cleanup process.
        
        Returns:
            Dictionary with cleanup statistics
            
        Raises:
            CleanerError: If cleanup fails
        """
        self.logger.info("🧹 Starting desktop application duplicate cleanup...")
        
        try:
            self.remove_wine_files()
            duplicates = self.find_duplicate_applications()
            self.hide_duplicate_applications(duplicates)
            self.clean_mime_duplicates()
            
            if not self.dry_run:
                self.update_caches()
                
            self.print_summary()
            return self.get_stats()
            
        except Exception as e:
            self.logger.error(f"Cleanup failed: {e}")
            raise CleanerError(f"Cleanup process failed: {e}") from e