"""
Custom exceptions for fedora-desktop-cleaner
"""


class CleanerError(Exception):
    """Base exception for desktop cleaner operations"""
    pass


class BackupError(CleanerError):
    """Exception raised when backup operations fail"""
    pass


class PermissionError(CleanerError):
    """Exception raised when file permissions prevent operation"""
    pass


class ConfigError(CleanerError):
    """Exception raised for configuration-related errors"""
    pass