"""
Permission Manager for AI Agent file access.

This module provides a permission manager that requests and tracks user permissions
for file and directory access during an AI agent session.
"""

from typing import Set, Optional, Callable
from pathlib import Path


class PermissionManager:
    """
    Manages permissions for file and directory access.

    This class tracks granted permissions for the current session and
    requests user approval before allowing file/directory operations.
    """

    def __init__(self, permission_callback: Optional[Callable[[str, str], bool]] = None):
        """
        Initialize the permission manager.

        Args:
            permission_callback: Optional callback function that asks the user for permission.
                                Should accept (path, operation) and return True if granted.
                                If None, a default console-based prompt will be used.
        """
        self.granted_paths: Set[str] = set()
        self.granted_directories: Set[str] = set()  # Directories with recursive access
        self.permission_callback = permission_callback or self._default_permission_callback

    def _default_permission_callback(self, path: str, operation: str) -> bool:
        """
        Default permission callback that prompts via console.

        Args:
            path: The path being accessed
            operation: The operation being performed (read, write, list)

        Returns:
            True if permission is granted, False otherwise
        """
        print(f"\n[Permission Request]")
        print(f"Operation: {operation}")
        print(f"Path: {path}")
        response = input("Grant permission? (y/n/session): ").strip().lower()
        return response in ['y', 'yes', 'session']

    def _normalize_path(self, path: str) -> str:
        """
        Normalize a path for consistent permission checking.

        Args:
            path: Path to normalize

        Returns:
            Normalized path string
        """
        return str(Path(path).resolve())

    def check_permission(self, path: str, operation: str, is_directory: bool = False) -> bool:
        """
        Check if permission is granted for a path and operation.

        Args:
            path: Path to check
            operation: Operation type (read, write, list)
            is_directory: Whether the path is a directory

        Returns:
            True if permission is granted, False otherwise
        """
        normalized_path = self._normalize_path(path)

        # Check if exact path has been granted
        if normalized_path in self.granted_paths:
            return True

        # Check if any parent directory has been granted recursive access
        path_obj = Path(normalized_path)
        for granted_dir in self.granted_directories:
            granted_dir_obj = Path(granted_dir)
            try:
                # Check if the path is within a granted directory
                path_obj.relative_to(granted_dir_obj)
                return True
            except ValueError:
                # Not a subdirectory
                continue

        return False

    def request_permission(self, path: str, operation: str, is_directory: bool = False) -> bool:
        """
        Request permission for a file/directory operation.

        Args:
            path: Path to access
            operation: Operation type (read, write, list)
            is_directory: Whether the path is a directory

        Returns:
            True if permission is granted, False otherwise
        """
        # Check if already granted
        if self.check_permission(path, operation, is_directory):
            return True

        # Request permission from user
        normalized_path = self._normalize_path(path)
        granted = self.permission_callback(normalized_path, operation)

        if granted:
            if is_directory:
                # For directories, grant recursive access
                self.granted_directories.add(normalized_path)
            else:
                # For files, grant specific access
                self.granted_paths.add(normalized_path)

        return granted

    def grant_permission(self, path: str, recursive: bool = False):
        """
        Manually grant permission to a path.

        Args:
            path: Path to grant permission for
            recursive: If True and path is a directory, grant recursive access
        """
        normalized_path = self._normalize_path(path)

        if recursive or Path(path).is_dir():
            self.granted_directories.add(normalized_path)
        else:
            self.granted_paths.add(normalized_path)

    def revoke_permission(self, path: str):
        """
        Revoke permission for a specific path.

        Args:
            path: Path to revoke permission for
        """
        normalized_path = self._normalize_path(path)
        self.granted_paths.discard(normalized_path)
        self.granted_directories.discard(normalized_path)

    def clear_all_permissions(self):
        """Clear all granted permissions."""
        self.granted_paths.clear()
        self.granted_directories.clear()

    def get_granted_permissions(self) -> dict:
        """
        Get all granted permissions.

        Returns:
            Dictionary with 'files' and 'directories' lists
        """
        return {
            "files": list(self.granted_paths),
            "directories": list(self.granted_directories)
        }

    def has_any_permissions(self) -> bool:
        """
        Check if any permissions have been granted.

        Returns:
            True if any permissions exist, False otherwise
        """
        return len(self.granted_paths) > 0 or len(self.granted_directories) > 0
