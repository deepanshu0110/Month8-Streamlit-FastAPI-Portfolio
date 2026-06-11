from fastapi import FastAPI, Depends, HTTPException, Query, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from pydantic import BaseModel, Field, validator
from typing import List, Optional
import pandas as pd
import joblib
import numpy as np

from day149_api import models
from day149_api.database import engine, get_db
from day149_api.auth import verify_api_key

models.Base.metadata.create_all(bind=engine)
app = FastAPI(title="FreelanceHub API v2 — Full Stack", version="2.0.0")

# Load trained model + encoders
model = joblib.load("day149_model.pkl")
encoders = joblib.load("day149_encoders.pkl")
le_platform = encoders['le_platform']
le_skill    = encoders['le_skill']
le_exp      = encoders['le_exp']
le_type     = encoders['le_type']
features    = encoders['features']

# ---------- Helper: generate & seed dataset (500 rows) ----------
def generate_full_dataset():
    np.random.seed(141)
    n = 500
    platforms     = np.random.choice(['Upwork','Freelancer','Fiverr','Toptal'], n, p=[0.35,0.30,0.25,0.10])
    skills        = np.random.choice(['Python','SQL','ML','Tableau','Excel','NLP'], n, p=[0.25,0.20,0.20,0.15,0.10,0.10])
    experience    = np.random.choice(['Junior','Mid','Senior','Expert'], n, p=[0.25,0.35,0.25,0.15])
    project_type  = np.random.choice(['Fixed','Hourly'], n, p=[0.55,0.45])
    hours_billed  = np.random.randint(5, 201, n)
    hourly_rate   = np.round(np.random.uniform(10, 100, n), 2)
    client_rating = np.round(np.random.uniform(2.5, 5.0, n), 1)
    status        = np.random.choice(['Completed','In Progress','Cancelled'], n, p=[0.60,0.25,0.15])
    project_value = np.round(hours_billed * hourly_rate, 2)
    high_value    = (project_value > 5000).astype(int)

    df = pd.DataFrame({
        'project_id'   : range(1, n+1),
        'platform'     : platforms,
        'skill'        : skills,
        'experience'   : experience,
        'project_type' : project_type,
        'hours_billed' : hours_billed,
        'hourly_rate'  : hourly_rate,
        'client_rating': client_rating,
        'status'       : status,
        'project_value': project_value,
        'high_value'   : high_value
    })
    return df

# ---------- Pydantic input for /predict ----------
class ProjectInput(BaseModel):
    platform: str
    skill: str
    experience: str
    project_type: str
    hours_billed: int = Field(..., ge=5, le=200)
    hourly_rate: float = Field(..., ge=10, le=100)
    client_rating: float = Field(..., ge=2.5, le=5.0)

    @validator('platform')
    def validate_platform(cls, v):
        allowed = ['Upwork', 'Freelancer', 'Fiverr', 'Toptal']
        if v not in allowed:
            raise ValueError(f"platform must be one of {allowed}")
        return v
    @validator('skill')
    def validate_skill(cls, v):
        allowed = ['Python', 'SQL', 'ML', 'Tableau', 'Excel', 'NLP']
        if v not in allowed:
            raise ValueError(f"skill must be one of {allowed}")
        return v
    @validator('experience')
    def validate_exp(cls, v):
        allowed = ['Junior', 'Mid', 'Senior', 'Expert']
        if v not in allowed:
            raise ValueError(f"experience must be one of {allowed}")
        return v
    @validator('project_type')
    def validate_type(cls, v):
        allowed = ['Fixed', 'Hourly']
        if v not in allowed:
            raise ValueError(f"project_type must be one of {allowed}")
        return v

# ---------- Background logging ----------
def log_prediction(db: Session, project_id: int, predicted: int, confidence: float):
    log = models.PredictionLog(
        project_id=project_id,
        predicted_high_value=predicted,
        confidence=round(confidence, 4)
    )
    db.add(log)
    db.commit()

# ---------- Health check endpoint (cloud‑required) ----------
@app.get("/health")
def health_check(db: Session = Depends(get_db)):
    try:
        db.execute(text("SELECT 1"))
        return {"status": "healthy", "service": "FreelanceHub API", "version": "1.0.0"}
    except Exception:
        raise HTTPException(
            status_code=503,
            detail={"status": "degraded", "db": "unreachable"}
        )

# ---------- Other endpoints ----------
@app.get("/")
def root():
    return {"status": "online", "api": "FreelanceHub API v2", "endpoints": ["/", "/seed-db", "/projects", "/projects/stats", "/projects/filter", "/projects/platform-summary", "/predict", "/predictions/log", "/analytics"]}

@app.post("/seed-db")
def seed_db(role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    if role != "admin":
        raise HTTPException(403, detail="Admin role required")
    db.query(models.Project).delete()
    df = generate_full_dataset()
    projects = []
    for _, row in df.iterrows():
        p = models.Project(
            project_id=int(row['project_id']),
            platform=row['platform'],
            skill=row['skill'],
            experience=row['experience'],
            project_type=row['project_type'],
            hours_billed=int(row['hours_billed']),
            hourly_rate=float(row['hourly_rate']),
            client_rating=float(row['client_rating']),
            status=row['status'],
            project_value=float(row['project_value']),
            high_value=int(row['high_value'])
        )
        projects.append(p)
    db.add_all(projects)
    db.commit()
    return {"seeded": len(projects)}

@app.get("/projects")
def get_projects(role: str = Depends(verify_api_key), skip: int = 0, limit: int = 50, db: Session = Depends(get_db)):
    projects = db.query(models.Project).offset(skip).limit(limit).all()
    return {"total": db.query(models.Project).count(), "projects": projects}

@app.get("/projects/stats")
def project_stats(role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    total = db.query(models.Project).count()
    completed = db.query(models.Project).filter(models.Project.status == "Completed").count()
    in_progress = db.query(models.Project).filter(models.Project.status == "In Progress").count()
    cancelled = db.query(models.Project).filter(models.Project.status == "Cancelled").count()
    avg_rate = db.query(func.avg(models.Project.hourly_rate)).scalar() or 0
    high_value_count = db.query(models.Project).filter(models.Project.high_value == 1).count()
    top_platform = db.query(models.Project.platform, func.count(models.Project.id))\
                     .group_by(models.Project.platform)\
                     .order_by(func.count(models.Project.id).desc()).first()
    return {
        "total_projects": total,
        "completed": completed,
        "in_progress": in_progress,
        "cancelled": cancelled,
        "avg_hourly_rate": round(avg_rate, 2),
        "high_value_count": high_value_count,
        "top_platform": top_platform[0] if top_platform else None
    }

@app.get("/projects/filter")
def filter_projects(status: str = Query(..., regex="^(Completed|In Progress|Cancelled)$"),
                    role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    results = db.query(models.Project).filter(models.Project.status == status).all()
    return results

@app.get("/projects/platform-summary")
def platform_summary(role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    rows = db.query(
        models.Project.platform,
        func.count(models.Project.id).label("count"),
        func.round(func.avg(models.Project.hourly_rate), 2).label("avg_hourly_rate"),
        func.round(func.avg(models.Project.project_value), 2).label("avg_project_value")
    ).group_by(models.Project.platform).order_by(func.count(models.Project.id).desc()).all()
    return [{"platform": r.platform, "count": r.count,
             "avg_hourly_rate": float(r.avg_hourly_rate),
             "avg_project_value": float(r.avg_project_value)} for r in rows]

@app.post("/predict")
def predict(proj: ProjectInput, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    plat_enc = int(le_platform.transform([proj.platform])[0])
    skill_enc = int(le_skill.transform([proj.skill])[0])
    exp_enc = int(le_exp.transform([proj.experience])[0])
    type_enc = int(le_type.transform([proj.project_type])[0])
    X = pd.DataFrame([[proj.hours_billed, proj.hourly_rate, proj.client_rating,
                       plat_enc, skill_enc, exp_enc, type_enc]], columns=features)
    pred = int(model.predict(X)[0])
    proba = model.predict_proba(X)[0][1]
    background_tasks.add_task(log_prediction, db, 0, pred, proba)
    return {"prediction": pred, "probability": round(proba, 4)}

@app.get("/predictions/log")
def get_logs(role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    return db.query(models.PredictionLog).order_by(models.PredictionLog.created_at.desc()).all()

@app.get("/analytics")
def analytics(role: str = Depends(verify_api_key), db: Session = Depends(get_db)):
    cats = db.query(
        models.Project.skill,
        func.count(models.Project.id).label("count"),
        func.avg(models.Project.project_value).label("avg_value"),
        (func.sum(models.Project.high_value).cast(float) / func.count(models.Project.id) * 100).label("high_value_pct")
    ).group_by(models.Project.skill).all()
    return [{"skill": c.skill, "count": c.count, "avg_value": round(c.avg_value,2),
             "high_value_pct": round(c.high_value_pct,1)} for c in cats]