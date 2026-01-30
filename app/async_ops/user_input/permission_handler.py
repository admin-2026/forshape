"""
GUI handler for permission input requests.

Shows a dialog to request file/object operation permissions from the user.
"""

from typing import TYPE_CHECKING

from ..base import GuiInputHandlerBase

if TYPE_CHECKING:
    from agent.async_ops import UserInputRequest


class PermissionHandler(GuiInputHandlerBase):
    """
    Handler for permission input requests.

    Shows a permission dialog and sends the response back via the bridge.
    """

    @property
    def type_id(self) -> str:
        return "permission"

    def handle(self, request: "UserInputRequest") -> None:
        """
        Handle a permission request by showing a dialog.

        Args:
            request: UserInputRequest with data containing resource and operation
        """
        from PySide2.QtWidgets import QMessageBox
        from PySide2.QtCore import Qt
        from agent.permission_manager import PermissionResponse

        resource = request.data.get("resource", "")
        operation = request.data.get("operation", "")

        msg = QMessageBox(self._parent)
        msg.setWindowTitle("Permission Request")
        msg.setWindowFlags(msg.windowFlags() | Qt.WindowStaysOnTopHint)
        msg.setText(f"The AI agent is requesting permission to {operation}.")
        msg.setInformativeText(f"Resource: {resource}")
        msg.setIcon(QMessageBox.Question)

        # Add buttons
        allow_once = msg.addButton("Allow Once", QMessageBox.AcceptRole)
        allow_session = msg.addButton("Allow for Session", QMessageBox.AcceptRole)
        deny = msg.addButton("Deny", QMessageBox.RejectRole)

        msg.exec_()
        clicked = msg.clickedButton()

        if clicked == allow_once:
            result = PermissionResponse.ALLOW_ONCE
            if self._logger:
                self._logger.info(f"Permission granted (once): {operation} on {resource}")
        elif clicked == allow_session:
            result = PermissionResponse.ALLOW_SESSION
            if self._logger:
                self._logger.info(f"Permission granted (session): {operation} on {resource}")
        else:
            result = PermissionResponse.DENY
            if self._logger:
                self._logger.info(f"Permission denied: {operation} on {resource}")

        self._bridge.send_response(request.request_id, data=result)
