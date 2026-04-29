import React from 'react'
import { useState } from 'react'
import './App.css'
import { api } from './services/api'

type Tab = 'formulations' | 'inference' | 'optimize' | 'fl'
type FormState = { Pt: number; Pd: number; Rh: number; CeO2: number; ZrO2: number; name: string }

interface PredResult {
  formulation: Record<string, number>
  predictions: Record<string, number>
  meets_euro6: boolean
  fitness: number
}

interface OptResult {
  best: { Pt: number; Pd: number; Rh: number; CeO2: number; ZrO2: number; predictions: Record<string, number>; fitness: number }
  history: Array<{ trial_id: number; fitness: number }>
  n_trials: number
}

interface FLResult {
  rounds: Array<{ round: number; clients: Record<string, { local_r2: number }>; global_r2: number }>
  final_global_r2: number
  fl_algorithm: string
  data_privacy: string
  concept: string
}

function Euro6Bar({ label, value, threshold }: { label: string; value: number; threshold: number }) {
  const pct = Math.min(100, (value / (threshold * 1.2)) * 100)
  const pass = value >= threshold
  return (
    <div className="euro6-row">
      <span className="euro6-label">{label}</span>
      <div className="euro6-bar-wrap">
        <div className={`euro6-bar ${pass ? 'pass' : 'fail'}`} style={{ width: `${pct}%` }} />
      </div>
      <span className="euro6-val" style={{ color: pass ? 'var(--success)' : 'var(--danger)' }}>
        {value.toFixed(1)}%
      </span>
    </div>
  )
}

function FitnessChart({ history }: { history: Array<{ trial_id: number; fitness: number }> }) {
  if (!history.length) return null
  const W = 800, H = 180, padL = 40, padR = 20, padT = 10, padB = 30
  const fits = history.map(h => h.fitness)
  const minF = Math.min(...fits) * 0.95
  const maxF = Math.max(...fits) * 1.05
  const x = (i: number) => padL + (i / (history.length - 1 || 1)) * (W - padL - padR)
  const y = (f: number) => padT + (1 - (f - minF) / (maxF - minF || 1)) * (H - padT - padB)
  const path = history.map((h, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(h.fitness)}`).join(' ')
  const areaPath = path + ` L${x(history.length - 1)},${H - padB} L${padL},${H - padB} Z`
  const bestIdx = history.reduce((bi, h, i) => h.fitness > history[bi].fitness ? i : bi, 0)
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" preserveAspectRatio="none">
      <defs>
        <linearGradient id="fitGrad" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="#8b5cf6" stopOpacity="0.3" />
          <stop offset="100%" stopColor="#8b5cf6" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.25, 0.5, 0.75, 1].map((t) => {
        const fy = padT + (1 - t) * (H - padT - padB)
        const fval = minF + t * (maxF - minF)
        return (
          <g key={t}>
            <line x1={padL} y1={fy} x2={W - padR} y2={fy} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
            <text x={padL - 6} y={fy + 4} textAnchor="end" fontSize="10" fill="var(--text-muted)">{fval.toFixed(0)}</text>
          </g>
        )
      })}
      <path d={areaPath} fill="url(#fitGrad)" />
      <path d={path} fill="none" stroke="#8b5cf6" strokeWidth="2" strokeLinejoin="round" />
      <circle cx={x(bestIdx)} cy={y(history[bestIdx].fitness)} r="5" fill="#8b5cf6" />
      <circle cx={x(bestIdx)} cy={y(history[bestIdx].fitness)} r="8" fill="rgba(139,92,246,0.3)" />
      <text x={padL} y={H - 6} fontSize="10" fill="var(--text-muted)">1</text>
      <text x={W - padR} y={H - 6} fontSize="10" fill="var(--text-muted)" textAnchor="end">{history.length}</text>
      <text x={(padL + W - padR) / 2} y={H - 6} fontSize="10" fill="var(--text-muted)" textAnchor="middle">Trial</text>
    </svg>
  )
}

function FLChart({ rounds }: { rounds: FLResult['rounds'] }) {
  if (!rounds.length) return null
  const W = 800, H = 180, padL = 40, padR = 20, padT = 10, padB = 30
  const minR = 0, maxR = 1
  const x = (i: number) => padL + (i / (rounds.length - 1 || 1)) * (W - padL - padR)
  const y = (v: number) => padT + (1 - (v - minR) / (maxR - minR || 1)) * (H - padT - padB)
  const path = rounds.map((r, i) => `${i === 0 ? 'M' : 'L'}${x(i)},${y(r.global_r2 ?? 0)}`).join(' ')
  return (
    <svg viewBox={`0 0 ${W} ${H}`} className="chart-svg" preserveAspectRatio="none">
      <path d={path} fill="none" stroke="#34d399" strokeWidth="2.5" strokeLinejoin="round" />
      {rounds.map((r, i) => (
        <circle key={i} cx={x(i)} cy={y(r.global_r2 ?? 0)} r="4" fill="#34d399" />
      ))}
      <text x={padL} y={H - 6} fontSize="10" fill="var(--text-muted)">R1</text>
      <text x={W - padR} y={H - 6} fontSize="10" fill="var(--text-muted)" textAnchor="end">R{rounds.length}</text>
      <text x={(padL + W - padR) / 2} y={H - 6} fontSize="10" fill="var(--text-muted)" textAnchor="middle">Round</text>
    </svg>
  )
}

function getR2Class(r2: number) {
  if (r2 >= 0.9) return 'r2-high'
  if (r2 >= 0.7) return 'r2-mid'
  return 'r2-low'
}

export default function App() {
  const [tab, setTab] = useState<Tab>('formulations')
  const [form, setForm] = useState<FormState>({ Pt: 1.5, Pd: 5.0, Rh: 0.3, CeO2: 100, ZrO2: 20, name: '' })
  const [predResult, setPredResult] = useState<PredResult | null>(null)
  const [formulations, setFormulations] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [optResult, setOptResult] = useState<OptResult | null>(null)
  const [flResult, setFlResult] = useState<FLResult | null>(null)

  const loadFormulations = () => api.formulations().then(setFormulations).catch(() => {})

  const handlePredict = async () => {
    setLoading(true)
    try {
      const res = await api.predict({ Pt: form.Pt, Pd: form.Pd, Rh: form.Rh, CeO2: form.CeO2, ZrO2: form.ZrO2 })
      setPredResult(res)
    } finally { setLoading(false) }
  }

  const handleSave = async () => {
    setLoading(true)
    try {
      await api.createFormulation({ name: form.name || undefined, Pt: form.Pt, Pd: form.Pd, Rh: form.Rh, CeO2: form.CeO2, ZrO2: form.ZrO2 })
      await loadFormulations()
    } finally { setLoading(false) }
  }

  const handleOptimize = async (trials = 60) => {
    setLoading(true)
    try {
      const res = await api.optimize(trials)
      setOptResult(res)
    } finally { setLoading(false) }
  }

  const handleFL = async (rounds = 5) => {
    setLoading(true)
    try {
      const res = await api.flRun(rounds)
      setFlResult(res)
    } finally { setLoading(false) }
  }

  const tabs: { key: Tab; label: string }[] = [
    { key: 'formulations', label: '配方管理' },
    { key: 'inference', label: 'PyTorch推理' },
    { key: 'optimize', label: '贝叶斯优化' },
    { key: 'fl', label: '联邦学习' },
  ]

  return (
    <div className="app-container">
      <div className="header">
        <div className="header-top">
          <div className="logo">&#9888;</div>
          <div>
            <div className="header-title">TWC-FL Platform</div>
            <div className="header-sub">三效催化转化器 &middot; 联邦学习优化平台 v1.0</div>
          </div>
          <div style={{ marginLeft: 'auto', display: 'flex', gap: 6, alignItems: 'center' }}>
            <span className="badge badge-green">PyTorch 2.2</span>
            <span className="badge badge-purple">FastAPI</span>
            <span className="badge badge-yellow">Optuna</span>
          </div>
        </div>
        <nav className="nav-tabs">
          {tabs.map(t => (
            <button key={t.key} className={`nav-tab${tab === t.key ? ' active' : ''}`} onClick={() => setTab(t.key)}>
              {t.label}
            </button>
          ))}
        </nav>
      </div>

      {tab === 'formulations' && (
        <>
          <div className="card">
            <div className="card-title">
              配方输入
              <span className="badge badge-purple">TWCNet MLP</span>
            </div>
            <div className="form-grid">
              {[
                { key: 'Pt', label: 'Pt (g/L) \u00b7 铂', min: 0, max: 3, step: 0.05 },
                { key: 'Pd', label: 'Pd (g/L) \u00b7 钯', min: 0, max: 10, step: 0.1 },
                { key: 'Rh', label: 'Rh (g/L) \u00b7 铑', min: 0, max: 1, step: 0.01 },
                { key: 'CeO2', label: 'CeO\u2082 (g/L) \u00b7 铈', min: 50, max: 200, step: 1 },
                { key: 'ZrO2', label: 'ZrO\u2082 (g/L) \u00b7 锆', min: 0, max: 50, step: 1 },
              ].map(({ key, label, min, max, step }) => (
                <div className="field" key={key}>
                  <label>{label}</label>
                  <div className="range-row">
                    <input type="range" min={min} max={max} step={step} value={(form as any)[key]} onChange={e => setForm(f => ({ ...f, [key]: +e.target.value }))} />
                    <span className="range-val">{(form as any)[key].toFixed(key === 'Pt' || key === 'Rh' ? 2 : key === 'Pd' ? 1 : 0)}</span>
                  </div>
                </div>
              ))}
              <div className="field">
                <label>配方名称</label>
                <input type="text" placeholder="可选，如：Demo-A1" value={form.name} onChange={e => setForm(f => ({ ...f, name: e.target.value }))} />
              </div>
            </div>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={handlePredict} disabled={loading}>
                {loading ? <><span className="spinner" /> 运行中&hellip;</> : '\uD83D\uDD2E 预测'}
              </button>
              <button className="btn btn-secondary" onClick={handleSave} disabled={loading}>
                &#128190; 保存配方
              </button>
            </div>
          </div>

          {predResult && (
            <div className="card">
              <div className="card-title">
                预测结果
                <span className={`badge ${predResult.meets_euro6 ? 'badge-green' : 'badge-red'}`}>
                  Euro6 {predResult.meets_euro6 ? '\u2713 通过' : '\u2717 未达标'}
                </span>
                <span className="badge badge-purple">fitness: {predResult.fitness}</span>
              </div>
              <div className="result-grid">
                {[
                  { label: 'CO 转化率', val: predResult.predictions.co_conv, pass: predResult.predictions.co_conv >= 94, unit: '% ≥94%' },
                  { label: 'HC 转化率', val: predResult.predictions.hc_conv, pass: predResult.predictions.hc_conv >= 94, unit: '% ≥94%' },
                  { label: 'NOx 转化率', val: predResult.predictions.nox_conv, pass: predResult.predictions.nox_conv >= 90, unit: '% ≥90%' },
                  { label: 'T50 温度', val: predResult.predictions.t50, pass: predResult.predictions.t50 <= 200, unit: '\u00b0C ≤200\u00b0C' },
                ].map(item => (
                  <div className="result-item" key={item.label}>
                    <div className="result-label">{item.label}</div>
                    <div className="result-value" style={{ color: item.pass ? 'var(--success)' : 'var(--danger)' }}>
                      {item.val}
                    </div>
                    <div className="result-unit">{item.unit}</div>
                  </div>
                ))}
              </div>
              <div className="euro6-section">
                <Euro6Bar label="CO" value={predResult.predictions.co_conv} threshold={94} />
                <Euro6Bar label="HC" value={predResult.predictions.hc_conv} threshold={94} />
                <Euro6Bar label="NOx" value={predResult.predictions.nox_conv} threshold={90} />
                <div className="euro6-status">
                  {predResult.meets_euro6 ? <span className="pass-icon">&#10003;</span> : <span className="fail-icon">&#10007;</span>}
                  <span style={{ color: predResult.meets_euro6 ? 'var(--success)' : 'var(--danger)' }}>
                    {predResult.meets_euro6 ? '满足 Euro6 排放标准' : '不满足 Euro6 排放标准'}
                  </span>
                  <span className="badge badge-purple" style={{ marginLeft: 'auto' }}>
                    Fitness {predResult.fitness}
                  </span>
                </div>
              </div>
            </div>
          )}

          <div className="card">
            <div className="card-title">已保存配方列表</div>
            <button className="btn btn-secondary" onClick={loadFormulations} style={{ marginBottom: 12 }}>
              &#128260; 刷新列表
            </button>
            {formulations.length === 0 ? (
              <div style={{ color: 'var(--text-muted)', fontSize: 13 }}>暂无保存的配方</div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table className="data-table">
                  <thead>
                    <tr>
                      <th>ID</th><th>名称</th><th>Pt</th><th>Pd</th><th>Rh</th><th>CeO\u2082</th><th>ZrO\u2082</th>
                      <th>CO%</th><th>HC%</th><th>NOx%</th><th>T50</th><th>Fitness</th><th>Euro6</th>
                    </tr>
                  </thead>
                  <tbody>
                    {formulations.map(f => (
                      <tr key={f.id}>
                        <td>{f.id}</td>
                        <td>{f.name || '\u2014'}</td>
                        <td>{f.Pt?.toFixed(2)}</td>
                        <td>{f.Pd?.toFixed(1)}</td>
                        <td>{f.Rh?.toFixed(2)}</td>
                        <td>{f.CeO2?.toFixed(0)}</td>
                        <td>{f.ZrO2?.toFixed(0)}</td>
                        <td style={{ color: (f.co_conv ?? 0) >= 94 ? 'var(--success)' : 'var(--danger)' }}>{f.co_conv?.toFixed(1)}</td>
                        <td style={{ color: (f.hc_conv ?? 0) >= 94 ? 'var(--success)' : 'var(--danger)' }}>{f.hc_conv?.toFixed(1)}</td>
                        <td style={{ color: (f.nox_conv ?? 0) >= 90 ? 'var(--success)' : 'var(--danger)' }}>{f.nox_conv?.toFixed(1)}</td>
                        <td>{f.t50?.toFixed(0)}\u00b0C</td>
                        <td style={{ color: 'var(--accent)' }}>{f.fitness_score?.toFixed(2)}</td>
                        <td>
                          {f.meets_euro6
                            ? <span className="badge badge-green">通过</span>
                            : <span className="badge badge-red">未达标</span>}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}

      {tab === 'inference' && (
        <>
          <div className="card">
            <div className="card-title">
              TWCNet 模型架构 <span className="badge badge-purple">PyTorch</span>
            </div>
            <div className="model-info">
              {[
                { title: '模型类型', val: 'TWCNet MLP' },
                { title: '网络结构', val: '5 \u2192 64 \u2192 64 \u2192 4' },
                { title: '激活函数', val: 'ReLU' },
                { title: '输出维度', val: '[CO%, HC%, NOx%, T50\u00b0C]' },
              ].map(item => (
                <div className="model-card" key={item.title}>
                  <div className="model-card-title">{item.title}</div>
                  <div className="model-card-val">{item.val}</div>
                </div>
              ))}
            </div>
            <div className="arch-diagram">
              {['Input(5)', 'Linear(64)', 'ReLU', 'Linear(64)', 'ReLU', 'Linear(4)', 'Output'].map((layer, i) => (
                <React.Fragment key={layer}>
                  <div className="arch-layer" style={layer === 'Output' ? { background: 'rgba(52,211,153,0.15)', borderColor: 'rgba(52,211,153,0.3)', color: 'var(--success)' } : {}}>{layer}</div>
                  {i < 6 && <span className="arch-arrow">\u2192</span>}
                </React.Fragment>
              ))}
            </div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 10 }}>
              推理策略：PyTorch NN 预测值与物理方程预测值以 50/50 加权融合，保证物理一致性
            </div>
          </div>

          <div className="card">
            <div className="card-title">精确输入推理</div>
            <div className="form-grid">
              {[
                { key: 'Pt', label: 'Pt (g/L)', min: 0, max: 3, step: 0.01 },
                { key: 'Pd', label: 'Pd (g/L)', min: 0, max: 10, step: 0.1 },
                { key: 'Rh', label: 'Rh (g/L)', min: 0, max: 1, step: 0.01 },
                { key: 'CeO2', label: 'CeO\u2082 (g/L)', min: 50, max: 200, step: 1 },
                { key: 'ZrO2', label: 'ZrO\u2082 (g/L)', min: 0, max: 50, step: 1 },
              ].map(({ key, label, min, max, step }) => (
                <div className="field" key={key}>
                  <label>{label}</label>
                  <input type="number" min={min} max={max} step={step} value={(form as any)[key]} onChange={e => setForm(f => ({ ...f, [key]: +e.target.value }))} />
                </div>
              ))}
            </div>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={handlePredict} disabled={loading}>
                {loading ? <><span className="spinner" /> 推理中&hellip;</> : '\u26A1 PyTorch 推理'}
              </button>
            </div>
          </div>

          {predResult && (
            <div className="card">
              <div className="card-title">推理结果对比</div>
              <div className="compare-grid">
                {[
                  { label: 'CO 转化率', nn: predResult.predictions.co_conv, phys: 85 + 4.5 * form.Pt + 2.1 * form.Pd - 0.05 * form.CeO2 + 0.02 * form.ZrO2 },
                  { label: 'HC 转化率', nn: predResult.predictions.hc_conv, phys: 80 + 2.0 * form.Pt + 5.5 * form.Pd - 1.0 * form.Rh - 0.03 * form.CeO2 + 0.03 * form.ZrO2 },
                  { label: 'NOx 转化率', nn: predResult.predictions.nox_conv, phys: 70 - 8.0 * form.Pt - 3.0 * form.Pd + 60.0 * form.Rh - 0.02 * form.CeO2 + 0.01 * form.ZrO2 },
                  { label: 'T50 温度', nn: predResult.predictions.t50, phys: 280 - 60 * form.Pt - 25 * form.Pd - 80 * form.Rh + 0.1 * form.CeO2 - 0.2 * form.ZrO2 },
                ].map(item => {
                  const nnV = Math.round(Math.min(100, Math.max(0, item.nn)) * 10) / 10
                  const phV = Math.round(Math.min(100, Math.max(0, item.phys)) * 10) / 10
                  const diff = Math.abs(nnV - phV)
                  return (
                    <div className="compare-item" key={item.label}>
                      <div className="compare-label">{item.label}</div>
                      <div className="compare-val" style={{ color: 'var(--accent)' }}>{nnV}</div>
                      <div className="compare-sub">神经网络预测</div>
                      <div style={{ marginTop: 6, fontSize: 12, color: 'var(--text-muted)' }}>
                        物理方程: <span style={{ color: 'var(--text-secondary)' }}>{phV.toFixed(1)}</span>
                      </div>
                      <div style={{ fontSize: 11, color: diff < 3 ? 'var(--success)' : 'var(--warn)', marginTop: 2 }}>
                        &#916; {diff.toFixed(1)}
                      </div>
                    </div>
                  )
                })}
              </div>
            </div>
          )}
        </>
      )}

      {tab === 'optimize' && (
        <>
          <div className="card">
            <div className="card-title">
              贝叶斯优化 <span className="badge badge-purple">Optuna TPE</span>
            </div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 14, lineHeight: 1.7 }}>
              使用 Optuna 的 Tree-structured Parzen Estimator (TPE) 采样器，在 5 维参数空间
              (Pt, Pd, Rh, CeO\u2082, ZrO\u2082) 中搜索满足 Euro6 约束的最优配方，目标函数为 fitness score。
            </div>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={() => handleOptimize(30)} disabled={loading}>
                {loading ? <><span className="spinner" /> 优化中&hellip;</> : '&#128640; 快速优化 (30 trials)'}
              </button>
              <button className="btn btn-primary" onClick={() => handleOptimize(60)} disabled={loading}>
                {loading ? <><span className="spinner" /> 优化中&hellip;</> : '&#128640; 完整优化 (60 trials)'}
              </button>
            </div>
          </div>

          {optResult && (
            <>
              <div className="card">
                <div className="card-title">
                  最优配方
                  <span className="badge badge-green">Best Trial</span>
                  <span className="badge badge-purple">fitness: {optResult.best.fitness?.toFixed(2)}</span>
                </div>
                <div className="result-grid">
                  {[
                    { label: 'Pt', val: optResult.best.Pt?.toFixed(3), unit: 'g/L' },
                    { label: 'Pd', val: optResult.best.Pd?.toFixed(2), unit: 'g/L' },
                    { label: 'Rh', val: optResult.best.Rh?.toFixed(3), unit: 'g/L' },
                    { label: 'CeO\u2082', val: optResult.best.CeO2?.toFixed(1), unit: 'g/L' },
                    { label: 'ZrO\u2082', val: optResult.best.ZrO2?.toFixed(1), unit: 'g/L' },
                  ].map(item => (
                    <div className="result-item" key={item.label}>
                      <div className="result-label">{item.label}</div>
                      <div className="result-value" style={{ color: 'var(--accent)', fontSize: 18 }}>{item.val}</div>
                      <div className="result-unit">{item.unit}</div>
                    </div>
                  ))}
                </div>
                <div className="result-grid" style={{ marginTop: 8 }}>
                  {[
                    { label: 'CO', val: optResult.best.predictions?.co_conv ?? 0, pass: (optResult.best.predictions?.co_conv ?? 0) >= 94 },
                    { label: 'HC', val: optResult.best.predictions?.hc_conv ?? 0, pass: (optResult.best.predictions?.hc_conv ?? 0) >= 94 },
                    { label: 'NOx', val: optResult.best.predictions?.nox_conv ?? 0, pass: (optResult.best.predictions?.nox_conv ?? 0) >= 90 },
                    { label: 'T50', val: optResult.best.predictions?.t50 ?? 300, pass: (optResult.best.predictions?.t50 ?? 300) <= 200 },
                  ].map(item => (
                    <div className="result-item" key={item.label}>
                      <div className="result-label">{item.label}</div>
                      <div className="result-value" style={{ color: item.pass ? 'var(--success)' : 'var(--danger)', fontSize: 16 }}>
                        {item.label === 'T50' ? `${item.val.toFixed(0)}\u00b0C` : `${item.val.toFixed(1)}%`}
                      </div>
                    </div>
                  ))}
                </div>
                <div className="euro6-section">
                  <Euro6Bar label="CO" value={optResult.best.predictions?.co_conv ?? 0} threshold={94} />
                  <Euro6Bar label="HC" value={optResult.best.predictions?.hc_conv ?? 0} threshold={94} />
                  <Euro6Bar label="NOx" value={optResult.best.predictions?.nox_conv ?? 0} threshold={90} />
                </div>
              </div>

              <div className="card">
                <div className="card-title">
                  优化收敛曲线
                  <span className="badge badge-purple">{optResult.n_trials} trials</span>
                </div>
                <div className="chart-wrap">
                  <FitnessChart history={optResult.history} />
                </div>
              </div>
            </>
          )}
        </>
      )}

      {tab === 'fl' && (
        <>
          <div className="card">
            <div className="card-title">
              联邦学习模拟 <span className="badge badge-purple">FedAvg</span>
              <span className="badge badge-yellow">PyTorch</span>
            </div>
            <div className="btn-row">
              <button className="btn btn-primary" onClick={() => handleFL(3)} disabled={loading}>
                {loading ? <><span className="spinner" /> 训练中&hellip;</> : '&#128260; 运行 3 轮 FL'}
              </button>
              <button className="btn btn-primary" onClick={() => handleFL(5)} disabled={loading}>
                {loading ? <><span className="spinner" /> 训练中&hellip;</> : '&#128260; 运行 5 轮 FL'}
              </button>
              <button className="btn btn-secondary" onClick={() => handleFL(10)} disabled={loading}>
                {loading ? <><span className="spinner" /> 训练中&hellip;</> : '&#128260; 运行 10 轮 FL'}
              </button>
            </div>
          </div>

          <div className="fl-concept">
            <div className="fl-concept-title">&#128274; 联邦学习原理</div>
            <p style={{ marginBottom: 8 }}>
              {flResult?.concept || '点击上方按钮启动模拟联邦学习训练。三家催化剂企业（威孚高科、润沃驰、催化剂厂）在配方数据不出厂的前提下，通过 FedAvg 算法联合训练全局 TWC 预测模型。'}
            </p>
            <p><strong style={{ color: 'var(--accent)' }}>算法:</strong> {flResult?.fl_algorithm || 'FedAvg (PyTorch weight averaging)'}</p>
            <p><strong style={{ color: 'var(--accent)' }}>数据隐私:</strong> {flResult?.data_privacy || '配方数据保留在各客户端本地，仅上传模型权重更新'}</p>
          </div>

          {flResult && (
            <>
              <div className="card">
                <div className="card-title">
                  FL 训练结果
                  <span className="badge badge-green">Final R\u00b2: {flResult.final_global_r2}</span>
                  <span className="badge badge-purple">{flResult.rounds.length} 轮</span>
                </div>
                <div style={{ overflowX: 'auto' }}>
                  <table className="data-table">
                    <thead>
                      <tr>
                        <th>轮次</th>
                        <th>威孚高科 R\u00b2</th>
                        <th>润沃驰 R\u00b2</th>
                        <th>催化剂厂 R\u00b2</th>
                        <th>全局 R\u00b2</th>
                      </tr>
                    </thead>
                    <tbody>
                      {flResult.rounds.map(r => (
                        <tr key={r.round}>
                          <td>Round {r.round}</td>
                          <td className={getR2Class(r.clients['威孚高科']?.local_r2 ?? 0)}>
                            {(r.clients['威孚高科']?.local_r2 ?? 0).toFixed(4)}
                          </td>
                          <td className={getR2Class(r.clients['润沃驰']?.local_r2 ?? 0)}>
                            {(r.clients['润沃驰']?.local_r2 ?? 0).toFixed(4)}
                          </td>
                          <td className={getR2Class(r.clients['催化剂厂']?.local_r2 ?? 0)}>
                            {(r.clients['催化剂厂']?.local_r2 ?? 0).toFixed(4)}
                          </td>
                          <td className={getR2Class(r.global_r2 ?? 0)} style={{ fontWeight: 700 }}>
                            {(r.global_r2 ?? 0).toFixed(4)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>

              <div className="card">
                <div className="card-title">全局 R\u00b2 收敛曲线</div>
                <div className="chart-wrap">
                  <FLChart rounds={flResult.rounds} />
                </div>
              </div>
            </>
          )}
        </>
      )}
    </div>
  )
}
