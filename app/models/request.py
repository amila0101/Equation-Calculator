from pydantic import BaseModel

class EquationRequest(BaseModel):
    equation: str
    variable: str = "x"
    type: str = "algebra"  # algebra, trig, calculus
