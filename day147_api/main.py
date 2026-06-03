# day147_api/main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, validator
from typing import List
import pandas as pd
import numpy as np
import joblib
import json

# Load artifacts
model   = joblib.load("day147_api/model.pkl")
le_cat  = joblib.load("day147_api/le_cat.pkl")
le_exp  = joblib.load("day147_api/le_exp.pkl")
le_pay  = joblib.load("day147_api/le_pay.pkl")
le_tgt  = joblib.load("day147_api/le_tgt.pkl")
with open("day147_api/metadata.json") as f:
    META = json.load(f)

FEATURES = META["features"]   # <-- crucial for DataFrame column names

app = FastAPI(title="FreelanceHub Project Status Predictor")

class ProjectInput(BaseModel):
    hourly_rate:      float = Field(..., ge=5.0, le=80.0)
    client_rating:    float = Field(..., ge=1.0, le=5.0)
    bids_received:    float = Field(..., ge=1.0, le=59.0)
    duration_days:    float = Field(..., ge=7.0, le=120.0)
    milestones:       int   = Field(..., ge=1, le=9)
    revision_rounds:  int   = Field(..., ge=0, le=4)
    category:         str
    experience_level: str
    payment_type:     str

    @validator('category')
    def validate_category(cls, v):
        allowed = ['Web Dev', 'Data Science', 'Graphic Design', 'Content Writing', 'SEO']
        if v not in allowed:
            raise ValueError(f"Must be one of {allowed}")
        return v

    @validator('experience_level')
    def validate_experience(cls, v):
        allowed = ['Junior', 'Mid', 'Senior']
        if v not in allowed:
            raise ValueError(f"Must be one of {allowed}")
        return v

    @validator('payment_type')
    def validate_payment(cls, v):
        allowed = ['Fixed', 'Hourly']
        if v not in allowed:
            raise ValueError(f"Must be one of {allowed}")
        return v

class BatchInput(BaseModel):
    projects: List[ProjectInput]

def encode_project(p: ProjectInput) -> pd.DataFrame:
    """Returns a DataFrame with proper column names to silence sklearn warning."""
    data = [[
        p.hourly_rate,
        p.client_rating,
        p.bids_received,
        p.duration_days,
        p.milestones,
        p.revision_rounds,
        int(le_cat.transform([p.category])[0]),
        int(le_exp.transform([p.experience_level])[0]),
        int(le_pay.transform([p.payment_type])[0])
    ]]
    return pd.DataFrame(data, columns=FEATURES)

@app.get("/")
def root():
    return {"status": "online", "api": "FreelanceHub Predictor", "endpoints": ["/", "/model-info", "/predict", "/predict-batch"]}

@app.get("/model-info")
def model_info():
    return {
        "model": META["model"],
        "accuracy": META["accuracy"],
        "training_rows": META["training_rows"],
        "test_rows": META["test_rows"],
        "features": FEATURES,
        "target_classes": META["target_classes"],
        "fill_medians": META["fill_medians"]
    }

@app.post("/predict")
def predict(project: ProjectInput):
    X = encode_project(project)          # now a DataFrame with feature names
    pred_class = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0]
    return {
        "prediction": le_tgt.inverse_transform([pred_class])[0],
        "confidence": round(float(max(proba)), 4),
        "cancelled_prob": round(float(proba[0]), 4),
        "completed_prob": round(float(proba[1]), 4)
    }

@app.post("/predict-batch")
def predict_batch(batch: BatchInput):
    if len(batch.projects) == 0:
        raise HTTPException(status_code=422, detail="Empty projects list")
    if len(batch.projects) > 100:
        raise HTTPException(status_code=422, detail="Maximum 100 projects per batch")
    results = []
    for i, proj in enumerate(batch.projects):
        X = encode_project(proj)
        pred_class = int(model.predict(X)[0])
        proba = model.predict_proba(X)[0]
        results.append({
            "index": i,
            "prediction": le_tgt.inverse_transform([pred_class])[0],
            "confidence": round(float(max(proba)), 4),
            "cancelled_prob": round(float(proba[0]), 4),
            "completed_prob": round(float(proba[1]), 4)
        })
    completed = sum(1 for r in results if r["prediction"] == "Completed")
    return {
        "total": len(results),
        "completed_count": completed,
        "cancelled_count": len(results)-completed,
        "completion_rate": round(completed/len(results), 4),
        "predictions": results
    }