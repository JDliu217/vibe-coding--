import { useState, useEffect, useRef } from 'react';
import './App.css';
import { fetchState, resetLedger, startBatch, stopBatch, tickBatch } from './api';

const STATUS_TEXT = { idle: '未开始', running: '运行中', done: '已完成' };
const EMPTY_STATS = { total: 0, success: 0, failed: 0, rounds: 0 };

export default function App() {
  const [submissions, setSubmissions] = useState([]);
  const [status, setStatus] = useState('idle');
  const [stats, setStats] = useState(EMPTY_STATS);
  const [reuseIntensity, setReuseIntensity] = useState(0.5);
  const [batchSize, setBatchSize] = useState(20);
  const [intervalMs, setIntervalMs] = useState(3000);
  const [error, setError] = useState('');

  const timerRef = useRef(null);
  const runningRef = useRef(false);
  const tickingRef = useRef(false);
  const batchIdRef = useRef(null);
  const settingsRef = useRef({ batchSize, reuseIntensity });
  settingsRef.current = { batchSize, reuseIntensity };

  const applyState = (data, includeSettings = false) => {
    batchIdRef.current = data.batchId;
    setStats(data.stats);
    setSubmissions(data.submissions);
    setStatus(data.status);
    if (includeSettings) {
      setReuseIntensity(data.reuseIntensity);
      setBatchSize(data.batchSize);
      setIntervalMs(data.intervalMs);
    }
  };

  const tick = async () => {
    if (!runningRef.current || !batchIdRef.current || tickingRef.current) return;
    tickingRef.current = true;
    try {
      const data = await tickBatch(batchIdRef.current, settingsRef.current);
      setStats(data.stats);
      setSubmissions(data.submissions);
      if (runningRef.current) setStatus(data.status);
      setError('');
    } catch (err) {
      runningRef.current = false;
      setStatus('done');
      setError(err.message || '本轮注册失败');
      if (batchIdRef.current) {
        stopBatch(batchIdRef.current).catch(() => {});
      }
    } finally {
      tickingRef.current = false;
    }
  };

  const tickRef = useRef(tick);
  tickRef.current = tick;

  useEffect(() => {
    let cancel = false;
    fetchState()
      .then((data) => {
        if (cancel) return;
        applyState(data, true);
        if (data.status === 'running') {
          runningRef.current = true;
          batchIdRef.current = data.batchId;
        }
      })
      .catch(() => {
        if (!cancel) setError('后端未启动，请先运行 Python API');
      });
    return () => {
      cancel = true;
    };
  }, []);

  useEffect(() => {
    if (status !== 'running') return undefined;
    const timer = setInterval(() => {
      tickRef.current();
    }, intervalMs);
    timerRef.current = timer;
    return () => {
      clearInterval(timer);
      if (timerRef.current === timer) timerRef.current = null;
    };
  }, [status, intervalMs]);

  const start = async () => {
    if (runningRef.current || tickingRef.current) return;
    setError('');
    try {
      const data = await startBatch({
        reuseIntensity,
        batchSize,
        intervalMs,
      });
      batchIdRef.current = data.batchId;
      runningRef.current = true;
      setStatus('running');
      await tick();
    } catch (err) {
      runningRef.current = false;
      setError(err.message || '无法开始注册');
    }
  };

  const stop = async () => {
    runningRef.current = false;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    setStatus('done');
    if (!batchIdRef.current) return;
    try {
      const data = await stopBatch(batchIdRef.current);
      applyState(data);
      setStatus('done');
    } catch (err) {
      setError(err.message || '停止失败');
    }
  };

  const reset = async () => {
    runningRef.current = false;
    if (timerRef.current) {
      clearInterval(timerRef.current);
      timerRef.current = null;
    }
    try {
      const data = await resetLedger();
      applyState(data);
      setError('');
    } catch (err) {
      setError(err.message || '重置失败');
    }
  };

  const isRunning = status === 'running';

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
        {error && <span className="status-error">{error}</span>}
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
          <div className="value accent">{stats.total}</div>
        </div>
        <div className="card">
          <div className="label">成功</div>
          <div className="value success">{stats.success}</div>
        </div>
        <div className="card">
          <div className="label">失败</div>
          <div className="value failed">{stats.failed}</div>
        </div>
        <div className="card">
          <div className="label">已执行轮数</div>
          <div className="value">{stats.rounds}</div>
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
          {submissions.map((row) => (
            <div key={row.id} className={`row ${row.status}`}>
              <div className="cell mono">{row.createdAt.slice(11)}</div>
              <div className="cell mono">{row.phone}</div>
              <div className="cell mono">{row.deviceId}</div>
              <div className="cell">{row.deviceModel}</div>
              <div className="cell mono">{row.ip}</div>
              <div className="cell">{row.isp} · {row.region}</div>
              <div className="cell">
                <span className={`tag ${row.status}`}>
                  {row.status === 'success' ? '成功' : '失败'}
                </span>
              </div>
            </div>
          ))}
        </div>
        {submissions.length === 0 && (
          <div className="empty">尚未开始注册，点击“开始注册”发起攻击模拟。</div>
        )}
      </section>
    </div>
  );
}
