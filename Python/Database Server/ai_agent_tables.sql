-- AI Agent database extension script
-- Add table structure for conversational task orchestration system

USE `user_test`;

-- Conversation history table
CREATE TABLE IF NOT EXISTS `conversation_history` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` VARCHAR(36) NOT NULL COMMENT 'Session ID(UUID)',
  `user_id` VARCHAR(50) DEFAULT NULL COMMENT 'User ID',
  `user_input` TEXT NOT NULL COMMENT 'User input',
  `agent_response` TEXT COMMENT 'Agent response',
  `context_before` TEXT COMMENT 'Context before execution(JSON)',
  `context_after` TEXT COMMENT 'Context after execution(JSON)',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp',
  INDEX `idx_session` (`session_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='AI Agent conversation history table';

-- User preference table
CREATE TABLE IF NOT EXISTS `user_preferences` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `user_id` VARCHAR(50) NOT NULL COMMENT 'User ID',
  `scenario` VARCHAR(50) NOT NULL COMMENT 'Scenario identifier(like sleep,movie)',
  `device` VARCHAR(50) NOT NULL COMMENT 'Device ID',
  `action` VARCHAR(50) NOT NULL COMMENT 'Action name',
  `parameter` VARCHAR(50) NOT NULL COMMENT 'Parameter name',
  `preferred_value` VARCHAR(100) NOT NULL COMMENT 'Preferred value',
  `created_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Creation time',
  `updated_at` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT 'Update time',
  UNIQUE KEY `uk_user_scenario_device_action_param` (`user_id`, `scenario`, `device`, `action`, `parameter`),
  INDEX `idx_user_scenario` (`user_id`, `scenario`),
  INDEX `idx_scenario` (`scenario`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User preference learning table';

-- Task execution log table(optional, for statistical analysis)
CREATE TABLE IF NOT EXISTS `task_execution_log` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `session_id` VARCHAR(36) NOT NULL COMMENT 'Session ID',
  `user_id` VARCHAR(50) DEFAULT NULL COMMENT 'User ID',
  `user_input` TEXT NOT NULL COMMENT 'User input',
  `task_plan` TEXT COMMENT 'Task plan(JSON)',
  `execution_result` TEXT COMMENT 'Execution result(JSON)',
  `success` TINYINT(1) DEFAULT 0 COMMENT 'Whether successful',
  `error_message` TEXT COMMENT 'Error message',
  `execution_time_ms` INT COMMENT 'Execution time(ms)',
  `timestamp` DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT 'Timestamp',
  INDEX `idx_session` (`session_id`),
  INDEX `idx_user` (`user_id`),
  INDEX `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Task execution log table';

-- Show new table structure
SELECT '=== Conversation History Table ===' AS '';
DESCRIBE `conversation_history`;

SELECT '=== User Preferences Table ===' AS '';
DESCRIBE `user_preferences`;

SELECT '=== Task Execution Log Table ===' AS '';
DESCRIBE `task_execution_log`;
