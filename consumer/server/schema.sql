-- 消费端账本 consumer_shop，与攻击方的 attack_console 分开。

CREATE DATABASE IF NOT EXISTS consumer_shop
  CHARACTER SET utf8mb4
  COLLATE utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS consumer_shop.users (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  phone VARCHAR(11) NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_users_phone (phone)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE IF NOT EXISTS consumer_shop.coupons (
  id INT UNSIGNED NOT NULL AUTO_INCREMENT,
  user_id INT UNSIGNED NOT NULL,
  code VARCHAR(16) NOT NULL,
  title VARCHAR(32) NOT NULL,
  amount_cent INT UNSIGNED NOT NULL,
  threshold_cent INT UNSIGNED NOT NULL,
  expires_at DATETIME NOT NULL,
  created_at DATETIME NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uk_coupons_user (user_id),
  UNIQUE KEY uk_coupons_code (code),
  CONSTRAINT fk_coupons_user FOREIGN KEY (user_id) REFERENCES consumer_shop.users (id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
