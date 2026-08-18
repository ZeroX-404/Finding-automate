def calculate(expression: str):
    """Repository-owned fixture for static-analysis acceptance testing."""
    value = expression
    return eval(value)
