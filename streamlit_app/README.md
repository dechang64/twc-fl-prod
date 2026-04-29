# TWC-FL Platform · Streamlit Cloud 部署指南

## 一、本地运行（Mac/Linux）

```bash
# 1. 克隆仓库
git clone https://github.com/YOUR_USERNAME/twc-fl-platform.git
cd twc-fl-platform

# 2. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate   # Mac/Linux
# venv\Scripts\activate    # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动 FastAPI 后端（在新终端）
cd backend
uvicorn app.main:app --host 0.0.0.0 --port 8000

# 5. 启动 Streamlit（另一个终端）
streamlit run streamlit_app/app.py

# 打开 http://localhost:8501
```

---

## 二、GitHub + Streamlit Cloud 部署（免费）

### 第一步：创建 GitHub 仓库

1. 登录 [GitHub](https://github.com) → 点击右上角 **+** → **New repository**
2. 仓库名称：`twc-fl-platform`
3. 设为 **Private**（可选，不想开源的话）
4. 点击 **Create repository**

### 第二步：推送代码

```bash
cd twc-fl-platform
git init
git add .
git commit -m "TWC-FL Platform v1.0"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/twc-fl-platform.git
git push -u origin main
```

### 第三步：部署到 Streamlit Cloud

1. 打开 [share.streamlit.io](https://share.streamlit.io)
2. 用 **GitHub 账号**登录
3. 点击 **New app**
4. 配置：

| 设置项 | 值 |
|--------|-----|
| Repository | `YOUR_USERNAME/twc-fl-platform` |
| Branch | `main` |
| Main file path | `streamlit_app/app.py` |

5. **Advanced settings** → 添加环境变量：

| Key | Value |
|-----|-------|
| `API_URL` | `https://YOUR-RAILWAY-APP.railway.app`（见下方） |

6. 点击 **Deploy!**

---

## 三、FastAPI 后端部署（免费 · 推荐 Railway）

Streamlit Cloud 不能调用本地 `localhost`，需要把 FastAPI 部署到公网。

### 使用 Railway 部署（每月$5免费额度）

1. 打开 [railway.app](https://railway.app) → 用 GitHub 登录
2. 点击 **New Project** → **Deploy from GitHub repo**
3. 选择 `YOUR_USERNAME/twc-fl-platform`
4. Railway 会自动检测 `backend/` 目录
5. 在 **Settings** 中添加启动命令：

```bash
cd backend && uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

6. Railway 会给一个 URL，例如：`https://twc-fl-api.up.railway.app`
7. 复制这个 URL，填入 Streamlit Cloud 的 `API_URL` 环境变量

### 或者：使用 Render（免费额度）

1. 打开 [render.com](https://render.com) → 用 GitHub 登录
2. **New** → **Web Service**
3. Connect `YOUR_USERNAME/twc-fl-platform`
4. 设置：

| 设置 | 值 |
|------|-----|
| Root Directory | `backend` |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `uvicorn app.main:app --host 0.0.0.0 --port 8000` |

5. 点击 **Deploy** → 得到 `https://twc-fl-api.onrender.com`

---

## 四、目录结构

```
twc-fl-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py           # FastAPI 应用入口
│   │   ├── database.py        # SQLite ORM
│   │   └── ml/
│   │       └── predictor.py   # 物理模型 + Optuna + FedAvg
│   ├── requirements.txt       # fastapi / uvicorn / optuna / ...
│   └── Dockerfile
├── streamlit_app/
│   ├── app.py                 # Streamlit 主程序
│   ├── requirements.txt       # streamlit / requests / plotly
│   └── .streamlit/
│       └── config.toml        # 黑色主题配置
├── docker-compose.yml
└── README.md
```

---

## 五、Streamlit Cloud 部署后的访问

部署完成后，Streamlit Cloud 会给你一个 URL，例如：

```
https://twc-fl-platform.streamlit.app
```

打开即用，支持：
- 🔮 5成分滑块配方预测
- 🚀 Optuna 贝叶斯优化（60 trials）
- 🔄 3方联邦学习 FedAvg 可视化
- 📋 配方库管理

---

## 六、常见问题

**Q: Streamlit Cloud 报错 "ModuleNotFoundError"?**  
A: 确保 `requirements.txt` 在仓库根目录，且 `app.py` 中的 `import` 都能在 `requirements.txt` 中找到。

**Q: API 连不上？**  
A: 检查 `API_URL` 环境变量是否填写正确，是否以 `https://` 开头，不带尾部斜杠。

**Q: 贝叶斯优化跑太久？**  
A: 在 Streamlit 界面选 30 trials，比 60 trials 快一倍。

**Q: 联邦学习按钮点了没反应？**  
A: 检查 FastAPI 后端是否正常运行（`curl https://YOUR-APP.railway.app/api/health`）。
