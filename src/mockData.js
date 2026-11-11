/**
 * mockData.js
 *
 * 固定参数生成模拟注册账号数据，并按设备 / IP 做聚合。
 * 整个为纯前端模拟，无需后端，方便面试演示“攻击聚类”特征。
 */

// ---------------- 固定参数（可面试讲解） ----------------
// 本次模拟生成的账号总数
export const ACCOUNT_COUNT = 60;

// 模拟多开设备池（手机模拟器 / 多开实例）
export const DEVICE_POOL = [
  'EMU-01', 'EMU-02', 'EMU-03', 'EMU-04', 'EMU-05', 'EMU-06',
];

// 模拟 IP 池（共用网络，模拟 IP 代理池）
export const IP_POOL = [
  '103.21.58.12', '103.21.58.15', '103.21.58.21', '103.21.58.33',
  '45.142.120.8', '45.142.120.11', '45.142.120.19', '203.0.113.45',
];

// 手机号前缀，方便生成看起来像手机号的字符串
const PHONE_PREFIXES = ['138', '139', '150', '151', '152', '153', '155', '156', '157', '158', '159'];

// ---------------- 工具函数 ----------------

/**
 * 伪随机数生成器：种子固定可复现，面试演示更稳定
 */
let seed = Date.now();
function pseudoRandom(min, max) {
  seed = (seed * 1103515245 + 12345) % 2147483648;
  return min + Math.floor((seed / 2147483648) * (max - min + 1));
}

/**
 * 随机从池中抽取，带“轻度偏置”：
 * 让前几个设备/IP 被抽到概率更高，模拟攻击者喜欢复用少量优质设备/IP。
 */
function biasedPick(pool) {
  const idx = pseudoRandom(0, pool.length - 1);
  // 30% 概率回落到前 1/3 的热门条目
  if (pseudoRandom(0, 99) < 30) {
    const hotCount = Math.ceil(pool.length / 3);
    return pool[pseudoRandom(0, hotCount - 1)];
  }
  return pool[idx];
}

function randomPhone() {
  const prefix = PHONE_PREFIXES[pseudoRandom(0, PHONE_PREFIXES.length - 1)];
  const suffix = String(pseudoRandom(10000000, 99999999));
  return `${prefix}${suffix}`;
}

/**
 * 生成一批模拟注册账号。
 * 每个账号：{ id, phone, deviceId, ip, createdAt }
 * 设备与 IP 从固定池中抽取，部分会被大量复用（聚类特征）。
 */
export function generateMockAccounts(count = ACCOUNT_COUNT) {
  const accounts = [];
  for (let i = 1; i <= count; i++) {
    accounts.push({
      id: `ACC-${String(i).padStart(4, '0')}`,
      phone: randomPhone(),
      deviceId: biasedPick(DEVICE_POOL),
      ip: biasedPick(IP_POOL),
      createdAt: new Date().toLocaleString('zh-CN', {
        hour12: false,
      }),
    });
  }
  return accounts;
}

/**
 * 按设备聚合：[{ deviceId, count, accounts: [id...] }]
 * 按 count 降序排列，便于展示“共用设备最多”的设备
 */
export function groupByDevice(accounts) {
  const map = new Map();
  for (const acc of accounts) {
    if (!map.has(acc.deviceId)) {
      map.set(acc.deviceId, { deviceId: acc.deviceId, count: 0, accounts: [] });
    }
    const g = map.get(acc.deviceId);
    g.count += 1;
    g.accounts.push(acc.id);
  }
  return Array.from(map.values()).sort((a, b) => b.count - a.count);
}

/**
 * 按 IP 聚合：[{ ip, count, accounts: [id...] }]
 * 按 count 降序排列
 */
export function groupByIp(accounts) {
  const map = new Map();
  for (const acc of accounts) {
    if (!map.has(acc.ip)) {
      map.set(acc.ip, { ip: acc.ip, count: 0, accounts: [] });
    }
    const g = map.get(acc.ip);
    g.count += 1;
    g.accounts.push(acc.id);
  }
  return Array.from(map.values()).sort((a, b) => b.count - a.count);
}
