from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .database import init_db
from .routes import router

app = FastAPI(
    title="FitBuddy – AI Fitness Plan Generator",
    description=(
        "AI-powered personalized 7-day workout plan generator with "
        "nutrition tips, feedback updates, and SQLite persistence."
    ),
    version="1.0.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.include_router(router)


@app.on_event("startup")
def startup_event():
    init_db()
