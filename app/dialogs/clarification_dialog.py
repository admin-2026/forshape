"""
Clarification dialog for AI agent to ask user questions.
"""

from PySide2.QtCore import Qt
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QDialog, QDialogButtonBox, QLabel, QScrollArea, QTextEdit, QVBoxLayout, QWidget


class ClarificationDialog(QDialog):
    """Dialog for AI agent to ask user clarification questions."""

    def __init__(self, questions, parent=None):
        """
        Initialize the clarification dialog.

        Args:
            questions: List of question strings to ask the user
            parent: Parent widget
        """
        super().__init__(parent)
        self.questions = questions if isinstance(questions, list) else [questions]
        self.responses = {}
        self.input_fields = []
        self.setup_ui()

    def setup_ui(self):
        """Setup the dialog UI."""
        self.setWindowTitle("AI Agent Clarification Questions")
        self.setMinimumSize(600, 400)

        # Bring dialog to front
        self.setWindowFlags(self.windowFlags() | Qt.WindowStaysOnTopHint)
        self.raise_()
        self.activateWindow()

        # Main layout
        main_layout = QVBoxLayout(self)

        # Add title label
        title_label = QLabel("Please answer the following questions:")
        title_label.setFont(QFont("Consolas", 11, QFont.Bold))
        main_layout.addWidget(title_label)

        # Create scroll area for questions
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        # Container widget for questions
        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(20)

        # Add question fields
        for i, question in enumerate(self.questions, start=1):
            # Question label
            question_label = QLabel(f"Question {i}:")
            question_label.setFont(QFont("Consolas", 10, QFont.Bold))
            container_layout.addWidget(question_label)

            # Question text
            question_text = QLabel(question)
            question_text.setFont(QFont("Consolas", 9))
            question_text.setWordWrap(True)
            container_layout.addWidget(question_text)

            # Response input (use QTextEdit for multi-line input)
            response_input = QTextEdit()
            response_input.setFont(QFont("Consolas", 9))
            response_input.setPlaceholderText("Type your response here...")
            response_input.setMaximumHeight(100)
            self.input_fields.append(response_input)
            container_layout.addWidget(response_input)

        container_layout.addStretch()
        scroll_area.setWidget(container)
        main_layout.addWidget(scroll_area)

        # Add button box
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.on_ok_clicked)
        button_box.rejected.connect(self.reject)
        main_layout.addWidget(button_box)

    def on_ok_clicked(self):
        """Handle OK button click."""
        # Collect all responses
        for i, (question, input_field) in enumerate(zip(self.questions, self.input_fields)):
            response = input_field.toPlainText().strip()
            self.responses[f"question_{i + 1}"] = {"question": question, "response": response}

        # Check if at least one question has a response
        has_response = any(r["response"] for r in self.responses.values())

        if not has_response:
            # Show warning if no responses provided
            from PySide2.QtWidgets import QMessageBox

            QMessageBox.warning(self, "No Responses", "Please provide at least one response before submitting.")
            return

        self.accept()

    def get_responses(self):
        """
        Return the user's responses.

        Returns:
            Dictionary mapping question identifiers to question/response pairs
        """
        return self.responses
