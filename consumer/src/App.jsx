import { useEffect, useState } from 'react';
import { fetchCampaign, fetchRegistration, registerPhone } from './api';

const STORAGE_KEY = 'shiguang-phone';
const PRODUCTS = [
  { name: '手冲咖啡豆', detail: '埃塞俄比亚 200g', price: 128 },
  { name: '亚麻托特包', detail: '本色帆布', price: 159 },
  { name: '陶瓷马克杯', detail: '釉色一对', price: 109 },
  { name: '香薰蜡烛', detail: '雪松 80g', price: 89 },
];

function yuan(value) {
  return `¥${value}`;
}

export default function App() {
  const [campaign, setCampaign] = useState(null);
  const [phone, setPhone] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [offline, setOffline] = useState(false);
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    let cancel = false;
    fetchCampaign()
      .then((data) => {
        if (!cancel) {
          setCampaign(data);
          setOffline(false);
        }
      })
      .catch(() => {
        if (!cancel) setOffline(true);
      });
    const saved = sessionStorage.getItem(STORAGE_KEY);
    if (saved) {
      fetchRegistration(saved)
        .then((data) => {
          if (cancel) return;
          setPhone(data.phone);
          setResult(data);
        })
        .catch(() => sessionStorage.removeItem(STORAGE_KEY));
    }
    return () => {
      cancel = true;
    };
  }, []);

  const submit = async (event) => {
    event.preventDefault();
    setSubmitting(true);
    setError('');
    try {
      const data = await registerPhone(phone);
      setPhone(data.phone);
      setResult(data);
      sessionStorage.setItem(STORAGE_KEY, data.phone);
    } catch (err) {
      setError(err.message || '领券失败');
    } finally {
      setSubmitting(false);
    }
  };

  const amount = campaign?.amountYuan ?? 20;
  const threshold = campaign?.thresholdYuan ?? 99;

  return (
    <div className="page">
      <header className="top">
        <span className="brand">拾光集市</span>
        <span className="top-note">新人礼</span>
      </header>

      {offline && (
        <p className="banner">消费端服务未启动。请在 consumer 目录运行 npm run api。</p>
      )}

      <section className="hero">
        <div className="hero-copy">
          <p className="eyebrow">新用户专享</p>
          <h1>注册领取 {amount} 元券</h1>
          <p className="lead">
            每个手机号限领一张，满 {threshold} 元可用，领取后 {campaign?.validDays ?? 7} 天内有效。
            这是本地消费端，券不会用于真实付款。
          </p>
          <ul className="rules">
            <li>一个手机号只能成为一次新用户</li>
            <li>未满 {threshold} 元的商品不能用这张券</li>
            <li>风控还没接入，新手机号目前都会发券</li>
          </ul>
        </div>

        <div className="panel">
          <h2>领取新人券</h2>
          <form onSubmit={submit}>
            <label htmlFor="phone">手机号</label>
            <input
              id="phone"
              inputMode="numeric"
              autoComplete="tel"
              placeholder="请输入 11 位手机号"
              value={phone}
              onChange={(event) => setPhone(event.target.value)}
            />
            <button type="submit" disabled={submitting || offline}>
              {submitting ? '正在发放' : '注册并领券'}
            </button>
          </form>
          {error && <p className="form-error">{error}</p>}
          {result && (
            <div className="claim">
              <p className="claim-note">
                {result.alreadyClaimed ? '这个手机号已经领过，还是这张券。' : '注册成功，券已放进你的账户。'}
              </p>
              <article className="ticket">
                <div className="ticket-value">
                  <strong>{result.coupon.amountYuan}</strong>
                  <span>元</span>
                </div>
                <div className="ticket-body">
                  <h3>{result.coupon.title}</h3>
                  <p>满 {result.coupon.thresholdYuan} 元可用</p>
                  <p className="ticket-meta">券码 {result.coupon.code} · 有效期至 {result.coupon.expiresAt}</p>
                </div>
              </article>
            </div>
          )}
        </div>
      </section>

      <section className="goods">
        <div className="goods-head">
          <h2>本周在售</h2>
          <p>券后价格按满 {threshold} 元减 {amount} 元计算，这里不能下单。</p>
        </div>
        <div className="product-grid">
          {PRODUCTS.map((item) => {
            const eligible = item.price >= threshold;
            return (
              <article key={item.name} className="product">
                <div className="product-swatch" />
                <h3>{item.name}</h3>
                <p>{item.detail}</p>
                <div className="price-row">
                  <span className="price">{yuan(item.price)}</span>
                  {eligible ? (
                    <span className="after">券后 {yuan(item.price - amount)}</span>
                  ) : (
                    <span className="muted">未满 {threshold}，暂不可用</span>
                  )}
                </div>
              </article>
            );
          })}
        </div>
      </section>
    </div>
  );
}
