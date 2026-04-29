from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os

from app.database import init_db, get_db
from app.models.formulation import TWCFormulation
from app.models.fl_round import FLRound
from app.ml.predictor import predict_twc, compute_fitness, optimize_twc, run_fl_simulation

# ── FastAPI App ──────────────────────────────────────────────────────────────────
app = FastAPI(
    title="TWC-FL Platform API",
    version="1.0.0-PROD",
    description="三元催化配方联邦学习优化平台 · FastAPI + NumPy",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup():
    init_db()
    print("✅ Database initialized")

# ── Schemas ─────────────────────────────────────────────────────────────────────
class FormulationCreate(BaseModel):
    name: Optional[str] = None
    Pt: float; Pd: float; Rh: float; CeO2: float; ZrO2: float

class PredictRequest(BaseModel):
    Pt: float; Pd: float; Rh: float; CeO2: float; ZrO2: float

class OptimizeRequest(BaseModel):
    n_trials: int = 60

class FLRequest(BaseModel):
    n_rounds: int = 5

# ── Routes ──────────────────────────────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "TWC-FL API",
        "version": "1.0.0-PROD",
        "framework": "FastAPI + NumPy + Optuna",
    }

@app.post("/api/formulations")
def create_formulation(data: FormulationCreate, db: Session = Depends(get_db)):
    p = predict_twc(data.Pt, data.Pd, data.Rh, data.CeO2, data.ZrO2)
    fitness = compute_fitness(p['co_conv'], p['hc_conv'], p['nox_conv'], p['t50'])
    meets = p['co_conv'] >= 94 and p['hc_conv'] >= 94 and p['nox_conv'] >= 90
    f = TWCFormulation(
        name=data.name, Pt=data.Pt, Pd=data.Pd, Rh=data.Rh,
        CeO2=data.CeO2, ZrO2=data.ZrO2, source='manual',
        co_conv=p['co_conv'], hc_conv=p['hc_conv'],
        nox_conv=p['nox_conv'], t50=p['t50'],
        meets_euro6=meets, fitness_score=fitness,
    )
    db.add(f); db.commit(); db.refresh(f)
    return {
        "id": f.id, "name": f.name,
        "Pt": f.Pt, "Pd": f.Pd, "Rh": f.Rh,
        "CeO2": f.CeO2, "ZrO2": f.ZrO2,
        "co_conv": f.co_conv, "hc_conv": f.hc_conv,
        "nox_conv": f.nox_conv, "t50": f.t50,
        "meets_euro6": f.meets_euro6,
        "fitness_score": f.fitness_score,
        "source": f.source,
    }

@app.get("/api/formulations", response_model=List[dict])
def list_formulations(db: Session = Depends(get_db)):
    fs = db.query(TWCFormulation).order_by(TWCFormulation.id.desc()).limit(100).all()
    return [
        {"id": f.id, "name": f.name, "Pt": f.Pt, "Pd": f.Pd, "Rh": f.Rh,
         "CeO2": f.CeO2, "ZrO2": f.ZrO2,
         "co_conv": f.co_conv, "hc_conv": f.hc_conv,
         "nox_conv": f.nox_conv, "t50": f.t50,
         "meets_euro6": f.meets_euro6, "fitness_score": f.fitness_score,
         "source": f.source, "created_at": str(f.created_at)}
        for f in fs
    ]

@app.post("/api/predict")
def predict(req: PredictRequest):
    p = predict_twc(req.Pt, req.Pd, req.Rh, req.CeO2, req.ZrO2)
    fitness = compute_fitness(p['co_conv'], p['hc_conv'], p['nox_conv'], p['t50'])
    meets = p['co_conv'] >= 94 and p['hc_conv'] >= 94 and p['nox_conv'] >= 90
    return {
        "predictions": p,
        "meets_euro6": meets,
        "fitness": round(fitness, 4),
    }

@app.post("/api/optimize")
def optimize(req: OptimizeRequest):
    result = optimize_twc(n_trials=req.n_trials)
    return result

@app.get("/api/fl/status")
def fl_status(db: Session = Depends(get_db)):
    rounds = db.query(FLRound).order_by(FLRound.round_number.desc()).limit(10).all()
    return {
        "total_rounds": db.query(FLRound).count(),
        "rounds": [
            {"id": r.id, "round": r.round_number,
             "global_r2": r.global_r2, "status": r.status}
            for r in rounds
        ]
    }

@app.post("/api/fl/rounds")
def run_fl(req: FLRequest, db: Session = Depends(get_db)):
    result = run_fl_simulation(n_rounds=req.n_rounds)
    for rd in result['rounds']:
        fr = FLRound(
            round_number=rd['round'],
            n_clients=3,
            global_r2=rd['global_r2'],
            client_results=rd['clients'],
            status='completed',
            completed_at=datetime.utcnow(),
        )
        db.add(fr)
    db.commit()
    return result

# ── Run ──────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("app.main:app", host="0.0.0.0", port=port, reload=False)
