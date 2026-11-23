import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from app.db import init_db
from app import seed
from app.templates_api.routes import router as templates_router
from app.analytics.routes import router as analytics_router
from app.feedback.routes import router as feedback_router

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(
    title="AI-Enhanced Phishing Simulation Platform",
    description=(
        "Internal, authorized security-awareness training tool. Generates "
        "AI-personalized phishing-simulation templates, tracks engagement, "
        "and delivers tailored post-click training. Not for use outside "
        "sanctioned, consented internal testing."
    ),
    version="1.0.0",
)

app.mount("/dashboard/static", StaticFiles(directory=str(BASE_DIR / "dashboard" / "static")), name="static")
templates = Jinja2Templates(directory=str(BASE_DIR / "dashboard" / "templates"))

app.include_router(templates_router)
app.include_router(analytics_router)
app.include_router(feedback_router)


@app.on_event("startup")
def on_startup():
    init_db()
    if os.getenv("SEED_DEMO_DATA", "true").lower() == "true":
        seed.run()


@app.get("/")
def dashboard_home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/analytics-view")
def analytics_view(request: Request):
    return templates.TemplateResponse("analytics.html", {"request": request})


@app.get("/health")
def health():
    return {"status": "ok"}
