"""
TWC-FL Platform · Streamlit App
三元催化配方联邦学习优化平台
"""
import streamlit as st
import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# ── Config ──────────────────────────────────────────────────────────────────
API_URL = "http://localhost:8000"
st.set_page_config(
    page_title="TWC-FL Platform",
    page_icon="⚗️",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ── Helpers ─────────────────────────────────────────────────────────────────
@st.cache_data(ttl=300)
def health_check():
    try:
        r = requests.get(f"{API_URL}/api/health", timeout=5)
        return r.json() if r.ok else None
    except Exception:
        return None


@st.cache_data(ttl=60)
def call_predict(Pt, Pd, Rh, CeO2, ZrO2):
    r = requests.post(
        f"{API_URL}/api/predict",
        json={"Pt": Pt, "Pd": Pd, "Rh": Rh, "CeO2": CeO2, "ZrO2": ZrO2},
        timeout=30,
    )
    return r.json() if r.ok else None


@st.cache_data(ttl=300)
def call_optimize(n_trials=60):
    r = requests.post(
        f"{API_URL}/api/optimize",
        json={"n_trials": n_trials},
        timeout=120,
    )
    return r.json() if r.ok else None


@st.cache_data(ttl=300)
def call_fl(n_rounds=5):
    r = requests.post(
        f"{API_URL}/api/fl/rounds",
        json={"n_rounds": n_rounds},
        timeout=60,
    )
    return r.json() if r.ok else None


@st.cache_data(ttl=120)
def list_formulations():
    r = requests.get(f"{API_URL}/api/formulations", timeout=10)
    return r.json() if r.ok else []


def euro6_bar(val: float, threshold: float, label: str):
    pct = min(100, val / threshold * 100)
    ok = val >= threshold
    color = "#22c55e" if ok else "#ef4444"
    st.markdown(f"""
    <div style="margin-bottom:4px">
        <span style="font-size:13px; font-weight:600; width:48px; display:inline-block">{label}</span>
        <span style="font-size:13px; color:{color}; font-weight:700; margin-left:8px">{val:.2f}{'%' if 'conv' in label.lower() else '°C'}</span>
        <div style="background:#1a1d27; border-radius:4px; height:8px; margin-top:2px">
            <div style="width:{pct:.1f}%; background:{color}; border-radius:4px; height:100%; transition:width 0.5s"></div>
        </div>
    </div>
    """, unsafe_allow_html=True)


# ── Styles ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
.stDeployButton {display:none !important}
footer {visibility: hidden !important}
[data-testid="stToolbar"] {display:none !important}
[class="stStatusWidget"] {display:none !important}
.block-container {padding-top: 1rem !important}
header[data-testid="stHeader"] {display:none !important}
.st-emotion-cache-1g2w5ys {padding: 0 !important}
.stTabs > div:first-child {background: #1a1d27; border-radius: 12px; padding: 4px;}
.stTabs button {border-radius: 8px !important; font-size: 14px !important; font-weight: 600 !important; padding: 8px 20px !important;}
.stTabs button[aria-selected="true"] {background: #8b5cf6 !important; color: white !important;}
.stMetric {background: #1a1d27 !important; border-radius: 10px !important; padding: 16px !important; border: 1px solid #2d3142 !important;}
.stMetricValue {color: #e2e8f0 !important; font-weight: 800 !important;}
.stMetricLabel {color: #64748b !important;}
.stButton > button {border-radius: 8px !important; font-weight: 600 !important; height: 38px !important; transition: opacity 0.2s;}
.stButton > button:hover {opacity: 0.85 !important;}
.stSlider > div > div > div {color: #8b5cf6 !important;}
</style>
""", unsafe_allow_html=True)

# ── Header ─────────────────────────────────────────────────────────────────
col_logo, col_title, col_badge = st.columns([1, 8, 3])

with col_logo:
    st.markdown("""
    <div style="font-size:2.5rem; text-align:center; line-height:1">⚗️</div>
    """, unsafe_allow_html=True)

with col_title:
    st.markdown("""
    <div style="font-size:1.4rem; font-weight:800; color:#e2e8f0; line-height:1.2">
    TWC-FL Platform
    </div>
    <div style="font-size:0.82rem; color:#64748b; margin-top:4px">
    三元催化配方 · 联邦学习优化平台
    </div>
    """, unsafe_allow_html=True)

with col_badge:
    health = health_check()
    if health:
        st.success(f"🟢 API: {health.get('version', '1.0')}")
    else:
        st.error("🔴 API离线")

# ── Main ───────────────────────────────────────────────────────────────────
st.divider()
tabs = st.tabs([
    "🔮 **配方预测**",
    "🚀 **贝叶斯优化**",
    "🔄 **联邦学习**",
    "📋 **配方库**",
])

# ── Tab 1: 配方预测 ──────────────────────────────────────────────────────
with tabs[0]:
    st.markdown("### 🔮 PyTorch 配方预测")

    col_in, col_out = st.columns([1, 1.4])

    with col_in:
        st.markdown("**配方输入**")
        with st.container():
            Pt = st.slider("Pt (g/L) · 铂", 0.0, 3.0, 1.5, 0.05, help="铂含量 — 主要影响CO转化率")
            Pd = st.slider("Pd (g/L) · 钯", 0.0, 10.0, 5.0, 0.1, help="钯含量 — 主要影响HC转化率")
            Rh = st.slider("Rh (g/L) · 铑", 0.0, 1.0, 0.3, 0.01, help="铑含量 — 决定NOx转化率，最贵")
            CeO2 = st.slider("CeO₂ (g/L) · 铈", 50.0, 200.0, 100.0, 1.0)
            ZrO2 = st.slider("ZrO₂ (g/L) · 锆", 0.0, 50.0, 20.0, 1.0)
            name = st.text_input("配方名称（可选）", placeholder="如：Demo-A1")

        submitted = st.button("⚡ 运行预测", type="primary", use_container_width=True)

    with col_out:
        st.markdown("**预测结果**")
        if submitted or "pred" in st.session_state:
            if submitted:
                result = call_predict(Pt, Pd, Rh, CeO2, ZrO2)
                if result:
                    st.session_state["pred"] = result
                else:
                    st.error("❌ 预测失败，请检查后端服务")
                    result = None
            else:
                result = st.session_state.get("pred")

            if result:
                p = result["predictions"]
                m6 = result["meets_euro6"]
                fitness = result.get("fitness", 0)

                # Euro6 bars
                st.markdown("**Euro6 合规状态**")
                euro6_bar(p["co_conv"], 94, "CO")
                euro6_bar(p["hc_conv"], 94, "HC")
                euro6_bar(p["nox_conv"], 90, "NOx")
                euro6_bar(p["t50"], 200, "T50")

                # Status
                if m6:
                    st.success(f"✅ 满足 Euro6 排放标准  |  Fitness: **{fitness:.2f}**")
                else:
                    st.warning(f"⚠️ 不满足 Euro6 排放标准  |  Fitness: **{fitness:.2f}**")

                # Details
                with st.expander("📊 详细数据"):
                    c1, c2, c3, c4 = st.columns(4)
                    items = [("CO", f"{p['co_conv']:.2f}%", p['co_conv'] >= 94),
                             ("HC", f"{p['hc_conv']:.2f}%", p['hc_conv'] >= 94),
                             ("NOx", f"{p['nox_conv']:.2f}%", p['nox_conv'] >= 90),
                             ("T50", f"{p['t50']:.1f}°C", p['t50'] <= 200)]
                    for c, (lbl, val, ok) in zip([c1,c2,c3,c4], items):
                        c.metric(lbl, val,
                                 delta="✓" if ok else "✗",
                                 help=f"{'满足' if ok else '不满足'} Euro6")

                # Physics vs NN
                with st.expander("🧠 PyTorch vs 物理方程对比"):
                    phys = {
                        "CO": 85 + 4.5*Pt + 2.1*Pd - 0.05*CeO2 + 0.02*ZrO2,
                        "HC": 80 + 2.0*Pt + 5.5*Pd - 1.0*Rh - 0.03*CeO2 + 0.03*ZrO2,
                        "NOx": 70 - 8.0*Pt - 3.0*Pd + 60.0*Rh - 0.02*CeO2 + 0.01*ZrO2,
                        "T50": 280 - 60*Pt - 25*Pd - 80*Rh + 0.1*CeO2 - 0.2*ZrO2,
                    }
                    comp_df = pd.DataFrame({
                        "指标": ["CO转化率", "HC转化率", "NOx转化率", "T50温度"],
                        "PyTorch NN": [p["co_conv"], p["hc_conv"], p["nox_conv"], p["t50"]],
                        "物理方程": [round(phys["CO"],2), round(phys["HC"],2), round(phys["NOx"],2), round(phys["T50"],2)],
                    })
                    comp_df["差异"] = abs(comp_df["PyTorch NN"] - comp_df["物理方程"]).round(2)
                    st.dataframe(comp_df, use_container_width=True, hide_index=True)

    # Model arch info
    with st.expander("ℹ️ TWCNet 模型架构"):
        st.markdown("""
        | 属性 | 值 |
        |------|-----|
        | 框架 | **PyTorch 2.2** |
        | 网络结构 | 5 → 64 → 64 → 4 |
        | 激活函数 | ReLU |
        | 输出维度 | [CO%, HC%, NOx%, T50°C] |
        | 推理策略 | PyTorch NN + 物理方程 50/50 加权融合 |
        """)
        st.markdown("**Euro6 排放标准阈值：** CO≥94% | HC≥94% | NOx≥90% | T50≤200°C")


# ── Tab 2: 贝叶斯优化 ─────────────────────────────────────────────────────
with tabs[1]:
    st.markdown("### 🚀 Optuna 贝叶斯优化")

    st.info("""
    使用 **Optuna TPE**（Tree-structured Parzen Estimator）采样器，在 5 维配方空间搜索满足 Euro6 约束的最优配方。
    目标：最大化 fitness score，同时满足 CO≥94%、HC≥94%、NOx≥90%。
    """)

    col_trial, col_btn = st.columns([1, 4])
    with col_trial:
        n_trials = st.selectbox("优化强度", [30, 60, 100], index=1, help="Trial数量越多结果越好，但耗时更长")

    optimize_clicked = st.button("🚀 启动优化", type="primary", use_container_width=True)

    if optimize_clicked:
        with st.spinner(f"Optuna {n_trials} trials 运行中，预计需要30~90秒…"):
            result = call_optimize(n_trials)

        if result:
            best = result["best"]
            history = result.get("history", [])

            st.success(f"✅ 优化完成！最优配方 fitness: **{best.get('fitness', 0):.2f}**")

            # Best formulation
            st.markdown("**最优配方**")
            bc1, bc2, bc3, bc4, bc5 = st.columns(5)
            for c, (lbl, val, unit) in zip(
                [bc1, bc2, bc3, bc4, bc5],
                [("Pt", best.get("Pt", 0), "g/L"), ("Pd", best.get("Pd", 0), "g/L"),
                          ("Rh", best.get("Rh", 0), "g/L"), ("CeO₂", best.get("CeO2", 0), "g/L"),
                          ("ZrO₂", best.get("ZrO2", 0), "g/L")]
            ):
                c.metric(lbl, f"{val:.3f}" if lbl in ["Pt","Rh"] else f"{val:.1f}", unit)

            p = best.get("predictions", {})
            euro6_bar(p.get("co_conv", 0), 94, "CO")
            euro6_bar(p.get("hc_conv", 0), 94, "HC")
            euro6_bar(p.get("nox_conv", 0), 90, "NOx")

            m6_ok = p.get("co_conv",0)>=94 and p.get("hc_conv",0)>=94 and p.get("nox_conv",0)>=90
            st.success("✅ Euro6 全部通过" if m6_ok else "⚠️ 部分指标未达标")

            # Convergence chart
            if history and len(history) > 1:
                st.markdown("**优化收敛曲线**")
                df_h = pd.DataFrame(history)
                df_h = df_h.dropna(subset=["fitness"])
                df_h["trial_id"] = range(1, len(df_h)+1)

                fig = px.line(
                    df_h, x="trial_id", y="fitness",
                    title=f"Fitness 收敛曲线 ({len(df_h)} trials)",
                    labels={"fitness": "Fitness ↑", "trial_id": "Trial"},
                    color_discrete_sequence=["#8b5cf6"],
                )
                fig.update_layout(
                    plot_bgcolor="#1a1d27",
                    paper_bgcolor="#0f1117",
                    font_color="#e2e8f0",
                    margin=dict(l=40, r=20, t=50, b=40),
                )
                fig.update_traces(fill="tozeroy", fillcolor="rgba(139,92,246,0.15)", line_width=2)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.error("❌ 优化失败，请检查后端服务")

    st.markdown("""
    ---
    **贝叶斯优化原理：**  
    1. 用随机搜索 warmup（10 trials）建立初始观测  
    2. TPE 根据历史结果构建概率代理模型（surrogate model）  
    3. Expected Improvement (EI) 准则选择下一个候选点  
    4. 重复直至收敛，比随机搜索快 3~5 倍
    """)


# ── Tab 3: 联邦学习 ─────────────────────────────────────────────────────
with tabs[2]:
    st.markdown("### 🔄 联邦学习模拟 (FedAvg)")

    st.info("""
    模拟三家催化剂企业（**威孚高科、润沃驰、催化剂厂**）在配方数据不出厂（Data Never Leaves）的前提下，
    通过 **FedAvg（Federated Averaging）** 算法联合训练全局 TWC 预测模型。
    """)

    # Architecture diagram
    with st.expander("🏗️ 联邦学习架构"):
        st.markdown("""
        ```
        ┌─────────────────┐    权重更新     ┌─────────────────┐
        │   Client-A       │ ←────────────→  │   Server         │
        │  (威孚高科)       │    (梯度聚合)    │  (协调方)        │
        │  本地数据训练     │                 │  全局模型聚合     │
        └─────────────────┘                 └─────────────────┘
                ↑                                        ↑
        ┌─────────────────┐    权重更新     │  FedAvg: W = Σ w_i / n
        │   Client-B       │ ←─────────────┘
        │  (润沃驰)         │
        └─────────────────┘
                ↑
        ┌─────────────────┐
        │   Client-C       │
        │  (催化剂厂)       │
        └─────────────────┘

        配方数据始终保留在各企业内部，不上传到服务器
        ```
        """)

    col_rounds, col_start = st.columns([1, 4])
    with col_rounds:
        n_rounds = st.slider("FL 轮次", 3, 10, 5)

    fl_clicked = st.button("🔄 运行联邦学习", type="primary", use_container_width=True)

    if fl_clicked:
        with st.spinner("FL 训练中，请稍候…"):
            result = call_fl(n_rounds)

        if result:
            rounds = result.get("rounds", [])
            final_r2 = result.get("final_global_r2", 0)
            clients = result.get("n_clients", 3)

            st.success(
                f"✅ 完成 {clients} 家机构 · {len(rounds)} 轮训练 · "
                f"最终全局 R² = **{final_r2:.4f}**"
            )

            # FL Results table
            st.markdown("**各轮次结果**")
            table_data = []
            for r in rounds:
                row = {"Round": f"Round {r['round']}"}
                if r.get("clients"):
                    for name, v in r["clients"].items():
                        row[name] = f"{v.get('local_r2', 0):.4f}"
                row["全局 R²"] = f"**{r.get('global_r2', 0):.4f}**"
                table_data.append(row)

            if table_data:
                df_fl = pd.DataFrame(table_data)
                st.dataframe(df_fl, use_container_width=True, hide_index=True)

            # Convergence chart
            if rounds:
                st.markdown("**全局 R² 收敛曲线**")
                df_r2 = pd.DataFrame([
                    {"Round": r["round"], "全局R²": r.get("global_r2", 0)}
                    for r in rounds
                ])
                fig = go.Figure()
                fig.add_trace(go.Scatter(
                    x=df_r2["Round"], y=df_r2["全局R²"],
                    mode="lines+markers",
                    marker=dict(size=8, color="#34d399"),
                    line=dict(color="#34d399", width=2.5),
                    fill="tozeroy",
                    fillcolor="rgba(52,211,153,0.1)",
                ))
                fig.update_layout(
                    plot_bgcolor="#1a1d27",
                    paper_bgcolor="#0f1117",
                    font_color="#e2e8f0",
                    yaxis=dict(range=[0, 1.05], title="R² Score"),
                    xaxis=dict(title="FL Round"),
                    margin=dict(l=40, r=20, t=30, b=40),
                    height=300,
                )
                st.plotly_chart(fig, use_container_width=True)

            # Privacy note
            st.caption(
                f"🔒 数据隐私保证：配方数据始终保留在各企业内部。"
                f"仅上传模型权重更新（梯度）。"
                f"算法：{result.get('fl_algorithm', 'FedAvg')}"
            )


# ── Tab 4: 配方库 ────────────────────────────────────────────────────────
with tabs[3]:
    st.markdown("### 📋 已保存配方库")

    if st.button("🔄 刷新"):
        st.rerun()

    try:
        formulations = list_formulations()
        if formulations and len(formulations) > 0:
            df = pd.DataFrame(formulations)
            df["Euro6"] = df.apply(
                lambda r: "✅" if (r.get("co_conv",0)>=94 and r.get("hc_conv",0)>=94 and r.get("nox_conv",0)>=90) else "❌",
                axis=1
            )
            st.dataframe(
                df[["id","name","Pt","Pd","Rh","CeO2","ZrO2","co_conv","hc_conv","nox_conv","t50","fitness_score","Euro6"]],
                use_container_width=True,
                hide_index=True,
            )
        else:
            st.info("暂无配方数据，去「配方预测」页面创建配方吧！")
    except Exception as e:
        st.warning(f"无法加载配方库：{e}")

# ── Footer ────────────────────────────────────────────────────────────────
st.divider()
st.caption(
    "TWC-FL Platform v1.0 · 苏州市社科联课题 J2025LX005 · "
    "技术栈: FastAPI + PyTorch + Optuna + Streamlit"
)
