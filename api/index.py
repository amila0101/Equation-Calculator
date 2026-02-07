# Vercel serverless entry: all /api/* requests are routed here.
# Export the FastAPI app so Vercel runs it as a single serverless function.
from app.main import app

# Vercel looks for an ASGI app named "app" at this entrypoint
# (Optional, for clarity)
export_app = app
