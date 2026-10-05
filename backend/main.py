from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.config import settings
from backend.routers import (
    economic_router,
    oil_router,
    scenarios_router,
    shipping_router,
)

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

# Register Forecasting and Intelligence Routers
app.include_router(oil_router)
app.include_router(economic_router)
app.include_router(shipping_router)
app.include_router(scenarios_router)


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