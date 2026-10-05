from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import joblib

app = FastAPI(
    title="GeoIntelligence AI",
    description="AI-Based Geopolitical Conflict, Escalation & Economic Impact Forecasting",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

try:
    model = joblib.load('ml/conflict_model.pkl')
    print("Conflict Model loaded successfully!")
except Exception as e:
    print(f"Error loading model: {e}")

class ConflictInput(BaseModel):
    recent_events: int
    conflict_intensity: int

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

@app.post("/api/predict_conflict")
def predict_escalation(data: ConflictInput):
    prediction = model.predict([[data.recent_events, data.conflict_intensity]])
    risk_status = "High Escalation Risk" if prediction[0] == 1 else "Normal / Low Risk"
    
    return {
        "recent_events": data.recent_events,
        "conflict_intensity": data.conflict_intensity,
        "escalation_prediction": int(prediction[0]),
        "status": risk_status
    }