from sympy import sympify

def parse_equation(equation_str):
    try:
        expr = sympify(equation_str)
        return expr
    except Exception:
        raise ValueError("Invalid equation format")
