from fastapi import APIRouter, HTTPException
from app.models.request import EquationRequest
from app.core.validator import validate_equation
from app.core.parser import parse_equation
from app.core.solver import solve_equation
from app.core.steps import generate_steps
import sympy

router = APIRouter(prefix="/api/calc", tags=["Calculator"])

@router.post("/solve")
def solve_eq(req: EquationRequest):
    try:
        eq_text = req.equation.strip()

        # ✅ Arithmetic shortcut (2+3, 5*5 etc.)
        if req.type == "arithmetic":
            try:
                result = str(eval(eq_text))  # safe for simple numbers
                steps = [f"Equation received: {eq_text}", f"Solving equation gives: {result}", "Steps generation complete"]
                return {
                    "success": True,
                    "equation": eq_text,
                    "variable": req.variable,
                    "type": req.type,
                    "result": [result],
                    "steps": steps
                }
            except Exception as e:
                raise HTTPException(status_code=400, detail=f"Arithmetic error: {str(e)}")

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
