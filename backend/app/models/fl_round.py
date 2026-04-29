from sqlalchemy import Column, Integer, Float, String, DateTime, JSON
from sqlalchemy.sql import func
from app.database import Base

class FLRound(Base):
    __tablename__ = "fl_rounds"

    id = Column(Integer, primary_key=True, index=True)
    round_number = Column(Integer, nullable=False)
    n_clients = Column(Integer, default=3)
    global_r2 = Column(Float, nullable=True)
    client_results = Column(JSON, nullable=True)
    status = Column(String, default="pending")
    started_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
