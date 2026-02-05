from fastapi import APIRouter, HTTPException
from app.models.request import EquationRequest
from app.core.validator import validate_equation
from app.core.parser import parse_equation
from app.core.solver import solve_equation
from app.core.steps import generate_steps
import sympy
import math
import re

router = APIRouter(tags=["Calculator"])


def normalize_superscripts(text):
    # Map for digits AND the superscript minus sign
    super_map = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻", "0123456789-")

    # 1. Handle the trig functions specifically first
    text = text.replace("sin⁻¹", "asin").replace("cos⁻¹", "acos").replace("tan⁻¹", "atan")

    # 2. Use the map to convert any remaining individual superscript characters
    return text.translate(super_map)


def parse_vector(vec_str: str) -> list:
    """Parse a vector string like '[3,4]', '{3,4}', or '3,4' into a list of components."""
    vec_str = vec_str.strip().strip('[]{}')
    parts = re.split(r"\s*,\s*", vec_str)
    return [p.strip() for p in parts if p.strip()]


def normalize_vector_brackets(text: str) -> str:
    """Convert curly braces {a,b} to square brackets [a,b] for consistent processing."""
    # Convert {a,b} to [a,b]
    text = re.sub(r'\{([^\}]+)\}', r'[\1]', text)
    return text


def evaluate_vector_expression(text: str) -> str:
    """
    Handle vector addition/subtraction: [a,b]+[c,d] -> [a+c, b+d]
    Also handles: [a,b]-[c,d] -> [a-c, b-d]
    Also handles: {a,b}+{c,d} -> [a+c, b+d] (converts to brackets)
    """
    # First normalize curly braces to square brackets
    text = normalize_vector_brackets(text)
    
    def eval_vector_op(match: re.Match) -> str:
        vec1_str = match.group(1)
        operator = match.group(2)
        vec2_str = match.group(3)
        
        try:
            vec1 = parse_vector(vec1_str)
            vec2 = parse_vector(vec2_str)
            
            if len(vec1) != len(vec2):
                raise ValueError(f"Vectors must have same dimension: {len(vec1)} vs {len(vec2)}")
            
            if operator == '+':
                result = [f"({v1})+({v2})" for v1, v2 in zip(vec1, vec2)]
            elif operator == '-':
                result = [f"({v1})-({v2})" for v1, v2 in zip(vec1, vec2)]
            else:
                return match.group(0)  # Return as-is if unknown operator
            
            return "[" + ",".join(result) + "]"
        except Exception:
            return match.group(0)  # Return original if parsing fails
    
    # Match patterns like [a,b]+[c,d] or [a,b]-[c,d] (after normalization)
    text = re.sub(r'\[([^\]]+)\]\s*([+\-])\s*\[([^\]]+)\]', eval_vector_op, text)
    return text


def expand_vector_norms(text: str) -> str:
    """
    Support vector norm syntax like ||4,5|| or ||x, y, z|| or ||[a,b]+[c,d]|| or ||{a,b}||.
    We convert:
        ||a,b||  -> sqrt((a)**2 + (b)**2)
        ||x,y,z|| -> sqrt((x)**2 + (y)**2 + (z)**2)
        ||[a,b]+[c,d]|| -> sqrt(((a)+(c))**2 + ((b)+(d))**2)
        ||{a,b}|| -> sqrt((a)**2 + (b)**2)
        [a,b] or {a,b} (standalone) -> sqrt((a)**2 + (b)**2)
    This works for both pure numbers and symbolic variables.
    """
    # First normalize curly braces to square brackets
    text = normalize_vector_brackets(text)
    
    def _replace_norm(match: re.Match) -> str:
        inner = match.group(1).strip()
        if not inner:
            return "0"
        
        # Normalize curly braces in inner expression
        inner = normalize_vector_brackets(inner)
        
        # Check if inner contains vector operations like [a,b]+[c,d]
        if '[' in inner and ']' in inner and ('+' in inner or '-' in inner):
            # First evaluate vector operations inside
            inner_evaluated = evaluate_vector_expression(inner)
            
            # Now extract the vector components from the result
            # inner_evaluated should be like [(a)+(c),(b)+(d)] or [a,b]
            vec_match = re.match(r'^\s*\[([^\]]+)\]\s*$', inner_evaluated.strip())
            if vec_match:
                vec_str = vec_match.group(1)
                parts = re.split(r"\s*,\s*", vec_str)
                parts = [p.strip() for p in parts if p.strip()]
                if parts:
                    squared_sum = " + ".join(f"(({p})**2)" for p in parts)
                    return f"sqrt({squared_sum})"
        
        # Check if inner is a vector [a,b] or {a,b}
        vec_match = re.match(r'^\s*\[([^\]]+)\]\s*$', inner.strip())
        if vec_match:
            vec_str = vec_match.group(1)
            parts = re.split(r"\s*,\s*", vec_str)
            parts = [p.strip() for p in parts if p.strip()]
            if parts:
                squared_sum = " + ".join(f"(({p})**2)" for p in parts)
                return f"sqrt({squared_sum})"
        
        # Regular norm: split on comma or whitespace
        parts = re.split(r"\s*,\s*|\s+", inner)
        parts = [p for p in parts if p]
        if not parts:
            return "0"
        
        # Single value ||x|| -> sqrt((x)**2) ~= |x|
        if len(parts) == 1:
            term = parts[0]
            return f"sqrt(({term})**2)"
        
        # Multi-dimensional Euclidean norm
        squared_sum = " + ".join(f"(({p})**2)" for p in parts)
        return f"sqrt({squared_sum})"
    
    # Replace every occurrence of || ... ||
    text = re.sub(r"\|\|([^|]+)\|\|", _replace_norm, text)
    
    # Also handle standalone [a,b] or {a,b} vectors (convert to norm)
    # But only if it's not part of a larger expression (to avoid breaking things)
    text_normalized = normalize_vector_brackets(text)
    if re.match(r'^\s*\[[^\]]+\]\s*$', text_normalized.strip()):
        vec_str = text_normalized.strip().strip('[]')
        parts = re.split(r"\s*,\s*", vec_str)
        parts = [p.strip() for p in parts if p.strip()]
        if parts:
            squared_sum = " + ".join(f"(({p})**2)" for p in parts)
            return f"sqrt({squared_sum})"
    
    return text


@router.post("/solve")
def solve_eq(req: EquationRequest):
    try:
        # Normalize superscripts and then expand any vector norms before further processing
        eq_text = normalize_superscripts(req.equation.strip())
        eq_text = expand_vector_norms(eq_text)

        safe_dict = {
            "math": math,
            "sqrt": math.sqrt,
            "log": math.log10,  # Map 'log' to Base 10 (what most users expect)
            "ln": math.log,
            "sin": lambda x: math.sin(math.radians(x)),
            "cos": lambda x: math.cos(math.radians(x)),
            "tan": lambda x: math.tan(math.radians(x)),
            "asin": lambda x: math.degrees(math.asin(x)),
            "acos": lambda x: math.degrees(math.acos(x)),
            "atan": lambda x: math.degrees(math.atan(x)),
            "pi": math.pi,
            "e": math.e,
            "E": math.e,
            "factorial": math.factorial,
        }

        # ✅ Arithmetic shortcut (2+3, 5*5 etc.)
        if req.type == "arithmetic":
            try:
                # Replace common math symbols if necessary
                normalized = normalize_superscripts(req.equation.strip())
                
                # Check if input has ||...|| norm syntax - expand it first
                if '||' in normalized:
                    normalized = expand_vector_norms(normalized)
                
                # Normalize curly braces to square brackets for consistent processing
                normalized = normalize_vector_brackets(normalized)
                
                # Handle vector operations first (e.g., [3,4]+[1,2] or {3,4}+{1,2})
                # Check if input contains vector notation BEFORE processing
                original_eq = normalized
                has_vectors = ('[' in normalized and ']' in normalized) or ('{' in req.equation and '}' in req.equation)
                
                if has_vectors:
                    # Process vector addition/subtraction
                    normalized = evaluate_vector_expression(normalized)
                    
                    # Now we need to evaluate the vector components properly
                    # normalized might be like [(3)+(1),(4)+(2)] or [4,6]
                    # We need to extract and evaluate each component
                    
                    def extract_and_eval_vector(vec_expr: str) -> list:
                        """Extract vector components and evaluate them."""
                        # Remove outer brackets
                        vec_expr = vec_expr.strip().strip('[]')
                        
                        # Split by comma, but be careful with nested parentheses
                        parts = []
                        current_part = ""
                        paren_depth = 0
                        
                        for char in vec_expr:
                            if char == '(':
                                paren_depth += 1
                                current_part += char
                            elif char == ')':
                                paren_depth -= 1
                                current_part += char
                            elif char == ',' and paren_depth == 0:
                                if current_part.strip():
                                    parts.append(current_part.strip())
                                current_part = ""
                            else:
                                current_part += char
                        
                        if current_part.strip():
                            parts.append(current_part.strip())
                        
                        # Evaluate each component
                        evaluated = []
                        for part in parts:
                            clean_part = part.replace('x', '*').replace('^', '**').replace('×', '*')
                            clean_part = re.sub(r'(\d+)!', r'factorial(\1)', clean_part)
                            try:
                                val = eval(clean_part, {"__builtins__": None}, safe_dict)
                                evaluated.append(float(val))
                            except Exception as e:
                                raise ValueError(f"Could not evaluate vector component '{part}': {str(e)}")
                        
                        return evaluated
                    
                    # Check if the entire expression is a vector (or vector operation result)
                    vec_match = re.match(r'^\s*\[([^\]]+)\]\s*$', normalized.strip())
                    if vec_match:
                        try:
                            vec_components = extract_and_eval_vector(normalized)
                            norm_value = math.sqrt(sum(p**2 for p in vec_components))
                            result = str(round(norm_value, 10))
                            steps = [
                                f"Input received: {req.equation}",
                                f"Vector expression: {normalized}",
                                f"Evaluated vector: {vec_components}",
                                f"Computing norm: sqrt({'+'.join([f'{p:.1f}²' for p in vec_components])})",
                                f"Norm result: {result}"
                            ]
                            return {
                                "success": True,
                                "result": result,
                                "steps": steps,
                            }
                        except Exception as e:
                            raise HTTPException(status_code=400, detail=f"Vector evaluation error: {str(e)}")
                
                # Expand vector norms (for ||...|| syntax)
                normalized = expand_vector_norms(normalized)
                normalized = normalized.replace("sin⁻¹", "asin").replace("cos⁻¹", "acos").replace("tan⁻¹", "atan")

                # USE 'normalized' here, NOT 'eq_text'
                clean_eq = normalized.replace('x', '*').replace('^', '**').replace('×', '*')
                clean_eq = re.sub(r'(\d+)!', r'factorial(\1)', clean_eq)
                clean_eq = re.sub(r'\(([^()]+)\)!', r'factorial(\1)', clean_eq)

                # Now eval() receives standard Python syntax (e.g., 7**4 instead of 7⁴)
                result_value = eval(clean_eq, {"__builtins__": None}, safe_dict)

                result = str(round(result_value, 10))
                steps = [
                    f"Input received: {req.equation}",
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

        #  For algebra, calculus, trig (existing engine)
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
