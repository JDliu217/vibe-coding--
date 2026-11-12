-- 攻击方账本 attack_console
-- 一个库、三组表。资源组启动时灌入；制造组和发出组先建空表，等 API 写入。

CREATE DATABASE IF NOT EXISTS attack_console
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

USE attack_console;

-- 资源组：有限、固定的真实设备、出口 IP、手机号
CREATE TABLE IF NOT EXISTS devices (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  device_code VARCHAR(32) NOT NULL,
  device_model VARCHAR(64) NOT NULL,
  os_version VARCHAR(64) NOT NULL,
  os_arch VARCHAR(16) NOT NULL,
  browser_name VARCHAR(32) NOT NULL,
  browser_version VARCHAR(32) NOT NULL,
  user_agent VARCHAR(255) NOT NULL,
  screen_resolution VARCHAR(32) NOT NULL,
  color_depth TINYINT UNSIGNED NOT NULL,
  device_pixel_ratio TINYINT UNSIGNED NOT NULL,
  platform VARCHAR(32) NOT NULL,
  hardware_concurrency TINYINT UNSIGNED NOT NULL,
  device_memory TINYINT UNSIGNED NOT NULL,
  touch_support TINYINT(1) NOT NULL,
  webgl_renderer VARCHAR(64) NOT NULL,
  audio_context_fingerprint VARCHAR(32) NOT NULL,
  canvas_fingerprint VARCHAR(32) NOT NULL,
  timezone VARCHAR(64) NOT NULL,
  language VARCHAR(32) NOT NULL,
  cookie_enabled TINYINT(1) NOT NULL,
  local_storage_enabled TINYINT(1) NOT NULL,
  webrtc_local_ip VARCHAR(45) NOT NULL,
  font_list_hash VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_devices_code (device_code)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS network_exits (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  ip VARCHAR(45) NOT NULL,
  ip_type VARCHAR(32) NOT NULL,
  region VARCHAR(64) NOT NULL,
  isp VARCHAR(64) NOT NULL,
  asn VARCHAR(16) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_network_exits_ip (ip)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS phone_numbers (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  phone CHAR(11) NOT NULL,
  status ENUM('available', 'assigned') NOT NULL DEFAULT 'available',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_phone_numbers_phone (phone),
  KEY idx_phone_numbers_status (status)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 制造组：一次任务、由真实设备派生的仿真设备号、再绑定出的待注册账号
CREATE TABLE IF NOT EXISTS batches (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  reuse_intensity DECIMAL(4,3) NOT NULL,
  batch_size INT UNSIGNED NOT NULL,
  interval_ms INT UNSIGNED NOT NULL,
  status ENUM('running', 'done') NOT NULL DEFAULT 'running',
  round_count INT UNSIGNED NOT NULL DEFAULT 0,
  started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  stopped_at TIMESTAMP NULL DEFAULT NULL,
  PRIMARY KEY (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS synthetic_devices (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  batch_id INT UNSIGNED NOT NULL,
  parent_device_id INT UNSIGNED NOT NULL,
  synthetic_code VARCHAR(32) NOT NULL,
  device_model VARCHAR(64) NOT NULL,
  os_version VARCHAR(64) NOT NULL,
  os_arch VARCHAR(16) NOT NULL,
  browser_name VARCHAR(32) NOT NULL,
  browser_version VARCHAR(32) NOT NULL,
  user_agent VARCHAR(255) NOT NULL,
  screen_resolution VARCHAR(32) NOT NULL,
  color_depth TINYINT UNSIGNED NOT NULL,
  device_pixel_ratio TINYINT UNSIGNED NOT NULL,
  platform VARCHAR(32) NOT NULL,
  hardware_concurrency TINYINT UNSIGNED NOT NULL,
  device_memory TINYINT UNSIGNED NOT NULL,
  touch_support TINYINT(1) NOT NULL,
  webgl_renderer VARCHAR(64) NOT NULL,
  audio_context_fingerprint VARCHAR(32) NOT NULL,
  canvas_fingerprint VARCHAR(32) NOT NULL,
  timezone VARCHAR(64) NOT NULL,
  language VARCHAR(32) NOT NULL,
  cookie_enabled TINYINT(1) NOT NULL,
  local_storage_enabled TINYINT(1) NOT NULL,
  webrtc_local_ip VARCHAR(45) NOT NULL,
  font_list_hash VARCHAR(32) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_synthetic_devices_code (synthetic_code),
  KEY idx_synthetic_devices_batch (batch_id),
  CONSTRAINT fk_synthetic_devices_batch
    FOREIGN KEY (batch_id) REFERENCES batches (id),
  CONSTRAINT fk_synthetic_devices_parent
    FOREIGN KEY (parent_device_id) REFERENCES devices (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS accounts (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  batch_id INT UNSIGNED NOT NULL,
  synthetic_device_id INT UNSIGNED NOT NULL,
  phone_number_id INT UNSIGNED NOT NULL,
  network_exit_id INT UNSIGNED NOT NULL,
  email VARCHAR(128) NOT NULL,
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uk_accounts_synthetic_device (synthetic_device_id),
  UNIQUE KEY uk_accounts_phone (phone_number_id),
  KEY idx_accounts_batch (batch_id),
  CONSTRAINT fk_accounts_batch
    FOREIGN KEY (batch_id) REFERENCES batches (id),
  CONSTRAINT fk_accounts_synthetic_device
    FOREIGN KEY (synthetic_device_id) REFERENCES synthetic_devices (id),
  CONSTRAINT fk_accounts_phone
    FOREIGN KEY (phone_number_id) REFERENCES phone_numbers (id),
  CONSTRAINT fk_accounts_network
    FOREIGN KEY (network_exit_id) REFERENCES network_exits (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 发出组：准备交给防守方的快照。结果先是占位，不是风控判定。
CREATE TABLE IF NOT EXISTS submissions (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  batch_id INT UNSIGNED NOT NULL,
  account_id INT UNSIGNED NOT NULL,
  payload_json JSON NOT NULL,
  status ENUM('success', 'failed') NOT NULL,
  failure_reason VARCHAR(255) NULL,
  result_source VARCHAR(32) NOT NULL DEFAULT 'placeholder',
  created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  KEY idx_submissions_batch (batch_id),
  KEY idx_submissions_created (created_at),
  CONSTRAINT fk_submissions_batch
    FOREIGN KEY (batch_id) REFERENCES batches (id),
  CONSTRAINT fk_submissions_account
    FOREIGN KEY (account_id) REFERENCES accounts (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
