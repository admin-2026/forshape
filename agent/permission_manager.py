"""
Permission Manager for AI Agent file access and object operations.

This module provides a permission manager that requests and tracks user permissions
for file, directory access, and object deletion during an AI agent session.

Uses WaitManager for GUI interaction, falling back to console prompts
if no manager is provided.
"""

from enum import Enum
from typing import Set, Optional, TYPE_CHECKING
from pathlib import Path

if TYPE_CHECKING:
    from .async_ops import WaitManager


class PermissionResponse(Enum):
    """Response types for permission requests."""
    DENY = 0           # Deny the operation
    ALLOW_ONCE = 1     # Allow this operation only (don't store)
    ALLOW_SESSION = 2  # Allow and store for the entire session


class PermissionManager:
    """
    Manages permissions for file, directory access, and object operations.

    This class tracks granted permissions for the current session and
    requests user approval before allowing file/directory operations and object deletion.

    Uses WaitManager for GUI interaction when available, otherwise
    falls back to console-based prompts.
    """

    def __init__(self, wait_manager: Optional["WaitManager"] = None):
        """
        Initialize the permission manager.

        Args:
            wait_manager: Optional WaitManager for GUI-based permission dialogs.
                         If None, falls back to console prompts.
        """
        self._manager = wait_manager
        self.granted_paths: Set[str] = set()
        self.granted_directories: Set[str] = set()  # Directories with recursive access

    def _request_user_permission(self, resource: str, operation: str) -> PermissionResponse:
        """
        Request permission from user via manager or console.

        Args:
            resource: The resource being accessed
            operation: The operation being performed

        Returns:
            PermissionResponse indicating user's choice
        """
        if self._manager is None:
            return self._console_prompt(resource, operation)

        response = self._manager.permission.request(resource, operation)

        if response.cancelled:
            return PermissionResponse.DENY

        # response.data should be a PermissionResponse enum
        return response.data if response.data else PermissionResponse.DENY

    def _console_prompt(self, resource: str, operation: str) -> PermissionResponse:
        """
        Fallback console-based permission prompt.

        Args:
            resource: The resource being accessed (path or object name)
            operation: The operation being performed (read, write, list, delete_object)

        Returns:
            PermissionResponse indicating the user's choice
        """
        print(f"\n[Permission Request]")
        print(f"Operation: {operation}")
        print(f"Resource: {resource}")
        response = input("Grant permission? (y/n/session): ").strip().lower()

        if response == 'session':
            return PermissionResponse.ALLOW_SESSION
        elif response in ['y', 'yes']:
            return PermissionResponse.ALLOW_ONCE
        else:
            return PermissionResponse.DENY

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
        result = self._request_user_permission(normalized_path, operation)

        # Handle the permission response
        if result == PermissionResponse.ALLOW_SESSION:
            # User selected "Allow for Session" - store the permission
            if is_directory:
                self.granted_directories.add(normalized_path)
            else:
                self.granted_paths.add(normalized_path)
            return True
        elif result == PermissionResponse.ALLOW_ONCE:
            # User selected "Allow Once" - grant permission but don't store
            return True
        else:  # PermissionResponse.DENY
            # User denied permission
            return False

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

    def request_object_deletion_permission(self, object_name: str) -> bool:
        """
        Request permission to delete an object.

        Note: Object deletion permissions are not cached since deletion is a
        one-time operation and the object won't exist afterward.

        Args:
            object_name: Name of the object to delete

        Returns:
            True if permission is granted, False otherwise
        """
        # Always request permission from user (no caching for deletions)
        result = self._request_user_permission(object_name, "delete_object")
        return result in (PermissionResponse.ALLOW_ONCE, PermissionResponse.ALLOW_SESSION)
