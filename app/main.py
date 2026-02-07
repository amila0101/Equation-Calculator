from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.calculator import router as calc_router

app = FastAPI(
    title="Equation Calculator API",
    description="Math engine supporting arithmetic, algebra, calculus with step-by-step solutions",
    version="1.0.0"
)

# CORS (for React / frontend)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # allow all for development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register calculator routes
app.include_router(calc_router, prefix="/api/calc")

# Optional: for Vercel serverless entrypoint (api/index.py imports this)
export_app = app

