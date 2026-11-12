// 攻击资源库（模拟“数据库表”：每行一台设备，列是注册时的设备指纹特征）
// 资源是有限、固定的集合，用来模拟攻击方多开设备 + 出口复用的真实约束。
//
// 说明：这里只生成攻击方资源种子，由 attacker/server/seed.js 写入本地库。
// 注册记录由 FastAPI 写入 attack_console，不在浏览器里累计。

export const DEVICE_COUNT = 100;
export const DEFAULT_BATCH_SIZE = 20;
export const DEFAULT_INTERVAL_MS = 3000;

// 有限的网络资源集合（出口 IP 池）
export const NETWORK_DB = [
  { ip: '103.21.58.10', ipType: '住宅宽带', region: '广东 深圳', isp: '中国移动', asn: 'AS56044' },
  { ip: '119.3.124.5', ipType: '住宅宽带', region: '北京 朝阳区', isp: '中国联通', asn: 'AS4837' },
  { ip: '36.136.22.9', ipType: '移动 4G/5G', region: '上海 徐汇区', isp: '中国移动', asn: 'AS56046' },
  { ip: '183.62.124.2', ipType: '住宅宽带', region: '广东 广州', isp: '中国电信', asn: 'AS4134' },
  { ip: '220.181.108.15', ipType: '数据中心', region: '北京 海淀区', isp: '阿里云', asn: 'AS45102' },
  { ip: '39.156.69.7', ipType: '移动 4G/5G', region: '四川 成都', isp: '中国移动', asn: 'AS56044' },
  { ip: '120.232.15.20', ipType: '数据中心', region: '上海 松江区', isp: '腾讯云', asn: 'AS45090' },
  { ip: '182.91.24.40', ipType: '住宅宽带', region: '浙江 杭州', isp: '中国电信', asn: 'AS4134' },
  { ip: '111.17.16.3', ipType: '移动 4G/5G', region: '湖北 武汉', isp: '中国移动', asn: 'AS56048' },
  { ip: '211.138.104.50', ipType: '住宅宽带', region: '四川 成都', isp: '中国联通', asn: 'AS4837' },
  { ip: '47.100.128.90', ipType: '数据中心', region: '北京 朝阳区', isp: '阿里云', asn: 'AS45102' },
  { ip: '8.210.152.60', ipType: '数据中心', region: '上海 徐汇区', isp: '腾讯云', asn: 'AS45090' },
];

const DEVICE_MODELS = [
  'iPhone 15 Pro', 'iPhone 14', 'Xiaomi 13', 'Xiaomi 14 Pro', 'Samsung Galaxy S23',
  'Huawei P60', 'Huawei Mate 60', 'OPPO Find X6', 'vivo X90', 'iPad Air 5',
  'MacBook Air M2', 'Dell XPS 13', 'ThinkPad X1 Carbon', 'Honor Magic5', 'OnePlus 11',
  'Google Pixel 8', 'Sony Xperia 1 V', 'Redmi K70', 'iQOO 12', 'Meizu 20',
];

const OS_VERSIONS = [
  'iOS 17.2', 'iOS 16.6', 'Android 14', 'Android 13', 'Android 12',
  'Windows 11 22H2', 'Windows 10 21H2', 'macOS Sonoma 14', 'iPadOS 17', 'HarmonyOS 4',
];

const BROWSERS = ['Chrome 120.0', 'Chrome 119.0', 'Safari 17.2', 'Edge 120.0', 'Firefox 121.0'];

const SCREEN_RESOLUTIONS = ['1179x2556', '1080x2400', '1440x3200', '2532x1170', '2880x1864', '1920x1080', '1366x768', '2560x1600'];

const TIMEZONES = ['Asia/Shanghai', 'Asia/Hong_Kong', 'Asia/Tokyo', 'America/New_York', 'Europe/London', 'Asia/Singapore'];

const LANGUAGES = ['zh-CN,zh;q=0.9', 'en-US,en;q=0.9', 'zh-TW,zh;q=0.9', 'en-GB,en;q=0.9'];

const WEBGL_RENDERERS = ['Adreno (TM) 740', 'Apple GPU', 'Intel Iris Xe', 'NVIDIA GeForce RTX 3060', 'Mali-G710', 'Radeon RX 6600'];

function randPick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function hashStr(str) {
  let h = 0;
  for (let i = 0; i < str.length; i++) {
    h = ((h << 5) - h + str.charCodeAt(i)) | 0;
  }
  return Math.abs(h).toString(16).padStart(8, '0');
}

// 生成固定的设备资源库：100 台设备，每台带完整指纹特征（模拟表的一行）
export function generateDeviceDB() {
  const devices = [];
  for (let i = 0; i < DEVICE_COUNT; i++) {
    const model = randPick(DEVICE_MODELS);
    const os = randPick(OS_VERSIONS);
    const browser = randPick(BROWSERS);
    const isMobile = /iOS|iPadOS|Android|HarmonyOS/.test(os);
    const ua = `${browser} (${os}) ${model}`;
    devices.push({
      deviceId: `DEV-${String(i + 1).padStart(3, '0')}`,
      deviceModel: model,
      osVersion: os,
      osArch: /Windows|macOS/.test(os) ? 'x86_64' : 'arm64',
      browserName: browser.split(' ')[0],
      browserVersion: browser,
      userAgent: ua,
      screenResolution: randPick(SCREEN_RESOLUTIONS),
      colorDepth: 24,
      devicePixelRatio: Math.random() > 0.5 ? 2 : 1,
      platform: /Windows/.test(os) ? 'Win32' : /macOS/.test(os) ? 'MacIntel' : 'Linux arm64',
      hardwareConcurrency: [4, 6, 8, 12, 16][randInt(0, 4)],
      deviceMemory: [4, 8, 16][randInt(0, 2)],
      touchSupport: isMobile || Math.random() > 0.5,
      webGLRenderer: randPick(WEBGL_RENDERERS),
      audioContextFingerprint: hashStr(ua + model + os),
      canvasFingerprint: hashStr(model + ua + browser),
      timezone: randPick(TIMEZONES),
      language: randPick(LANGUAGES),
      cookieEnabled: true,
      localStorageEnabled: true,
      webrtcLocalIP: `192.168.${randInt(0, 255)}.${randInt(2, 254)}`,
      fontListHash: hashStr(model + os + browser + 'fonts'),
    });
  }
  return devices;
}

// 生成一轮注册记录：模拟攻击端读取设备特征，把账号“注册”进防守方库。
// batchSize      本轮注册账号数
// reuseIntensity 0~1，越大本轮选用的 IP 越少（出口复用越严重）
// counter        全局账号递增计数（由调用方维护）
export function generateRegistrationBatch({
  batchSize = DEFAULT_BATCH_SIZE,
  reuseIntensity = 0.5,
  counter = 0,
  deviceDB = [],
  networkDB = NETWORK_DB,
} = {}) {
  const now = new Date();
  const stamp = now.toISOString().replace('T', ' ').slice(0, 19);

  // 本轮选用的 IP 子集：复用强度越高，选中的 IP 越少
  const distinctCount = Math.max(1, Math.ceil(networkDB.length * (1 - reuseIntensity)));
  const shuffled = [...networkDB].sort(() => 0.5 - Math.random());
  const ipSubset = shuffled.slice(0, distinctCount);

  // 攻击方可观测的原始注册结果：大部分成功，少数失败（验证码错误或请求被拒）
  const statusPool = ['success', 'success', 'success', 'success', 'success', 'failed'];

  const batch = [];
  for (let i = 0; i < batchSize; i++) {
    const n = counter + i + 1;
    const device = deviceDB.length
      ? deviceDB[Math.floor(Math.random() * deviceDB.length)]
      : null;
    const ip = ipSubset[Math.floor(Math.random() * ipSubset.length)];
    const status = randPick(statusPool);

    batch.push({
      id: `REG-${String(n).padStart(5, '0')}`,
      phone: `138${String(n).padStart(8, '0')}`,
      email: `user${n}@example.com`,
      status,
      createdAt: stamp,
      device,
      network: ip,
      failureReason:
        status === 'failed' ? '注册请求被拒绝（验证码校验失败）' : null,
    });
  }
  return batch;
}
