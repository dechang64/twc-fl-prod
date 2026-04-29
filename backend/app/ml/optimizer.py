"""Optuna-based Bayesian optimization for TWC formulation"""
import optuna
from app.ml.predictor import predict_twc, compute_fitness

def objective(trial: optuna.Trial) -> float:
    Pt = trial.suggest_float('Pt', 0.0, 3.0)
    Pd = trial.suggest_float('Pd', 0.0, 10.0)
    Rh = trial.suggest_float('Rh', 0.0, 1.0)
    CeO2 = trial.suggest_float('CeO2', 50.0, 200.0)
    ZrO2 = trial.suggest_float('ZrO2', 0.0, 50.0)
    p = predict_twc(Pt, Pd, Rh, CeO2, ZrO2)
    fitness = compute_fitness(p['co_conv'], p['hc_conv'], p['nox_conv'], p['t50'])
    return -fitness

def optimize_twc(n_trials: int = 60, n_jobs: int = 1) -> dict:
    study = optuna.create_study(direction='minimize', sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, n_jobs=n_jobs, show_progress_bar=False)
    best = study.best_trial
    best_params = best.params
    p = predict_twc(**best_params)
    fitness = compute_fitness(p['co_conv'], p['hc_conv'], p['nox_conv'], p['t50'])
    history = [
        {
            'trial_id': t.number,
            'Pt': t.params.get('Pt'),
            'Pd': t.params.get('Pd'),
            'Rh': t.params.get('Rh'),
            'CeO2': t.params.get('CeO2'),
            'ZrO2': t.params.get('ZrO2'),
            'fitness': -t.value,
        }
        for t in study.get_trials()
        if t.value is not None
    ]
    return {
        'best': {**best_params, 'predictions': p, 'fitness': fitness},
        'history': history,
        'n_trials': n_trials,
        'study_name': study.study_name,
    }
