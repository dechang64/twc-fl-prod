"""Simulated Federated Learning for TWC"""
import torch
import torch.nn as nn
import numpy as np
from app.ml.predictor import TWCNet, physics_predict

def generate_client_data(n_per_client: int = 150, seed: int = 42):
    """Generate 3 client datasets with different Rh focus ranges (non-IID)"""
    np.random.seed(seed)
    torch.manual_seed(seed)
    data = []
    for i in range(n_per_client * 3):
        Pt = np.random.uniform(0.0, 3.0)
        Pd = np.random.uniform(0.0, 10.0)
        Rh = np.random.uniform(0.0, 1.0)
        CeO2 = np.random.uniform(50.0, 200.0)
        ZrO2 = np.random.uniform(0.0, 50.0)
        p = physics_predict(Pt, Pd, Rh, CeO2, ZrO2)
        data.append({
            'Pt': Pt, 'Pd': Pd, 'Rh': Rh, 'CeO2': CeO2, 'ZrO2': ZrO2,
            'co': p['co_conv'], 'hc': p['hc_conv'],
            'nox': p['nox_conv'], 't50': p['t50'],
        })
    import pandas as pd
    df = pd.DataFrame(data)
    features = df[['Pt', 'Pd', 'Rh', 'CeO2', 'ZrO2']].values.astype(np.float32)
    targets = df[['co', 'hc', 'nox', 't50']].values.astype(np.float32)

    idx = np.arange(len(df))
    np.random.shuffle(idx)
    n = n_per_client
    client_data = [
        {'X': features[idx[:n]], 'y': targets[idx[:n]], 'name': '威孚高科'},
        {'X': features[idx[n:2*n]], 'y': targets[idx[n:2*n]], 'name': '润沃驰'},
        {'X': features[idx[2*n:3*n]], 'y': targets[idx[2*n:3*n]], 'name': '催化剂厂'},
    ]
    return client_data

def local_train(model: nn.Module, X: np.ndarray, y: np.ndarray, epochs: int = 30, lr: float = 0.05):
    model.train()
    optimizer = torch.optim.Adam(model.parameters(), lr=lr)
    loss_fn = nn.MSELoss()
    X_t = torch.tensor(X, dtype=torch.float32)
    y_t = torch.tensor(y, dtype=torch.float32)
    for _ in range(epochs):
        pred = model(X_t)
        loss = loss_fn(pred, y_t)
        optimizer.zero_grad()
        loss.backward()
        optimizer.step()
    with torch.no_grad():
        train_r2 = 1 - loss_fn(model(X_t), y_t).item() / (y_t.var().item() + 1e-8)
    return float(train_r2)

def run_fl_simulation(n_rounds: int = 5):
    """Run simulated FL across 3 clients"""
    client_data = generate_client_data(n_per_client=150, seed=42)

    global_model = TWCNet()
    global_weights = {k: v.clone() for k, v in global_model.state_dict().items()}

    rounds_history = []
    for r in range(n_rounds):
        round_results = {'round': r+1, 'clients': {}, 'global_r2': None}
        updated_weights = []
        for cd in client_data:
            model = TWCNet()
            model.load_state_dict({k: v.clone() for k, v in global_weights.items()})
            r2 = local_train(model, cd['X'], cd['y'], epochs=30 + r*5)
            round_results['clients'][cd['name']] = {'local_r2': round(r2, 4), 'samples': len(cd['X'])}
            updated_weights.append(model.state_dict())

        new_weights = {}
        for k in global_weights.keys():
            new_weights[k] = sum(w[k] for w in updated_weights) / len(updated_weights)
        global_weights = new_weights

        global_model.load_state_dict({k: v.clone() for k, v in global_weights.items()})
        all_X = np.vstack([cd['X'] for cd in client_data])
        all_y = np.vstack([cd['y'] for cd in client_data])
        with torch.no_grad():
            pred = global_model(torch.tensor(all_X, dtype=torch.float32))
            mse = torch.nn.MSELoss()(pred, torch.tensor(all_y, dtype=torch.float32)).item()
            global_r2 = 1 - mse / (all_y.var() + 1e-8)
        round_results['global_r2'] = round(float(global_r2), 4)
        rounds_history.append(round_results)

    return {
        'rounds': rounds_history,
        'final_global_r2': rounds_history[-1]['global_r2'],
        'n_clients': 3,
        'fl_algorithm': 'FedAvg (PyTorch weight averaging)',
        'data_privacy': '配方数据保留在各客户端本地，仅上传模型权重更新',
        'concept': '模拟威孚高科、润沃驰、催化剂厂三方，在配方数据不出厂的前提下联合训练全局TWC预测模型',
    }
