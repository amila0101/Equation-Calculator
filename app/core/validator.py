def validate_equation(equation):
    if not equation or not isinstance(equation, str):
        raise ValueError("Equation must be a non-empty string")
