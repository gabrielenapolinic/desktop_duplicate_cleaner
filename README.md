# Fedora Desktop Cleaner

![GPLv3 Logo](GPLv3_Logo.svg.png)

🧹 **Clean duplicate desktop applications from Fedora Linux 'Open With' dialogs**

[![Python](https://img.shields.io/badge/python-3.6%2B-blue.svg)](https://python.org)
[![License: GPL-3.0](https://img.shields.io/badge/License-GPL%203.0-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Platform](https://img.shields.io/badge/platform-Fedora%20Linux-blue.svg)](https://fedoraproject.org/)

Tired of seeing duplicate applications in your "Open With" dialog? This tool removes the annoying duplicate entries that appear when right-clicking files in Fedora Linux.

## 🎯 Problem Solved

When you right-click a file in Fedora and select "Open With Other Application", you often see:
- Multiple "A Wine application" entries
- Duplicate system applications  
- Same app listed several times
- Confusing, cluttered interface

**This tool fixes all of that!** ✨

## 🚀 Features

- **🍷 Wine Cleanup**: Removes dozens of Wine extension duplicates
- **🎭 Smart Hiding**: Hides system application duplicates intelligently  
- **📄 MIME Cleaning**: Removes duplicate associations from configuration files
- **💾 Safe Operation**: Creates automatic backups before making changes
- **🔍 Dry Run Mode**: Preview changes without modifying anything
- **🌍 Universal**: Works on any Fedora installation regardless of installed apps

## 📦 Installation

### Option 1: Install from PyPI (Recommended)
```bash
pip install fedora-desktop-cleaner
```

### Option 2: Install from Source
```bash
git clone https://github.com/yourusername/fedora-desktop-cleaner.git
cd fedora-desktop-cleaner
pip install .
```

### Option 3: Run Directly
```bash
git clone https://github.com/yourusername/fedora-desktop-cleaner.git
cd fedora-desktop-cleaner
python -m fedora_desktop_cleaner.cli
```

## 🎮 Usage

### Command Line

```bash
# Interactive cleanup (recommended for first use)
fedora-desktop-cleaner

# Preview what would be cleaned (safe)
fedora-desktop-cleaner --dry-run

# Automatic cleanup without prompts
fedora-desktop-cleaner --auto

# Detailed output
fedora-desktop-cleaner --verbose

# Help
fedora-desktop-cleaner --help
```

### Python API

```python
from fedora_desktop_cleaner import DesktopDuplicateCleaner

# Basic usage
cleaner = DesktopDuplicateCleaner()
stats = cleaner.run()
print(f"Removed {stats['wine_files_removed']} Wine duplicates")

# Dry run to preview changes
cleaner = DesktopDuplicateCleaner(dry_run=True, verbose=True)
cleaner.run()

# Get statistics
duplicates = cleaner.find_duplicate_applications()
print(f"Found {len(duplicates)} apps with duplicates")
```

## 🔧 What It Does

### 1. Wine Extension Cleanup
Removes Wine-generated `.desktop` files that create multiple "A Wine application" entries:
- `wine-extension-*.desktop` (zip, rar, pdf, etc.)
- `wine-protocol-*.desktop` 
- Old backup directories with Wine files

### 2. System Duplicate Hiding  
Hides duplicate system applications by creating local overrides:
- Brave Browser (multiple versions)
- Document Viewer duplicates
- Print Preview variants
- And more...

### 3. MIME Association Cleanup
Cleans duplicate entries from:
- `~/.local/share/applications/mimeapps.list`
- `~/.config/mimeapps.list`

### 4. Cache Updates
Refreshes system caches:
- Desktop application database
- MIME type associations

## 📊 Before & After

**Before:**
```
Open With Other Application:
├── A Wine application
├── A Wine application  
├── A Wine application
├── Document Viewer
├── Document Viewer
├── Brave Web Browser
├── Brave Web Browser
└── ...
```

**After:**
```
Open With Other Application:
├── Document Viewer
├── Brave Web Browser  
├── Text Editor
└── ...
```

## ⚙️ Requirements

- **OS**: Fedora Linux (any version)
- **Python**: 3.6 or higher
- **Desktop**: Works with GNOME, KDE, XFCE, etc.
- **Dependencies**: None (uses only Python standard library)

## 🛡️ Safety Features

- **Automatic backups** created before any changes (`.bak` files)
- **Dry run mode** to preview changes safely
- **Non-destructive** - only hides/removes user-specific files
- **Reversible** - backups can be restored if needed
- **Smart detection** - preserves important system files

## 🐛 Troubleshooting

### "Permission denied" errors
The tool only modifies files in your home directory. If you see permission errors, check that you can write to `~/.local/share/applications/`.

### Changes not visible immediately  
Log out and back in, or restart your desktop session for changes to take full effect.

### Want to undo changes?
Restore from automatic backups:
```bash
cd ~/.local/share/applications/
# Find .bak files and restore them
ls *.list.bak
mv mimeapps.list.bak mimeapps.list
```

### Still seeing duplicates?
Run with `--verbose` to see what's being processed:
```bash
fedora-desktop-cleaner --verbose --dry-run
```

## 🤝 Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)  
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Development Setup
```bash
git clone https://github.com/yourusername/fedora-desktop-cleaner.git
cd fedora-desktop-cleaner
python -m venv venv
source venv/bin/activate
pip install -e .
```

## 📋 To-Do

- [ ] Add support for other Linux distributions
- [ ] GUI interface using GTK
- [ ] Whitelist/blacklist configuration
- [ ] Automatic scheduled cleanup
- [ ] Integration with system package managers

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/yourusername/fedora-desktop-cleaner/issues)
- **Discussions**: [GitHub Discussions](https://github.com/yourusername/fedora-desktop-cleaner/discussions)
- **Email**: your.email@example.com

## 📄 License

This project is licensed under the GNU General Public License v3.0 - see the [LICENSE](LICENSE) file for details.

## ⭐ Acknowledgments

- Inspired by the frustration of cluttered "Open With" dialogs
- Built for the Fedora Linux community
- Thanks to all users who report issues and suggest improvements

## 🔗 Related Projects

- [MenuLibre](https://github.com/bluesabre/menulibre) - Menu editor for Linux
- [Alacarte](https://gitlab.gnome.org/GNOME/alacarte) - GNOME menu editor
- [Desktop Entry Specification](https://specifications.freedesktop.org/desktop-entry-spec/) - FreeDesktop.org spec

---

**Made with ❤️ for Fedora Linux users**

*Found this helpful? Give it a ⭐ on GitHub!*