from fastapi import FastAPI
from app.api.calculator import router as calc_router

app = FastAPI(
    title="Next-Level Equation Calculator",
    description="Professional calculator supporting algebra, trig, calculus, matrices with step-by-step solutions",
    version="1.0.0"
)

# Register API router
app.include_router(calc_router)
