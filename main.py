"""FastAPI App"""

from fastapi import FastAPI
from dotenv import load_dotenv
from routes.movies import router as movies_router


load_dotenv()

app = FastAPI()

# Include the routes
app.include_router(movies_router, prefix="/api/v1", tags=["movies"])


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to FastAPI!"}
