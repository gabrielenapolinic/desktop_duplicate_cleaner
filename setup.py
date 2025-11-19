#!/usr/bin/env python3
"""
Setup configuration for fedora-desktop-cleaner
"""

from setuptools import setup, find_packages
import os

# Read README for long description
def read_readme():
    readme_path = os.path.join(os.path.dirname(__file__), 'README.md')
    if os.path.exists(readme_path):
        with open(readme_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""

setup(
    name="fedora-desktop-cleaner",
    version="1.0.0",
    author="Your Name",
    author_email="your.email@example.com",
    description="Clean duplicate desktop applications from Fedora Linux 'Open With' dialogs",
    long_description=read_readme(),
    long_description_content_type="text/markdown",
    url="https://github.com/yourusername/fedora-desktop-cleaner",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: End Users/Desktop",
        "Topic :: System :: Systems Administration",
        "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.6",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Operating System :: POSIX :: Linux",
    ],
    python_requires=">=3.6",
    install_requires=[
        # No external dependencies - uses only standard library
    ],
    entry_points={
        "console_scripts": [
            "fedora-desktop-cleaner=fedora_desktop_cleaner.cli:main",
        ],
    },
    keywords="fedora linux desktop applications duplicates gnome kde",
    project_urls={
        "Bug Reports": "https://github.com/yourusername/fedora-desktop-cleaner/issues",
        "Source": "https://github.com/yourusername/fedora-desktop-cleaner",
        "Documentation": "https://github.com/yourusername/fedora-desktop-cleaner#readme",
    },
)