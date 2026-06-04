from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from .database import Base

class Project(Base):
    __tablename__ = "projects"
    id              = Column(Integer, primary_key=True, index=True)
    project_id      = Column(Integer, unique=True, index=True)
    category        = Column(String)
    experience_level= Column(String)
    hourly_rate     = Column(Float)
    client_rating   = Column(Float)
    bids_received   = Column(Float)
    payment_type    = Column(String)
    duration_days   = Column(Float)
    status          = Column(String, index=True)
    platform        = Column(String)

class PredictionLog(Base):
    __tablename__ = "prediction_logs"
    id              = Column(Integer, primary_key=True, index=True)
    project_id      = Column(Integer)
    predicted_status= Column(String)
    confidence      = Column(Float)
    created_at      = Column(DateTime(timezone=True), server_default=func.now())