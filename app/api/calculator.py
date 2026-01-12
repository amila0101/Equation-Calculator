from fastapi import APIRouter, HTTPException
from app.models.request import EquationRequest
from app.core.validator import validate_equation
from app.core.parser import parse_equation
from app.core.solver import solve_equation
from app.core.steps import generate_steps
from sympy import Basic  # For type checking SymPy objects

router = APIRouter(prefix="/api/calc", tags=["Calculator"])

def sympy_to_string(obj):
    """
    Convert SymPy objects to string recursively for JSON.
    """
    if isinstance(obj, dict):
        return {k: sympy_to_string(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sympy_to_string(v) for v in obj]
    elif isinstance(obj, Basic):  # SymPy object
        return str(obj)
    else:
        return obj

@router.post("/solve")
def solve_eq(req: EquationRequest):
    try:
        # 1️⃣ Validate input equation
        validate_equation(req.equation)

        # 2️⃣ Parse equation string -> SymPy expression
        expr = parse_equation(req.equation)

        # 3️⃣ Solve equation
        result = solve_equation(expr, req.variable, req.type)

        # 4️⃣ Generate steps
        steps = generate_steps(req.equation, result)
        steps = [str(step) for step in steps]

        # 5️⃣ Convert all SymPy results to string for JSON
        result = sympy_to_string(result)

        # 6️⃣ Return final JSON
        return {
            "success": True,
            "equation": req.equation,
            "variable": req.variable,
            "type": req.type,
            "result": result,
            "steps": steps
        }

    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Internal Server Error: {str(e)}")
