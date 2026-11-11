import { useState, useEffect, useRef, useCallback } from 'react';
import './App.css';
import {
  generateDeviceDB,
  generateRegistrationBatch,
  DEFAULT_BATCH_SIZE,
  DEFAULT_INTERVAL_MS,
} from './mockData';

const STATUS_TEXT = { idle: '未开始', running: '运行中', done: '已完成' };

export default function App() {
  const [deviceDB] = useState(() => generateDeviceDB());
  const [registrations, setRegistrations] = useState([]);
  const [status, setStatus] = useState('idle');
  const [rounds, setRounds] = useState(0);
  const [reuseIntensity, setReuseIntensity] = useState(0.5);
  const [batchSize, setBatchSize] = useState(DEFAULT_BATCH_SIZE);
  const [intervalMs, setIntervalMs] = useState(DEFAULT_INTERVAL_MS);

  // 真实累计计数（不因日志截断而失真）
  const counterRef = useRef(0);
  const successRef = useRef(0);
  const blockedRef = useRef(0);
  const failedRef = useRef(0);
  const timerRef = useRef(null);
  const settingsRef = useRef({ batchSize, reuseIntensity, intervalMs });
  settingsRef.current = { batchSize, reuseIntensity, intervalMs };

  // 执行一轮注册（读取当前设置 + 设备资源库，写入模拟防守方库）
  const step = useCallback(() => {
    const { batchSize: bs, reuseIntensity: ri } = settingsRef.current;
    const batch = generateRegistrationBatch({
      batchSize: bs,
      reuseIntensity: ri,
      counter: counterRef.current,
      deviceDB,
    });
    counterRef.current += bs;
    for (const r of batch) {
      if (r.status === 'success') successRef.current += 1;
      else if (r.status === 'blocked') blockedRef.current += 1;
      else failedRef.current += 1;
    }
    setRegistrations((prev) => [...prev, ...batch].slice(-1000));
    setRounds((r) => r + 1);
  }, [deviceDB]);

  const start = () => {
    if (timerRef.current) return;
    setStatus('running');
    step();
    timerRef.current = setInterval(step, settingsRef.current.intervalMs);
  };

  const stop = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setStatus('done');
  };

  const reset = () => {
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    counterRef.current = 0;
    successRef.current = 0;
    blockedRef.current = 0;
    failedRef.current = 0;
    setRegistrations([]);
    setRounds(0);
    setStatus('idle');
  };

  useEffect(() => () => {
    if (timerRef.current) clearInterval(timerRef.current);
  }, []);

  // 运行中调整间隔时立即生效
  useEffect(() => {
    if (status === 'running') {
      clearInterval(timerRef.current);
      timerRef.current = setInterval(step, intervalMs);
    }
  }, [intervalMs, status, step]);

  const total = counterRef.current;
  const success = successRef.current;
  const blocked = blockedRef.current;
  const failed = failedRef.current;
  const isRunning = status === 'running';
  const logRows = [...registrations].reverse().slice(0, 50);

  return (
    <div className="app">
      <header className="app-header">
        <span className="badge">攻防风控 Agent</span>
        <h1>攻击模拟控制台</h1>
        <p className="sub">批量注册攻击模拟 · 有限设备资源 + 出口复用</p>
      </header>

      <div className="status-bar">
        <span className={`pill ${status}`}>
          <span className="dot" />
          {STATUS_TEXT[status]}
        </span>
        <span className="status-hint">
          每轮 {batchSize} 个账号 · 间隔 {intervalMs} ms · 出口复用强度 {(reuseIntensity * 100).toFixed(0)}%
        </span>
      </div>

      <div className="controls">
        <div className="control-group">
          <label>
            出口复用强度 <span className="val">{(reuseIntensity * 100).toFixed(0)}%</span>
          </label>
          <input
            type="range"
            min="0"
            max="100"
            value={Math.round(reuseIntensity * 100)}
            onChange={(e) => setReuseIntensity(parseInt(e.target.value, 10) / 100)}
            disabled={false}
          />
          <span className="range-labels">
            <span>低（IP 分散）</span>
            <span>高（IP 集中）</span>
          </span>
        </div>

        <div className="control-group small">
          <label>每轮账号数</label>
          <input
            type="number"
            min="1"
            max="100"
            value={batchSize}
            onChange={(e) => setBatchSize(Math.max(1, Math.min(100, parseInt(e.target.value, 10) || 1)))}
          />
        </div>

        <div className="control-group small">
          <label>注册间隔 (ms)</label>
          <input
            type="number"
            min="500"
            max="30000"
            step="500"
            value={intervalMs}
            onChange={(e) => setIntervalMs(Math.max(500, Math.min(30000, parseInt(e.target.value, 10) || 500)))}
          />
        </div>

        <div className="actions">
          <button className={`btn ${isRunning ? 'btn-stop' : 'btn-start'}`} onClick={isRunning ? stop : start}>
            {isRunning ? '停止注册' : '开始注册'}
          </button>
          {status !== 'idle' && (
            <button className="btn btn-reset" onClick={reset}>
              重置
            </button>
          )}
        </div>
      </div>

      <div className="stats">
        <div className="card">
          <div className="label">总注册数</div>
          <div className="value accent">{total}</div>
        </div>
        <div className="card">
          <div className="label">成功</div>
          <div className="value success">{success}</div>
        </div>
        <div className="card">
          <div className="label">被拦截</div>
          <div className="value blocked">{blocked}</div>
        </div>
        <div className="card">
          <div className="label">失败</div>
          <div className="value failed">{failed}</div>
        </div>
        <div className="card">
          <div className="label">已执行轮数</div>
          <div className="value">{rounds}</div>
        </div>
      </div>

      <section className="log">
        <div className="log-head">
          <h2>实时注册日志</h2>
          <span className="log-note">原始数据，未做风险聚合（聚合分析属于防守方）</span>
        </div>
        <div className="log-table">
          <div className="row head">
            <div className="cell">时间</div>
            <div className="cell">手机号</div>
            <div className="cell">设备ID</div>
            <div className="cell">设备型号</div>
            <div className="cell">IP</div>
            <div className="cell">运营商 · 地区</div>
            <div className="cell">状态</div>
          </div>
          {logRows.map((r) => (
            <div key={r.id} className={`row ${r.status}`}>
              <div className="cell mono">{r.createdAt.slice(11)}</div>
              <div className="cell mono">{r.phone}</div>
              <div className="cell mono">{r.device?.deviceId ?? '-'}</div>
              <div className="cell">{r.device?.deviceModel ?? '-'}</div>
              <div className="cell mono">{r.network.ip}</div>
              <div className="cell">{r.network.isp} · {r.network.region}</div>
              <div className="cell">
                <span className={`tag ${r.status}`}>
                  {r.status === 'success' ? '成功' : r.status === 'blocked' ? '拦截' : '失败'}
                </span>
              </div>
            </div>
          ))}
        </div>
        {registrations.length === 0 && (
          <div className="empty">尚未开始注册，点击“开始注册”发起攻击模拟。</div>
        )}
      </section>
    </div>
  );
}
