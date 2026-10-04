from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings

app = FastAPI(
    title=settings.APP_NAME,
    description="AI-Based Geopolitical Conflict, Escalation & Economic Impact Forecasting",
    version=settings.APP_VERSION,
)

# Allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "message": "GeoIntelligence AI Backend is running",
        "status": "success"
    }


@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "service": "GeoIntelligence AI"
    }