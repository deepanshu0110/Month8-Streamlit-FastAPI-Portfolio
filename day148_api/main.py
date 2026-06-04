from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import numpy as np
import pandas as pd
import joblib
import os

from . import models
from .database import engine, get_db
from .auth import verify_api_key

# Create tables (idempotent)
models.Base.metadata.create_all(bind=engine)

app = FastAPI(title="FreelanceHub API v2 — DB Edition", version="2.0.0")

# ---------- Helper: Generate / Seed Dataset (same as Section 1) ----------
def _build_dataset() -> pd.DataFrame:
    np.random.seed(141)
    n = 500
    categories      = ['Web Dev', 'Data Science', 'Graphic Design', 'Content Writing', 'SEO']
    experience_lvls = ['Junior', 'Mid', 'Senior']
    payment_types   = ['Fixed', 'Hourly']
    df = pd.DataFrame({
        'project_id':       range(1, n+1),
        'category':         np.random.choice(categories, n),
        'experience_level': np.random.choice(experience_lvls, n),
        'hourly_rate':      np.round(np.random.uniform(5, 80, n), 2),
        'client_rating':    np.where(np.random.rand(n) < 0.08, np.nan,
                                np.round(np.random.uniform(1, 5, n), 1)),
        'bids_received':    np.where(np.random.rand(n) < 0.06, np.nan,
                                np.random.randint(1, 60, n).astype(float)),
        'payment_type':     np.random.choice(payment_types, n),
        'duration_days':    np.where(np.random.rand(n) < 0.05, np.nan,
                                np.random.randint(3, 120, n).astype(float)),
        'status':           np.random.choice(['Completed', 'Cancelled', 'In Progress'],
                                n, p=[0.55, 0.25, 0.20]),
        'platform':         np.random.choice(['Upwork', 'Fiverr', 'Freelancer'], n),
    })
    # Fill NaN
    df['client_rating'] = df['client_rating'].fillna(df['client_rating'].median())
    df['bids_received'] = df['bids_received'].fillna(df['bids_received'].median())
    df['duration_days'] = df['duration_days'].fillna(df['duration_days'].median())
    return df

# ---------- ML Model (Train or Load) ----------
MODEL_PATH = "day148_model.pkl"
ENCODERS_PATH = "day148_encoders.pkl"

def train_model():
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import LabelEncoder

    df = _build_dataset()
    # Encode categorical features
    le_cat = LabelEncoder()
    le_exp = LabelEncoder()
    le_pay = LabelEncoder()
    df['cat_enc'] = le_cat.fit_transform(df['category'])
    df['exp_enc'] = le_exp.fit_transform(df['experience_level'])
    df['pay_enc'] = le_pay.fit_transform(df['payment_type'])

    features = ['hourly_rate', 'client_rating', 'bids_received', 'duration_days',
                'cat_enc', 'exp_enc', 'pay_enc']
    X = df[features]
    y = df['status']   # multi‑class: Completed, Cancelled, In Progress

    model = RandomForestClassifier(n_estimators=100, random_state=141)
    model.fit(X, y)

    # Save model and encoders
    joblib.dump(model, MODEL_PATH)
    joblib.dump({'le_cat': le_cat, 'le_exp': le_exp, 'le_pay': le_pay,
                 'features': features}, ENCODERS_PATH)
    return model, le_cat, le_exp, le_pay, features

if os.path.exists(MODEL_PATH) and os.path.exists(ENCODERS_PATH):
    model = joblib.load(MODEL_PATH)
    encoders = joblib.load(ENCODERS_PATH)
    le_cat = encoders['le_cat']
    le_exp = encoders['le_exp']
    le_pay = encoders['le_pay']
    features = encoders['features']
else:
    model, le_cat, le_exp, le_pay, features = train_model()

# ---------- Pydantic Input Schema (Same as Day 147) ----------
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

# ---------- Background Task: Log Prediction ----------
def log_to_db(db: Session, project_id: int, predicted_status: str, confidence: float):
    log_entry = models.PredictionLog(
        project_id=project_id,
        predicted_status=predicted_status,
        confidence=round(confidence, 4)
    )
    db.add(log_entry)
    db.commit()

# ---------- Endpoints ----------
@app.get("/")
def root():
    return {
        "status": "online",
        "api": "FreelanceHub API v2",
        "endpoints": ["/", "/seed-db", "/projects", "/projects/stats",
                      "/projects/filter", "/predict", "/predictions/log", "/analytics"]
    }

@app.post("/seed-db", dependencies=[Depends(verify_api_key)])
def seed_db(db: Session = Depends(get_db)):
    # Clear existing data
    db.query(models.Project).delete()
    df = _build_dataset()
    projects = []
    for _, row in df.iterrows():
        proj = models.Project(
            project_id=int(row['project_id']),
            category=row['category'],
            experience_level=row['experience_level'],
            hourly_rate=float(row['hourly_rate']),
            client_rating=float(row['client_rating']),
            bids_received=float(row['bids_received']),
            payment_type=row['payment_type'],
            duration_days=float(row['duration_days']),
            status=row['status'],
            platform=row['platform']
        )
        projects.append(proj)
    db.add_all(projects)
    db.commit()
    return {"seeded": len(projects)}

@app.get("/projects", dependencies=[Depends(verify_api_key)])
def get_projects(skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return {"total": db.query(models.Project).count(), "projects": projects}

@app.get("/projects/stats", dependencies=[Depends(verify_api_key)])
def project_stats(db: Session = Depends(get_db)):
    total = db.query(models.Project).count()
    completed = db.query(models.Project).filter(models.Project.status == "Completed").count()
    cancelled = db.query(models.Project).filter(models.Project.status == "Cancelled").count()
    in_progress = db.query(models.Project).filter(models.Project.status == "In Progress").count()
    avg_rate = db.query(func.avg(models.Project.hourly_rate)).scalar() or 0
    high_value_count = db.query(models.Project).filter(models.Project.hourly_rate > 50).count()
    top_platform = db.query(models.Project.platform, func.count(models.Project.id))\
                     .group_by(models.Project.platform)\
                     .order_by(func.count(models.Project.id).desc())\
                     .first()
    return {
        "total_projects": total,
        "completed": completed,
        "cancelled": cancelled,
        "in_progress": in_progress,
        "avg_hourly_rate": round(avg_rate, 2),
        "high_value_count": high_value_count,
        "top_platform": top_platform[0] if top_platform else None
    }

@app.get("/projects/filter", dependencies=[Depends(verify_api_key)])
def filter_projects(status: str = Query(..., regex="^(Completed|Cancelled|In Progress)$"),
                    db: Session = Depends(get_db)):
    results = db.query(models.Project).filter(models.Project.status == status).all()
    return {"count": len(results), "projects": results}

@app.post("/predict")
def predict(project: ProjectInput, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # Encode categoricals
    cat_enc = int(le_cat.transform([project.category])[0])
    exp_enc = int(le_exp.transform([project.experience_level])[0])
    pay_enc = int(le_pay.transform([project.payment_type])[0])
    X = pd.DataFrame([[
        project.hourly_rate,
        project.client_rating,
        project.bids_received,
        project.duration_days,
        cat_enc, exp_enc, pay_enc
    ]], columns=features)
    pred_label = model.predict(X)[0]
    proba = model.predict_proba(X)[0]
    confidence = round(float(max(proba)), 4)
    # Log in background
    background_tasks.add_task(log_to_db, db, 0, pred_label, confidence)  # project_id=0 for on‑the‑fly predictions
    return {
        "prediction": pred_label,
        "confidence": confidence,
        "probabilities": dict(zip(model.classes_, proba.round(4)))
    }

@app.get("/predictions/log", dependencies=[Depends(verify_api_key)])
def get_prediction_logs(db: Session = Depends(get_db)):
    logs = db.query(models.PredictionLog).order_by(models.PredictionLog.created_at.desc()).all()
    return logs

@app.delete("/projects/{project_id}", dependencies=[Depends(verify_api_key)])
def delete_project(project_id: int, role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    if role != "admin":
        raise HTTPException(status_code=403, detail="Admin role required")
    proj = db.query(models.Project).filter(models.Project.project_id == project_id).first()
    if not proj:
        raise HTTPException(status_code=404, detail="Project not found")
    db.delete(proj)
    db.commit()
    return {"deleted": project_id, "status": "removed"}

# ★ Bonus: /analytics endpoint
@app.get("/analytics", dependencies=[Depends(verify_api_key)])
def analytics(db: Session = Depends(get_db)):
    results = db.query(
        models.Project.category,
        func.count(models.Project.id).label("count"),
        func.avg(models.Project.hourly_rate).label("avg_rate"),
        (func.sum((models.Project.status == "Completed").cast("int")) * 100.0 /
         func.count(models.Project.id)).label("completed_pct")
    ).group_by(models.Project.category).all()
    by_category = []
    for row in results:
        by_category.append({
            "category": row.category,
            "count": row.count,
            "avg_rate": round(row.avg_rate, 2) if row.avg_rate else 0,
            "completed_pct": round(row.completed_pct, 1) if row.completed_pct else 0
        })
    return {"by_category": by_category}