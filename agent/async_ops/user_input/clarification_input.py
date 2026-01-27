"""
Clarification input provider.

Handles asking questions and collecting text responses from the user.
"""

from typing import Any, Dict, List, Optional

from ..base import UserInputBase, UserInputResponse


class ClarificationInput(UserInputBase):
    """
    Provider for clarification questions.

    Request data: {"questions": ["question1", "question2", ...]}
    Response data: {"responses": {"question1": "answer1", ...}}
    """

    @property
    def type_id(self) -> str:
        return "clarification"

    def request(self, questions: List[str]) -> UserInputResponse:
        """
        Request clarification from user.

        Args:
            questions: List of questions to ask

        Returns:
            Response with data={"responses": {q: answer, ...}}
        """
        return self._do_request({"questions": questions})

    def validate_request_data(self, data: Dict[str, Any]) -> Optional[str]:
        """Validate that questions list is provided and non-empty."""
        questions = data.get("questions")
        if not questions:
            return "questions list is required"
        if not isinstance(questions, list):
            return "questions must be a list"
        if len(questions) == 0:
            return "questions list cannot be empty"
        return None

    def validate_response_data(self, data: Any) -> Optional[str]:
        """Validate that responses dict is provided."""
        if data is None:
            return None  # Cancelled responses have None data
        if not isinstance(data, dict):
            return "response data must be a dictionary"
        if "responses" not in data:
            return "response must contain 'responses' key"
        return None
