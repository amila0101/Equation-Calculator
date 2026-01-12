# Equation Calculator

Equation Calculator is a Python-based API built with **FastAPI** and **SymPy** that can solve algebra, calculus, and trigonometry equations. It provides **step-by-step solutions** and returns JSON responses, making it easy to integrate into web or mobile applications.

## Features
- Solve algebraic equations (e.g., x^2 - 4 = 0)
- Compute derivatives and integrals for calculus problems
- Support for trigonometric equations
- Step-by-step solution generation
- Clean JSON API responses for easy integration

## Tech Stack
- Python 3.13+
- FastAPI
- SymPy
- Uvicorn (ASGI server)
- Pydantic (request validation)

## API Example
POST `/api/calc/solve`
```json
{
  "equation": "x**2 - 4",
  "variable": "x",
  "type": "algebra"
}
