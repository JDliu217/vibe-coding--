import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';
import mysql from 'mysql2/promise';
import { NETWORK_DB, generateDeviceDB } from '../src/mockData.js';

const root = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..');
const PHONE_COUNT = 1000;

function loadEnv(file) {
  if (!fs.existsSync(file)) return;
  const text = fs.readFileSync(file, 'utf8');
  for (const line of text.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith('#')) continue;
    const i = trimmed.indexOf('=');
    if (i === -1) continue;
    const key = trimmed.slice(0, i).trim();
    let value = trimmed.slice(i + 1).trim();
    if ((value.startsWith('"') && value.endsWith('"')) || (value.startsWith("'") && value.endsWith("'"))) {
      value = value.slice(1, -1);
    }
    if (process.env[key] === undefined) process.env[key] = value;
  }
}

function splitSql(sql) {
  return sql
    .split(/;\s*(?:\r?\n|$)/)
    .map((statement) => statement.trim())
    .filter((statement) => statement && !statement.split(/\r?\n/).every((line) => !line.trim() || line.trim().startsWith('--')));
}

async function count(conn, table) {
  const [rows] = await conn.query(`SELECT COUNT(*) AS c FROM \`${table}\``);
  return rows[0].c;
}

async function main() {
  loadEnv(path.join(root, '.env'));

  const conn = await mysql.createConnection({
    host: process.env.MYSQL_HOST || '127.0.0.1',
    port: Number(process.env.MYSQL_PORT || 3306),
    user: process.env.MYSQL_USER || 'root',
    password: process.env.MYSQL_PASSWORD ?? '',
    multipleStatements: false,
    charset: 'utf8mb4',
  });

  const schema = fs.readFileSync(path.join(root, 'server', 'schema.sql'), 'utf8');
  for (const statement of splitSql(schema)) {
    await conn.query(statement);
  }
  await conn.query('USE attack_console');

  if ((await count(conn, 'devices')) === 0) {
    const devices = generateDeviceDB();
    const rows = devices.map((d) => [
      d.deviceId, d.deviceModel, d.osVersion, d.osArch, d.browserName, d.browserVersion,
      d.userAgent, d.screenResolution, d.colorDepth, d.devicePixelRatio, d.platform,
      d.hardwareConcurrency, d.deviceMemory, d.touchSupport ? 1 : 0, d.webGLRenderer,
      d.audioContextFingerprint, d.canvasFingerprint, d.timezone, d.language,
      d.cookieEnabled ? 1 : 0, d.localStorageEnabled ? 1 : 0, d.webrtcLocalIP, d.fontListHash,
    ]);
    await conn.query(
      `INSERT INTO devices (
        device_code, device_model, os_version, os_arch, browser_name, browser_version,
        user_agent, screen_resolution, color_depth, device_pixel_ratio, platform,
        hardware_concurrency, device_memory, touch_support, webgl_renderer,
        audio_context_fingerprint, canvas_fingerprint, timezone, language,
        cookie_enabled, local_storage_enabled, webrtc_local_ip, font_list_hash
      ) VALUES ?`,
      [rows],
    );
  }

  if ((await count(conn, 'network_exits')) === 0) {
    const rows = NETWORK_DB.map((n) => [n.ip, n.ipType, n.region, n.isp, n.asn]);
    await conn.query(
      `INSERT INTO network_exits (ip, ip_type, region, isp, asn) VALUES ?`,
      [rows],
    );
  }

  if ((await count(conn, 'phone_numbers')) === 0) {
    const rows = [];
    for (let n = 1; n <= PHONE_COUNT; n += 1) {
      rows.push([`138${String(n).padStart(8, '0')}`]);
    }
    await conn.query('INSERT INTO phone_numbers (phone) VALUES ?', [rows]);
  }

  const tables = ['devices', 'network_exits', 'phone_numbers', 'batches', 'synthetic_devices', 'accounts', 'submissions'];
  const summary = {};
  for (const table of tables) summary[table] = await count(conn, table);
  console.log(JSON.stringify(summary));
  await conn.end();
}

main().catch((err) => {
  console.error(err.message);
  process.exit(1);
});
