"""
Fedora Desktop Cleaner

A Python library to clean duplicate desktop applications from Fedora Linux 'Open With' dialogs.
This removes the annoying duplicate entries that appear when right-clicking files.

Main features:
- Removes Wine extension duplicates
- Hides system application duplicates  
- Cleans MIME association duplicates
- Creates automatic backups
- Works universally across Fedora installations

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

__version__ = "1.0.0"
__author__ = "Your Name"
__email__ = "your.email@example.com"

from .cleaner import DesktopDuplicateCleaner
from .exceptions import CleanerError, BackupError

__all__ = [
    'DesktopDuplicateCleaner',
    'CleanerError', 
    'BackupError',
]