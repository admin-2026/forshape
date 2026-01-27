"""
Permission input provider.

Handles requesting file/object operation permissions from the user.
"""

from typing import Any, Dict, Optional

from ..base import UserInputBase, UserInputResponse


class PermissionInput(UserInputBase):
    """
    Provider for permission requests.

    Request data: {"resource": "path/or/name", "operation": "read/write/delete_object"}
    Response data: PermissionResponse enum value
    """

    @property
    def type_id(self) -> str:
        return "permission"

    def request(self, resource: str, operation: str) -> UserInputResponse:
        """
        Request permission for an operation.

        Args:
            resource: Path or object being accessed
            operation: Operation type (read, write, delete_object, etc.)

        Returns:
            Response with data=PermissionResponse enum value
        """
        return self._do_request({"resource": resource, "operation": operation})

    def validate_request_data(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate that resource and operation are provided."""
        if "resource" not in data:
            return "resource is required"
        if "operation" not in data:
            return "operation is required"
        return None

    def validate_response_data(self, data: Any) -> Optional[str]:
        """Validate permission response."""
        # PermissionResponse enum is validated by the consumer
        return None
