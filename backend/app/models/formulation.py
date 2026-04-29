from sqlalchemy import Column, Integer, Float, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.database import Base

class TWCFormulation(Base):
    __tablename__ = "twc_formulations"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=True)
    Pt = Column(Float, nullable=False)
    Pd = Column(Float, nullable=False)
    Rh = Column(Float, nullable=False)
    CeO2 = Column(Float, nullable=False)
    ZrO2 = Column(Float, nullable=False)

    co_conv = Column(Float, nullable=True)
    hc_conv = Column(Float, nullable=True)
    nox_conv = Column(Float, nullable=True)
    t50 = Column(Float, nullable=True)

    meets_euro6 = Column(Boolean, default=False)
    fitness_score = Column(Float, nullable=True)
    source = Column(String, default="manual")

    created_at = Column(DateTime(timezone=True), server_default=func.now())
