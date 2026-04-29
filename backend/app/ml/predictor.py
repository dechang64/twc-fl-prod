"""
TWC-FL ML Module
Physics-based TWC predictor + Optuna Bayesian optimization + NumPy FedAvg simulation
"""
import numpy as np

def physics_predict(Pt, Pd, Rh, CeO2, ZrO2):
    co  = min(100.0, max(70.0, 85  + 4.5*Pt  + 2.1*Pd - 0.05*CeO2 + 0.02*ZrO2))
    hc  = min(100.0, max(70.0, 80  + 2.0*Pt  + 5.5*Pd - 1.0*Rh  - 0.03*CeO2 + 0.03*ZrO2))
    nox = min(100.0, max(50.0, 70  - 8.0*Pt  - 3.0*Pd + 60.0*Rh  - 0.02*CeO2 + 0.01*ZrO2))
    t50 = max(120.0, min(280.0, 280 - 60*Pt   - 25*Pd  - 80*Rh   + 0.1*CeO2  - 0.2*ZrO2 ))
    return {'co_conv': round(co, 2), 'hc_conv': round(hc, 2),
            'nox_conv': round(nox, 2), 't50': round(t50, 2)}


def compute_fitness(co, hc, nox, t50):
    f_co  = co  if co  >= 94 else co  * 0.5
    f_hc  = hc  if hc  >= 94 else hc  * 0.5
    f_nox = nox if nox >= 90 else nox * 0.5
    f_t50 = max(0.0, 200 - t50) if t50 <= 220 else 0.0
    return 0.30*f_co + 0.25*f_hc + 0.30*f_nox + 0.15*f_t50


def predict_twc(Pt, Pd, Rh, CeO2, ZrO2):
    return physics_predict(float(Pt), float(Pd), float(Rh), float(CeO2), float(ZrO2))


def optimize_twc(n_trials=60):
    import optuna
    optuna.logging.set_verbosity(optuna.logging.WARNING)

    def objective(trial):
        Pt   = trial.suggest_float('Pt',   0.0, 3.0)
        Pd   = trial.suggest_float('Pd',   0.0, 10.0)
        Rh   = trial.suggest_float('Rh',   0.0, 1.0)
        CeO2 = trial.suggest_float('CeO2', 50.0, 200.0)
        ZrO2 = trial.suggest_float('ZrO2', 0.0, 50.0)
        p = physics_predict(Pt, Pd, Rh, CeO2, ZrO2)
        return -compute_fitness(p['co_conv'], p['hc_conv'], p['nox_conv'], p['t50'])

    study = optuna.create_study(direction='minimize',
                               sampler=optuna.samplers.TPESampler(seed=42))
    study.optimize(objective, n_trials=n_trials, show_progress_bar=False)

    best = study.best_trial
    bp = best.params
    p = physics_predict(bp['Pt'], bp['Pd'], bp['Rh'], bp['CeO2'], bp['ZrO2'])
    fitness = compute_fitness(p['co_conv'], p['hc_conv'], p['nox_conv'], p['t50'])

    history = [
        {'trial_id': t.number,
         'Pt': t.params.get('Pt'), 'Pd': t.params.get('Pd'),
         'Rh': t.params.get('Rh'), 'CeO2': t.params.get('CeO2'), 'ZrO2': t.params.get('ZrO2'),
         'fitness': round(-t.value, 4)}
        for t in study.get_trials() if t.value is not None
    ]

    return {
        'best': {**bp, 'predictions': p, 'fitness': round(fitness, 4)},
        'history': history,
        'n_trials': n_trials,
    }


def run_fl_simulation(n_rounds=5):
    rng = np.random.default_rng(42)

    def gen_data(n, Rh_lo, Rh_hi):
        X_list, y_list = [], []
        for _ in range(n):
            Pt   = rng.uniform(0.0, 3.0)
            Pd   = rng.uniform(0.0, 10.0)
            Rh   = rng.uniform(Rh_lo, Rh_hi)
            CeO2 = rng.uniform(50.0, 200.0)
            ZrO2 = rng.uniform(0.0, 50.0)
            p = physics_predict(Pt, Pd, Rh, CeO2, ZrO2)
            X_list.append([Pt/3, Pd/10, Rh, CeO2/200, ZrO2/50])
            y_list.append(p['co_conv'])
        return np.array(X_list, dtype=np.float64), np.array(y_list, dtype=np.float64)

    # Client 1: 威孚高科, Rh in [0, 0.33]
    c1_X, c1_y = gen_data(150, 0.0, 0.33)
    # Client 2: 润沃驰, Rh in [0.33, 0.67]
    c2_X, c2_y = gen_data(150, 0.33, 0.67)
    # Client 3: 催化剂厂, Rh in [0.67, 1.0]
    c3_X, c3_y = gen_data(150, 0.67, 1.0)

    clients = [
        {'X': c1_X, 'y': c1_y, 'name': '威孚高科'},
        {'X': c2_X, 'y': c2_y, 'name': '润沃驰'},
        {'X': c3_X, 'y': c3_y, 'name': '催化剂厂'},
    ]

    # Global normalization
    all_X = np.vstack([c['X'] for c in clients])
    all_y = np.concatenate([c['y'] for c in clients])
    mean_x, std_x = all_X.mean(axis=0), all_X.std(axis=0) + 1e-8
    mean_y, std_y = all_y.mean(), all_y.std() + 1e-8
    for cd in clients:
        cd['X_n'] = (cd['X'] - mean_x) / std_x
        cd['y_n'] = (cd['y'] - mean_y) / std_y

    # Init global linear model: y = X @ w + b
    w = np.zeros(5)
    b = 0.0

    rounds_history = []
    for r in range(n_rounds):
        lr = 0.05
        local_updates = []
        local_r2s = {}

        for cd in clients:
            X_n, y_n = cd['X_n'], cd['y_n']
            n_samples = len(X_n)
            w_local, b_local = w.copy(), float(b)

            # Local SGD
            idx_arr = rng.choice(n_samples, size=min(30 + r*5, n_samples), replace=False)
            for idx_i in idx_arr:
                x_i, y_i = X_n[idx_i], y_n[idx_i]
                pred = float(x_i @ w_local + b_local)
                err = pred - y_i
                w_local = w_local - lr * err * x_i
                b_local = b_local - lr * err

            # Local R²
            preds_n = X_n @ w_local + b_local
            ss_res = np.sum((preds_n - y_n)**2)
            ss_tot = np.sum((y_n - y_n.mean())**2)
            r2 = 1 - ss_res / (ss_tot + 1e-8)

            local_updates.append((w_local, b_local, n_samples))
            local_r2s[cd['name']] = {'local_r2': round(float(r2), 4), 'samples': int(n_samples)}

        # FedAvg
        total = sum(s for _, _, s in local_updates)
        w = sum(w_i * n_i for w_i, _, n_i in local_updates) / total
        b = sum(b_i * n_i for _, b_i, n_i in local_updates) / total

        # Global R²
        preds_n = all_X @ w + b
        preds = preds_n * std_y + mean_y
        ss_res = np.sum((preds - all_y)**2)
        ss_tot = np.sum((all_y - all_y.mean())**2)
        global_r2 = 1 - ss_res / (ss_tot + 1e-8)

        rounds_history.append({
            'round': r + 1,
            'clients': local_r2s,
            'global_r2': round(float(global_r2), 4),
        })

    return {
        'rounds': rounds_history,
        'final_global_r2': rounds_history[-1]['global_r2'],
        'n_clients': 3,
        'fl_algorithm': 'FedAvg (Linear Regression + SGD)',
        'data_privacy': '配方数据保留在各客户端本地，仅上传模型参数（权重/偏置）',
        'concept': ('模拟威孚高科、润沃驰、催化剂厂三方，在配方数据不出厂'
                    '（Data Never Leaves）的前提下，通过 FedAvg 算法联合训练全局 TWC CO转化率预测模型'),
    }
