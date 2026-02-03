"""
Step result dataclass for AI agent execution.

This module provides the StepResult class used by all step types.
"""

from dataclasses import dataclass
from typing import Dict, List


@dataclass
class StepResult:
    """Result of a Step execution."""

    response: str
    messages: List[Dict]
    token_usage: Dict
    status: str  # "completed", "cancelled", "max_iterations", "error"
