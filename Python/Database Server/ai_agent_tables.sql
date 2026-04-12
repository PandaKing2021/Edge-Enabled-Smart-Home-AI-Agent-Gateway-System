-- AI Agent数据库扩展脚本
-- 为对话式任务自动编排系统新增表结构

USE `user_test`;

-- 对话历史表
CREATE TABLE IF NOT EXISTS `conversation_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` VARCHAR(36) NOT NULL COMMENT '会话ID(UUID)',
  `user_id` VARCHAR(50) DEFAULT NULL COMMENT '用户ID',
  `user_input` TEXT NOT NULL COMMENT '用户输入',
  `agent_response` TEXT COMMENT 'Agent响应',
  `context_before` TEXT COMMENT '执行前上下文(JSON)',
  `context_after` TEXT COMMENT '执行后上下文(JSON)',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  INDEX `idx_session` (`session_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI Agent对话历史记录表';

-- 用户偏好表
CREATE TABLE IF NOT EXISTS `user_preferences` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` VARCHAR(50) NOT NULL COMMENT '用户ID',
  `scenario` VARCHAR(50) NOT NULL COMMENT '场景标识(如sleep,movie)',
  `device` VARCHAR(50) NOT NULL COMMENT '设备ID',
  `action` VARCHAR(50) NOT NULL COMMENT '动作名称',
  `parameter` VARCHAR(50) NOT NULL COMMENT '参数名称',
  `preferred_value` VARCHAR(100) NOT NULL COMMENT '偏好值',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
  UNIQUE KEY `uk_user_scenario_device_action_param` (`user_id`, `scenario`, `device`, `action`, `parameter`),
  INDEX `idx_user_scenario` (`user_id`, `scenario`),
  INDEX `idx_scenario` (`scenario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户偏好学习表';

-- 任务执行日志表(可选,用于统计分析)
CREATE TABLE IF NOT EXISTS `task_execution_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` VARCHAR(36) NOT NULL COMMENT '会话ID',
  `user_id` VARCHAR(50) DEFAULT NULL COMMENT '用户ID',
  `user_input` TEXT NOT NULL COMMENT '用户输入',
  `task_plan` TEXT COMMENT '任务计划(JSON)',
  `execution_result` TEXT COMMENT '执行结果(JSON)',
  `success` TINYINT(1) DEFAULT 0 COMMENT '是否成功',
  `error_message` TEXT COMMENT '错误信息',
  `execution_time_ms` INT COMMENT '执行耗时(毫秒)',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  INDEX `idx_session` (`session_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='任务执行日志表';

-- 显示新表结构
SELECT '=== 对话历史表 ===' AS '';
DESCRIBE `conversation_history`;

SELECT '=== 用户偏好表 ===' AS '';
DESCRIBE `user_preferences`;

SELECT '=== 任务执行日志表 ===' AS '';
DESCRIBE `task_execution_log`;
