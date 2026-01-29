"""
Calculator tools for AI Agent.

This module provides mathematical calculation tools
for evaluating arithmetic expressions.
"""

import json
import math
import re
from typing import Dict, List, Callable, Union


from .base import ToolBase


# Regex pattern for valid math expressions
# Allows: numbers, operators (+, -, *, /, **, %), parentheses, decimal points,
# whitespace, and common math functions
MATH_EXPRESSION_PATTERN = re.compile(
    r'^[\d\s\+\-\*\/\%\.\(\)]+$|'  # Basic arithmetic
    r'^[\d\s\+\-\*\/\%\.\(\)]*'    # With optional math functions
    r'(sqrt|pow|abs|sin|cos|tan|log|log10|exp|floor|ceil|round)'
    r'[\d\s\+\-\*\/\%\.\(\)]*$',
    re.IGNORECASE
)

# Stricter pattern: only numbers, basic operators, parentheses, decimal, whitespace
SAFE_MATH_PATTERN = re.compile(r'^[\d\s\+\-\*\/\%\.\(\)\^]+$')


class CalculatorTools(ToolBase):
    """
    Calculator tools for mathematical operations.

    Uses eval with regex validation for expression evaluation.
    """

    def get_definitions(self) -> List[Dict]:
        """Get tool definitions in OpenAI function format."""
        return [
            {
                "type": "function",
                "function": {
                    "name": "calculate",
                    "description": "Evaluate a mathematical expression. Supports basic arithmetic (+, -, *, /, %, **), parentheses, and math functions (sqrt, pow, abs, sin, cos, tan, log, exp, floor, ceil, round).",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "expression": {
                                "type": "string",
                                "description": "The mathematical expression to evaluate. Examples: '2 + 3 * 4', '(10 + 5) / 3', 'sqrt(16)', 'pow(2, 8)'."
                            }
                        },
                        "required": ["expression"]
                    }
                }
            }
        ]

    def get_functions(self) -> Dict[str, Callable[..., str]]:
        """Get mapping of tool names to implementations."""
        return {
            "calculate": self._tool_calculate,
        }

    def get_tool_instructions(self) -> str:
        """Get usage instructions for calculator tools."""
        return """
### Calculator Tools
1. **calculate** - Evaluate mathematical expressions

### Supported Syntax
- Basic arithmetic: +, -, *, /, %, ** (power)
- Parentheses for grouping: (2 + 3) * 4
- Math functions: sqrt(x), pow(x, y), abs(x), sin(x), cos(x), tan(x), log(x), exp(x), floor(x), ceil(x), round(x)

### Calculator Examples

**Calculate 15 + 27:**
> Use calculate with expression="15 + 27"

**Calculate (10 + 5) * 3 / 2:**
> Use calculate with expression="(10 + 5) * 3 / 2"

**Calculate square root of 144:**
> Use calculate with expression="sqrt(144)"

**Calculate 2 to the power of 8:**
> Use calculate with expression="pow(2, 8)" or expression="2 ** 8"
"""

    def _json_error(self, message: str, **kwargs) -> str:
        """Create a JSON error response."""
        response = {"error": message}
        response.update(kwargs)
        return json.dumps(response, indent=2)

    def _json_success(self, result: Union[int, float], expression: str) -> str:
        """Create a JSON success response."""
        response = {
            "success": True,
            "expression": expression,
            "result": result
        }
        return json.dumps(response, indent=2)

    def _is_valid_expression(self, expression: str) -> bool:
        """
        Validate that the expression contains only safe math characters.

        Args:
            expression: The expression to validate

        Returns:
            True if the expression is safe to evaluate
        """
        # Remove allowed math function names for validation
        allowed_functions = [
            'sqrt', 'pow', 'abs', 'sin', 'cos', 'tan',
            'log', 'log10', 'exp', 'floor', 'ceil', 'round', 'pi', 'e'
        ]
        temp_expr = expression.lower()
        for func in allowed_functions:
            temp_expr = temp_expr.replace(func, '')

        # After removing function names, only safe characters should remain
        return bool(SAFE_MATH_PATTERN.match(temp_expr))

    def _tool_calculate(self, expression: str) -> str:
        """
        Implementation of the calculate tool.
        Evaluates a mathematical expression using eval with regex validation.

        Args:
            expression: The mathematical expression to evaluate

        Returns:
            JSON string with result or error message
        """
        try:
            # Validate expression is provided
            if not expression or not isinstance(expression, str):
                return self._json_error("Expression must be a non-empty string")

            expression = expression.strip()
            if not expression:
                return self._json_error("Expression cannot be empty")

            # Validate expression contains only safe characters
            if not self._is_valid_expression(expression):
                return self._json_error(
                    "Invalid expression: contains disallowed characters",
                    expression=expression
                )

            # Replace ^ with ** for power operations
            safe_expression = expression.replace('^', '**')

            # Create a safe namespace with only math functions
            safe_namespace = {
                'sqrt': math.sqrt,
                'pow': math.pow,
                'abs': abs,
                'sin': math.sin,
                'cos': math.cos,
                'tan': math.tan,
                'log': math.log,
                'log10': math.log10,
                'exp': math.exp,
                'floor': math.floor,
                'ceil': math.ceil,
                'round': round,
                'pi': math.pi,
                'e': math.e,
            }

            # Evaluate the expression
            result = eval(safe_expression, {"__builtins__": {}}, safe_namespace)

            return self._json_success(result, expression)

        except ZeroDivisionError:
            return self._json_error("Division by zero", expression=expression)
        except ValueError as e:
            return self._json_error(f"Math error: {str(e)}", expression=expression)
        except SyntaxError:
            return self._json_error("Invalid expression syntax", expression=expression)
        except Exception as e:
            return self._json_error(f"Error evaluating expression: {str(e)}", expression=expression)
