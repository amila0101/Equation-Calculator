from fastapi import APIRouter, HTTPException
from app.models.request import EquationRequest
from app.core.validator import validate_equation
from app.core.parser import parse_equation
from app.core.solver import solve_equation
from app.core.steps import generate_steps
import sympy
import math
router = APIRouter(tags=["Calculator"])

@router.post("/solve")
def solve_eq(req: EquationRequest):
    try:
        eq_text = req.equation.strip()

        safe_dict = {
            "math": math,
            "sqrt": math.sqrt,
            "log": math.log10,  # Map 'log' to Base 10 (what most users expect)
            "ln": math.log,
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "pi": math.pi,
            "e": math.e
        }

        # ✅ Arithmetic shortcut (2+3, 5*5 etc.)
        if req.type == "arithmetic":
            try:
                # Replace common math symbols if necessary
                clean_eq = eq_text.replace('x', '*').replace('^', '**').replace('×', '*')
                # Use a literal_eval or a simple eval with restricted globals for safety
                result_value = eval(clean_eq, {"__builtins__": None}, safe_dict)

                result = str(round(result_value, 10))
                steps = [
                    f"Input received: {eq_text}",
                    f"Performing arithmetic operations...",
                    f"Calculation result: {result}"
                ]
                return {
                    "success": True,
                    "result": result,  # React expects a string or list based on your render logic
                    "steps": steps,
                    # ... other fields
                }
            except Exception as e:
                # This helps you see the actual error in the browser console
                raise HTTPException(status_code=400, detail=f"Math Error: {str(e)}")

        # ✅ For algebra, calculus, trig (existing engine)
        validate_equation(eq_text)
        expr = parse_equation(eq_text)
        raw_result = solve_equation(expr, req.variable, req.type)

        # Normalize SymPy objects into JSON‑serializable strings
        if req.type == "algebra":
            # SymPy usually returns a list of solutions
            if isinstance(raw_result, (list, tuple)):
                result = [str(r) for r in raw_result]
            else:
                result = [str(raw_result)]
        elif req.type == "trig":
            # Trig: provide exact and numeric approximations (radians & degrees)
            if isinstance(raw_result, (list, tuple)):
                sols = list(raw_result)
            else:
                sols = [raw_result]

            exact = [str(s) for s in sols]
            approx_rad = []
            approx_deg = []
            for s in sols:
                try:
                    numeric = float(sympy.N(s))
                    approx_rad.append(numeric)
                    approx_deg.append(float(sympy.N(numeric * 180 / sympy.pi)))
                except Exception:
                    # Fallback if SymPy cannot evaluate numerically
                    approx_rad.append(None)
                    approx_deg.append(None)

            result = {
                "exact": exact,
                "approx_rad": approx_rad,
                "approx_deg": approx_deg,
            }
        elif req.type == "calculus":
            # Expect a dict with derivative / integral
            if isinstance(raw_result, dict):
                result = {k: str(v) for k, v in raw_result.items()}
            else:
                result = {"value": str(raw_result)}
        else:
            result = str(raw_result)

        steps = generate_steps(eq_text, result)
        steps = [str(step) for step in steps]

        return {
            "success": True,
            "equation": eq_text,
            "variable": req.variable,
            "type": req.type,
            "result": result,
            "steps": steps
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
