-- 数据库服务器初始化脚本
-- 创建数据库和表结构

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `user_test` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

USE `user_test`;

-- 用户数据表
CREATE TABLE IF NOT EXISTS `users_data` (
  `username` VARCHAR(50) NOT NULL,
  `password` VARCHAR(100) NOT NULL,
  `owned_device_key` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`username`),
  UNIQUE KEY `owned_device_key` (`owned_device_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 设备密钥表
CREATE TABLE IF NOT EXISTS `device_key` (
  `key_id` VARCHAR(50) NOT NULL,
  `owned_by_user` VARCHAR(50) DEFAULT NULL,
  `is_used` TINYINT(1) DEFAULT 0,
  PRIMARY KEY (`key_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 设备数据表
CREATE TABLE IF NOT EXISTS `device_data` (
  `device_name` VARCHAR(50) NOT NULL,
  `bind_device_key` VARCHAR(50) NOT NULL,
  PRIMARY KEY (`device_name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- 插入示例数据
-- 插入默认用户
INSERT IGNORE INTO `users_data` (`username`, `password`, `owned_device_key`)
VALUES ('Jiang', 'pwd', 'A1');

-- 插入设备密钥
INSERT IGNORE INTO `device_key` (`key_id`, `owned_by_user`, `is_used`)
VALUES 
  ('A1', 'Jiang', 1),
  ('A2', NULL, 0),
  ('A3', NULL, 0);

-- 插入设备数据
INSERT IGNORE INTO `device_data` (`device_name`, `bind_device_key`)
VALUES 
  ('A1_tem_hum', 'A1'),
  ('A1_curtain', 'A1'),
  ('A1_security', 'A1'),
  ('A2_tem_hum', 'A2'),
  ('A2_curtain', 'A2'),
  ('A3_tem_hum', 'A3');

-- 显示表结构
DESCRIBE `users_data`;
DESCRIBE `device_key`;
DESCRIBE `device_data`;

-- 显示示例数据
SELECT '=== 用户数据 ===' AS '';
SELECT * FROM `users_data`;
SELECT '=== 设备密钥 ===' AS '';
SELECT * FROM `device_key`;
SELECT '=== 设备数据 ===' AS '';
SELECT * FROM `device_data`;
