ALLOWED = {"1 + 1", "2 + 2"}

def calculate(expression):
    if expression not in ALLOWED:
        raise ValueError("not allowed")
    return eval(expression)
