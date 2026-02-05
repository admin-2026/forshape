"""Parser for extracting constants from Python source files."""

import ast


class ConstantsParser:
    """Parser for extracting and resolving constants from Python source."""

    def __init__(self, content):
        """Initialize the parser with file content.

        Args:
            content: Python file content as string
        """
        self.content = content

    def parse_expressions(self):
        """Parse variable expressions from Python source using AST.

        Returns:
            Dictionary mapping variable names to their source expressions
        """
        expressions = {}
        try:
            tree = ast.parse(self.content)
            for node in ast.iter_child_nodes(tree):
                if isinstance(node, ast.Assign):
                    for target in node.targets:
                        if isinstance(target, ast.Name) and target.id.isupper():
                            name = target.id
                            expression = ast.get_source_segment(self.content, node.value)
                            if expression:
                                expressions[name] = expression
        except SyntaxError:
            pass
        return expressions

    def execute_constants(self, base_namespace=None):
        """Execute Python content and return resolved variable values.

        Args:
            base_namespace: Optional namespace with pre-defined variables (e.g., from constants.py)

        Returns:
            Dictionary of variable names to resolved values
        """
        try:
            # Start with base namespace if provided (for object-specific constants)
            namespace = dict(base_namespace) if base_namespace else {}
            exec(self.content, namespace)

            resolved = {}
            for name, value in namespace.items():
                if name.isupper() and not name.startswith("_"):
                    resolved[name] = str(value)

            return resolved
        except Exception:
            return {}

    def parse_and_resolve(self, base_namespace=None):
        """Parse variables and resolve their values.

        Args:
            base_namespace: Optional namespace with pre-defined variables (e.g., from constants.py)

        Returns:
            List of tuples (name, resolved_value, expression)
        """
        expressions = self.parse_expressions()
        resolved_values = self.execute_constants(base_namespace)

        variables = []
        for name, expression in expressions.items():
            resolved_value = resolved_values.get(name, "N/A")
            variables.append((name, resolved_value, expression))

        return variables
