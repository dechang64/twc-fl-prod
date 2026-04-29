# TWC-FL Platform · Production Architecture Spec
## 架构选型：B方案（生产级）

### 技术栈
| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI (Python 3.11) |
| 深度学习 | PyTorch 2.x + 百度AI Studio |
| 联邦学习 | PaddleFL (百度开源FL框架) |
| 数据库 | PostgreSQL 15 + SQLAlchemy 2.x (ORM) |
| 缓存 | Redis 7 |
| 前端 | React 18 + Vite + TypeScript |
| 部署 | Docker + Docker Compose |
| 算法 | 贝叶斯优化 (BoTorch / Optuna) |

### 项目结构
```
/workspace/twc-fl-prod/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # settings (from env)
│   │   ├── database.py          # PostgreSQL + Redis
│   │   ├── models/              # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── formulation.py    # TWCFormulation model
│   │   │   ├── fl_round.py      # FLRound model
│   │   │   └── user.py
│   │   ├── api/                 # API route handlers
│   │   │   ├── __init__.py
│   │   │   ├── formulations.py
│   │   │   ├── predict.py
│   │   │   ├── optimize.py
│   │   │   └── fl.py
│   │   ├── ml/                  # ML modules
│   │   │   ├── __init__.py
│   │   │   ├── predictor.py     # PyTorch TWC predictor
│   │   │   ├── trainer.py      # local training
│   │   │   ├── aggregator.py    # FL weight aggregation
│   │   │   └── optimizer.py    # BoTorch/Optuna
│   │   └── services/            # Business logic
│   │       ├── __init__.py
│   │       └── fl_service.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── main.py                  # uvicorn entry
├── frontend/
│   ├── src/
│   │   ├── pages/ (Dashboard, Formulation, FL, Optimize, Dataset)
│   │   ├── components/ (charts, tables, sliders)
│   │   ├── services/api.ts
│   │   └── App.tsx
│   ├── Dockerfile
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

### API Design
```
POST /api/formulations          # 创建配方
GET  /api/formulations          # 列出配方列表
POST /api/predict               # PyTorch推理
POST /api/optimize              # BoTorch贝叶斯优化
GET  /api/fl/status              # FL当前状态
POST /api/fl/rounds             # 触发一轮FL
GET  /api/fl/rounds/{id}         # 查看FL轮次详情
POST /api/fl/ clients/{id}/train # 客户端本地训练（模拟）
```

### Data Models
```python
# TWCFormulation
id, name, Pt, Pd, Rh, CeO2, ZrO2,
co_conv, hc_conv, nox_conv, t50,  # 实测或预测值
meets_euro6: bool,
fitness_score: float,
created_at, source: str          # 'manual' | 'optimized' | 'fl'

# FLRound
id, round_number, n_clients,
global_model_version, avg_r2,
started_at, completed_at,
client_results: JSON
```

### FL流程设计（真实验）
1. 服务器端广播全局模型参数
2. 各客户端（威孚/润沃驰/催化剂厂）在本地数据训练
3. 只上传梯度/权重更新，不上传原始配方数据
4. 服务器端FedAvg聚合
5. 重复直至收敛

### 贝叶斯优化设计
- 使用Optuna（比scipy更现代，支持GPU加速）
- 目标函数：maximize fitness(Pt, Pd, Rh, CeO2, ZrO2)
- 约束：满足Euro6（CO≥94%, HC≥94%, NOx≥90%）
- 60次trial，目标精度>95%

### 前端设计
- 4个主标签页：配方管理 | 模型推理 | 贝叶斯优化 | 联邦学习
- 实时FL进度可视化（WebSocket推送）
- Euro6合规状态彩色指示器
- 优化历史SVG折线图

### 关键约束
- 数据生成：生成500条物理启发的TWC数据（带真实物理关系）
- 所有API均需CORS配置允许前端访问
- Docker Compose一键启动所有服务
- 后端端口：8000，前端端口：5173
