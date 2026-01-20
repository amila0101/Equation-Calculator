from sympy import symbols, solve, diff, integrate, sympify

def solve_equation(expr, variable="x", eq_type="algebra"):
    var = symbols(variable)
    
    if eq_type == "algebra":
        solution = solve(expr, var)
        return solution  # SymPy list of solutions
    elif eq_type == "calculus":
        return {
            "derivative": diff(expr, var),
            "integral": integrate(expr, var)
        }
    elif eq_type == "trig":
        solution = solve(expr, var)
        return solution
    else:
        raise ValueError("Unsupported equation type")
