import { useState, useEffect } from 'react';
import {
  generateMockAccounts,
  groupByDevice,
  groupByIp,
  ACCOUNT_COUNT,
  DEVICE_POOL,
  IP_POOL,
} from './mockData.js';

/**
 * App.jsx - 攻防风控 Agent · 攻击模拟控制台
 *
 * 页面：单页，两个按钮（开始模拟 / 查看结果），一行运行状态。
 * 全部为前端模拟，不接后端。
 */

export default function App() {
  const [status, setStatus] = useState('idle'); // 'idle' | 'running' | 'done'
  const [accounts, setAccounts] = useState([]);
  const [showResults, setShowResults] = useState(false);

  const STATUS_LABEL = {
    idle: '未开始',
    running: '运行中',
    done: '已完成',
  };

  // 当状态切换为 done 时自动展开结果区
  useEffect(() => {
    if (status === 'done') {
      setShowResults(true);
    }
  }, [status]);

  const STATUS_COLOR = {
    idle: '#9ca3af',
    running: '#3b82f6',
    done: '#10b981',
  };

  // 开始模拟：设置运行中，短延时后生成数据并标记完成
  const handleStartSimulation = () => {
    setStatus('running');
    setAccounts([]);
    setShowResults(false);

    // 模拟攻击过程耗时（进度反馈，约 1.2 秒）
    setTimeout(() => {
      const newAccounts = generateMockAccounts(ACCOUNT_COUNT);
      setAccounts(newAccounts);
      setStatus('done');
    }, 1200);
  };

  // 查看结果：仅在已完成时展开结果面板；若无数据则轻量提示
  const handleViewResults = () => {
    if (status === 'done' && accounts.length > 0) {
      setShowResults(true);
    } else if (status !== 'done') {
      // 可在此处加 toast 提示，此处保持静默，不影响主流程
      return;
    }
  };

  const deviceGroups = groupByDevice(accounts);
  const ipGroups = groupByIp(accounts);

  const formatAccounts = (ids, limit = 6) => {
    if (ids.length <= limit) return ids.join('，');
    return `${ids.slice(0, limit).join('，')} 等 ${ids.length} 个`;
  };

  return (
    <div className="app">
      {/* 头部 */}
      <header className="header">
        <div className="badge">攻防风控 Agent</div>
        <h1>攻击模拟控制台</h1>
        <p className="sub">
          模拟黑产批量注册攻击（多开 + IP 池），展示账号聚类与共用设备/网络特征
        </p>
      </header>

      {/* 运行状态栏 */}
      <div className="status-bar">
        <span className="status-dot" style={{ backgroundColor: STATUS_COLOR[status] }}></span>
        <span className="status-text">{STATUS_LABEL[status]}</span>
      </div>

      {/* 操作区：两个按钮 */}
      <div className="actions">
        <button className="btn btn-primary" onClick={handleStartSimulation} disabled={status === 'running'}>
          {status === 'running' ? '模拟进行中...' : '开始模拟'}
        </button>
        <button
          className="btn btn-secondary"
          onClick={handleViewResults}
          disabled={status !== 'done' || accounts.length === 0}
        >
          查看结果
        </button>
      </div>

      {/* 参数说明卡片 */}
      <div className="params-card">
        <p className="params-title">模拟参数</p>
        <div className="params-grid">
          <div className="param-item">
            <span className="param-key">账号总数</span>
            <span className="param-value">{ACCOUNT_COUNT}</span>
          </div>
          <div className="param-item">
            <span className="param-key">模拟设备</span>
            <span className="param-value">{DEVICE_POOL.join('，')}</span>
          </div>
          <div className="param-item">
            <span className="param-key">模拟 IP</span>
            <span className="param-value">{IP_POOL.join('，')}</span>
          </div>
        </div>
      </div>

      {/* 结果区 */}
      {showResults && accounts.length > 0 && (
        <section className="results">
          <h2>模拟结果</h2>

          {/* 顶部统计卡片 */}
          <div className="stats-cards">
            <div className="stat-card">
              <span className="stat-label">模拟注册账号总数</span>
              <span className="stat-value">{accounts.length}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">复用设备数</span>
              <span className="stat-value">{deviceGroups.length}</span>
            </div>
            <div className="stat-card">
              <span className="stat-label">复用 IP 数</span>
              <span className="stat-value">{ipGroups.length}</span>
            </div>
          </div>

          {/* 共用设备列表 */}
          <div className="group-section">
            <h3>共用设备（多开聚类）</h3>
            <div className="group-list">
              {deviceGroups.map((g) => (
                <div key={g.deviceId} className="group-item">
                  <div className="group-head">
                    <span className="group-id">{g.deviceId}</span>
                    <span className="group-count">{g.count} 个账号</span>
                  </div>
                  <div className="group-accounts">{formatAccounts(g.accounts)}</div>
                </div>
              ))}
            </div>
          </div>

          {/* 共用网络（IP）列表 */}
          <div className="group-section">
            <h3>共用网络（IP 池复用）</h3>
            <div className="group-list">
              {ipGroups.map((g) => (
                <div key={g.ip} className="group-item">
                  <div className="group-head">
                    <span className="group-id">{g.ip}</span>
                    <span className="group-count">{g.count} 个账号</span>
                  </div>
                  <div className="group-accounts">{formatAccounts(g.accounts)}</div>
                </div>
              ))}
            </div>
          </div>
        </section>
      )}

      {showResults && accounts.length === 0 && (
        <div className="empty-tip">暂无模拟数据，请先点击“开始模拟”。</div>
      )}
    </div>
  );
}
