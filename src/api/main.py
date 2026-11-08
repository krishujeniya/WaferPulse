"""FastAPI entrypoint for src.api."""

import uvicorn
from backend.app.main import app

__all__ = ["app"]

if __name__ == "__main__":
    uvicorn.run("src.api.main:app", host="0.0.0.0", port=8000, reload=True)
