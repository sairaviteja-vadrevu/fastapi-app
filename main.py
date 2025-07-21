"""FastAPI App"""

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.movies import router as movies_router


load_dotenv()

app = FastAPI(
    title="FastAPI App",
    description="A FastAPI application for managing routes",
    version="1.0.0",
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include the routes
app.include_router(movies_router, prefix="/api/v1", tags=["movies"])


@app.get("/")
def read_root():
    """Root endpoint."""
    return {"message": "Welcome to FastAPI!"}
