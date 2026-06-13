from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Project(Base):
    __tablename__ = "projects"
    id              = Column(Integer, primary_key=True, index=True)
    project_id      = Column(Integer, unique=True, index=True)
    platform        = Column(String)
    skill           = Column(String)
    experience      = Column(String)
    project_type    = Column(String)
    hours_billed    = Column(Integer)
    hourly_rate     = Column(Float)
    client_rating   = Column(Float)
    status          = Column(String, index=True)
    project_value   = Column(Float)
    high_value      = Column(Integer)   # 1 if project_value > 5000 else 0

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id              = Column(Integer, primary_key=True, index=True)
    project_id      = Column(Integer)
    predicted_high_value = Column(Integer)
    confidence      = Column(Float)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())