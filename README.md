# TWC-FL Platform

**Three-Way Catalyst Federated Learning Collaboration Platform**

> Privacy-preserving collaborative optimization for automotive catalyst R&D via Federated Learning.

![Streamlit](https://img.shields.io/badge/Streamlit-1.28+-red?logo=streamlit)
![Python](https://img.shields.io/badge/Python-3.9+-blue?logo=python)
![License](https://img.shields.io/badge/License-MIT-green)

---

## Problem

Automotive catalyst manufacturers hold **proprietary formula data** (precious metal loadings, performance metrics) that they cannot share directly. Yet cross-enterprise collaboration is essential to:

- Reduce expensive **Rhodium (Rh)** usage
- Optimize **Pd/Pt/Rh** ratios for emission standards
- Accelerate R&D cycles through shared learning

## Solution

TWC-FL enables **data-free model collaboration** — enterprises train locally, share only model updates, and benefit from collective intelligence without exposing proprietary formulas.

---

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Streamlit Dashboard                   │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐   │
│  │ DataVault│ │Knowledge │ │Bayesian  │ │  Audit   │   │
│  │          │ │  Hub     │ │Optimizer │ │  Chain   │   │
│  └────┬─────┘ └──────────┘ └────┬─────┘ └──────────┘   │
│       │                          │                      │
│       ▼                          ▼                      │
│  ┌─────────────────────────────────────────────┐        │
│  │              FL Engine (FedAvg + DP)         │        │
│  └─────────────────────────────────────────────┘        │
└─────────────────────────────────────────────────────────┘
         │              │              │
    ┌────┴────┐   ┌────┴────┐   ┌────┴────┐
    │Client A │   │Client B │   │Client C │
    │(Local)  │   │(Local)  │   │(Local)  │
    └─────────┘   └─────────┘   └─────────┘
```

## Modules

### 💾 DataVault — Formula Data Management

Secure storage and management of catalyst formula data.

| Feature | Description |
|---------|-------------|
| Multi-format import | CSV, Excel, JSON |
| Quality report | Outlier detection, missing fields, distribution stats |
| Similarity search | Find similar formulations by composition |
| Anonymization | Gaussian noise injection for FL participation |
| Export | Pandas DataFrame, CSV download |

```python
from twc_fl import DataVault

vault = DataVault(":memory:")
vault.add_formula(
    {"Pt": 1.5, "Pd": 2.0, "Rh": 0.1},
    {"CO_conv": 95.0, "HC_conv": 93.0, "NOx_conv": 90.0}
)
report = vault.quality_report()
anon = vault.anonymize(seed=42, noise_scale=0.5)
```

### 🎯 BayesianOptimizer — Formula Optimization

Gaussian Process surrogate model with Expected Improvement acquisition function.

| Feature | Description |
|---------|-------------|
| GP surrogate | Kernel-based regression on historical data |
| EI acquisition | Balance exploration vs exploitation |
| Constraint support | Bound individual metal loadings |
| Active learning | Iteratively improve with experiment feedback |

```python
from twc_fl import BayesianOptimizer

opt = BayesianOptimizer()
opt.add_single_observation(
    {"Pt": 1.5, "Pd": 2.0, "Rh": 0.1},
    {"NOx_conv": 90.0}
)
result = opt.recommend_candidates("NOx_conv", "maximize", top_k=5)
for cand in result.candidates:
    print(cand.composition, cand.predicted_performance)
```

### 🌐 FLEngine — Federated Learning

Pure NumPy FedAvg implementation with Differential Privacy.

| Feature | Description |
|---------|-------------|
| FedAvg aggregation | Weighted average by sample count |
| Differential Privacy | Laplace mechanism with configurable ε |
| Convergence tracking | Per-round loss, delta, client participation |
| Multi-client simulation | Configurable clients with varying data quality |

```python
from twc_fl import FLEngine, FLClient, FLConfig

config = FLConfig(dp_epsilon=10.0, learning_rate=0.01)
engine = FLEngine(config)
engine.add_client(FLClient("c1", "Enterprise A", num_samples=200))
engine.add_client(FLClient("c2", "Enterprise B", num_samples=150))

history = engine.run_simulation(num_rounds=10)
```

### 📚 KnowledgeHub — Domain Knowledge

Built-in TWC industry knowledge base with 20 FAQs and literature references.

| Category | Topics |
|----------|--------|
| `formulation` | Pd/Rh ratios, OSC materials, washcoat optimization |
| `aging` | Thermal degradation, poisoning, regeneration |
| `regulation` | Euro 6/7, China VI, EPA standards |
| `fl` | Federated learning for catalyst R&D |
| `general` | TWC fundamentals, testing methods |

```python
from twc_fl import KnowledgeHub

hub = KnowledgeHub()
results = hub.search("how to reduce Rh loading")
refs = hub.recommend_literature("Pd Rh catalyst")
```

### 🔗 AuditChain — Blockchain Audit

SHA-256 hash chain for tamper-proof audit trail.

| Feature | Description |
|---------|-------------|
| Hash chaining | Each entry links to previous via SHA-256 |
| Tamper detection | Verify chain integrity at any time |
| Query & filter | Search by action type, actor, time range |
| Export | JSON, CSV, Pandas DataFrame |

```python
from twc_fl import AuditChain

chain = AuditChain()
chain.append("data_import", "user", {"count": 100})
chain.append("fl_round", "system", {"round": 1})
assert chain.verify_chain()  # True
```

---

## Quick Start

### Deploy to Streamlit Cloud

1. **Clone this repo**
   ```bash
   git clone https://github.com/KaRROB/TWC-FL-Platform.git
   cd TWC-FL-Platform
   ```

2. **Project structure**
   ```
   TWC-FL-Platform/
   ├── requirements.txt
   └── streamlitapp/
       ├── app.py              # Streamlit entry point
       └── twc_fl/             # Python package
           ├── __init__.py
           ├── data_vault.py
           ├── knowledge_hub.py
           ├── bayesian_optimizer.py
           ├── fl_engine.py
           └── audit_chain.py
   ```

3. **Push to GitHub** and connect to [Streamlit Cloud](https://streamlit.io/cloud)

4. Set the entry point to `streamlitapp/app.py`

### Run Locally

```bash
pip install -r requirements.txt
cd streamlitapp
streamlit run app.py
```

**Dependencies:**
- `streamlit >= 1.28.0`
- `numpy >= 1.24.0`
- `pandas >= 2.0.0`

> No PyTorch, TensorFlow, or heavy ML frameworks required. Pure NumPy.

---

## Dashboard Tabs

| Tab | Description |
|-----|-------------|
| 📊 Overview | Platform architecture & module guide |
| 💾 Data Vault | Add formulas, quality report, similarity search, anonymization |
| 📚 Knowledge Hub | FAQ search, literature recommendations, category browsing |
| 🎯 Bayesian Optimizer | Recommend candidate formulas, submit experiment feedback |
| 🌐 FL Engine | Run federated training, convergence curves, client management |
| 🔗 Audit Chain | View audit log, verify chain integrity, export data |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Backend | Pure Python (3.9+) |
| Math | NumPy only — no PyTorch/TF |
| UI | Streamlit |
| Privacy | Laplace DP mechanism |
| Optimization | GP + Expected Improvement |
| Audit | SHA-256 hash chain |

---

## License

MIT
