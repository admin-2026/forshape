"""
GUI handler for clarification input requests.

Shows a dialog to collect answers to clarification questions from the user.
"""

from typing import TYPE_CHECKING

from ..base import GuiInputHandlerBase

if TYPE_CHECKING:
    from agent.async_ops import UserInputRequest


class ClarificationHandler(GuiInputHandlerBase):
    """
    Handler for clarification input requests.

    Shows a ClarificationDialog and sends responses back via the bridge.
    """

    @property
    def type_id(self) -> str:
        return "clarification"

    def handle(self, request: "UserInputRequest") -> None:
        """
        Handle a clarification request by showing a dialog.

        Args:
            request: UserInputRequest with data containing questions
        """
        from app.dialogs import ClarificationDialog

        questions = request.data.get("questions", [])
        dialog = ClarificationDialog(questions, parent=self._parent)
        result = dialog.exec_()

        if result == ClarificationDialog.Accepted:
            responses = dialog.get_responses()
            if self._logger:
                self._logger.info(f"User clarification response: {responses}")
            self._bridge.send_response(
                request.request_id,
                data={"responses": responses}
            )
        else:
            if self._logger:
                self._logger.info("User cancelled clarification dialog")
            self._bridge.send_response(
                request.request_id,
                cancelled=True
            )
