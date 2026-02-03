"""
Step result dataclass for AI agent execution.

This module provides the StepResult class used by all step types.
"""

from dataclasses import dataclass


@dataclass
class StepResult:
    """Result of a Step execution."""

    response: str
    messages: list[dict]
    token_usage: dict
    status: str  # "completed", "cancelled", "max_iterations", "error"
