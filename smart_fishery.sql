-- ============================================================
-- 智慧渔场管理系统数据库脚本
-- Smart Fishery Management System Database Schema
-- ============================================================

-- 创建数据库
CREATE DATABASE IF NOT EXISTS `smart_fishery_db` 
CHARACTER SET utf8mb4 
COLLATE utf8mb4_unicode_ci;

-- 选择使用数据库
USE `smart_fishery_db`;

-- ============================================================
-- 表1: ponds (鱼池基本信息表)
-- 用于记录渔场内所有池塘的基础档案信息
-- ============================================================
CREATE TABLE IF NOT EXISTS `ponds` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '鱼池唯一编号，自增',
  `pond_name` VARCHAR(100) NOT NULL UNIQUE COMMENT '鱼池名称（如"一号池"）',
  `fish_type` VARCHAR(50) NOT NULL COMMENT '养殖鱼类种类（如"草鱼"、"鲈鱼"）',
  `fish_count` INT DEFAULT 0 COMMENT '当前鱼类估计数量（尾）',
  `volume` FLOAT DEFAULT 0.0 COMMENT '鱼池体积容量（立方米）',
  `status` VARCHAR(20) DEFAULT '正常' COMMENT '鱼池状态（如"正常"、"维护中"、"空闲"）',
  `location` VARCHAR(255) COMMENT '鱼池位置描述',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录最后更新时间',
  INDEX `idx_status` (`status`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='鱼池基本信息表';

-- ============================================================
-- 表2: sensor_data (传感器水质监测数据表)
-- 用于存储由各类水质传感器高频次上报的实时环境监测数据
-- ============================================================
CREATE TABLE IF NOT EXISTS `sensor_data` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '数据记录唯一编号，自增',
  `pond_id` INT NOT NULL COMMENT '关联的鱼池编号(ponds.id)',
  `temperature` FLOAT COMMENT '水温（℃）',
  `ph_value` FLOAT COMMENT '水体pH值',
  `dissolved_oxygen` FLOAT COMMENT '溶解氧浓度（mg/L）',
  `salinity` FLOAT COMMENT '盐度（‰）',
  `ammonia_nitrogen` FLOAT COMMENT '氨氮含量（mg/L）',
  `nitrite_nitrogen` FLOAT COMMENT '亚硝酸盐（mg/L）',
  `recorded_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '传感器数据采集时间',
  FOREIGN KEY (`pond_id`) REFERENCES `ponds`(`id`) ON DELETE CASCADE,
  INDEX `idx_pond_id` (`pond_id`),
  INDEX `idx_recorded_at` (`recorded_at`),
  INDEX `idx_pond_recorded` (`pond_id`, `recorded_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='传感器水质监测数据表';

-- ============================================================
-- 表3: devices (硬件设备信息表)
-- 记录渔场内部署的所有可控硬件设备的基础信息与当前状态
-- ============================================================
CREATE TABLE IF NOT EXISTS `devices` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '设备唯一编号，自增',
  `pond_id` INT NOT NULL COMMENT '设备对应所在的鱼池编号',
  `device_name` VARCHAR(100) NOT NULL COMMENT '设备名称（如"1号增氧机"）',
  `device_type` VARCHAR(50) NOT NULL COMMENT '设备类型（增氧机、投喂机、水泵、温控等）',
  `device_model` VARCHAR(100) COMMENT '设备型号规格',
  `status` VARCHAR(20) DEFAULT '离线' COMMENT '当前运行状态（在线、离线、运行、停止、故障）',
  `power_consumption` FLOAT DEFAULT 0.0 COMMENT '额定功率（瓦特）',
  `last_active` DATETIME COMMENT '设备最后一次心跳或活跃时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '设备添加时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '设备信息最后更新时间',
  FOREIGN KEY (`pond_id`) REFERENCES `ponds`(`id`) ON DELETE CASCADE,
  INDEX `idx_pond_id` (`pond_id`),
  INDEX `idx_device_type` (`device_type`),
  INDEX `idx_status` (`status`),
  INDEX `idx_last_active` (`last_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='硬件设备信息表';

-- ============================================================
-- 表4: device_logs (设备操作与告警日志表)
-- 详细记录系统中所有设备的启停控制操作日志、自动化联动执行记录及故障报警信息
-- ============================================================
CREATE TABLE IF NOT EXISTS `device_logs` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志唯一编号，自增',
  `device_id` INT NOT NULL COMMENT '关联的设备编号(devices.id)',
  `pond_id` INT NOT NULL COMMENT '关联的鱼池编号(ponds.id)',
  `action` VARCHAR(50) NOT NULL COMMENT '执行的具体动作（如"开启"、"关闭"、"报警"、"自动触发"）',
  `operator` VARCHAR(100) COMMENT '操作来源（如"admin手动"、"系统自动触发"、"自动化规则"）',
  `previous_state` VARCHAR(20) COMMENT '操作前设备状态',
  `current_state` VARCHAR(20) COMMENT '操作后设备状态',
  `details` TEXT COMMENT '详细描述信息',
  `log_time` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作或事件发生时间',
  FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`pond_id`) REFERENCES `ponds`(`id`) ON DELETE CASCADE,
  INDEX `idx_device_id` (`device_id`),
  INDEX `idx_pond_id` (`pond_id`),
  INDEX `idx_log_time` (`log_time`),
  INDEX `idx_action` (`action`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备操作与告警日志表';

-- ============================================================
-- 表5: users (用户管理表)
-- 系统用户账号与权限管理
-- ============================================================
CREATE TABLE IF NOT EXISTS `users` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '用户唯一编号',
  `username` VARCHAR(50) NOT NULL UNIQUE COMMENT '用户名（登录用）',
  `email` VARCHAR(100) UNIQUE COMMENT '用户邮箱',
  `password_hash` VARCHAR(255) NOT NULL COMMENT '密码哈希值（bcrypt加密）',
  `full_name` VARCHAR(100) COMMENT '用户真实姓名',
  `role` VARCHAR(50) DEFAULT 'operator' COMMENT '用户角色（admin管理员、operator操作员、viewer观察员）',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '用户账号是否激活',
  `last_login` DATETIME COMMENT '上次登录时间',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '账号创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '账号最后更新时间',
  INDEX `idx_username` (`username`),
  INDEX `idx_role` (`role`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='用户管理表';

-- ============================================================
-- 表6: device_control_rules (设备自动化控制规则表)
-- 存储针对水质指标的智能联动控制规则
-- ============================================================
CREATE TABLE IF NOT EXISTS `device_control_rules` (
  `id` INT AUTO_INCREMENT PRIMARY KEY COMMENT '规则编号',
  `rule_name` VARCHAR(100) NOT NULL COMMENT '规则名称（如"溶氧过低自动增氧"）',
  `pond_id` INT NOT NULL COMMENT '适用的鱼池编号',
  `device_id` INT NOT NULL COMMENT '要控制的设备编号',
  `trigger_type` VARCHAR(50) COMMENT '触发条件类型（dissolved_oxygen、temperature、ph_value等）',
  `trigger_threshold_min` FLOAT COMMENT '触发最小阈值',
  `trigger_threshold_max` FLOAT COMMENT '触发最大阈值',
  `action_on_trigger` VARCHAR(50) COMMENT '触发时执行的动作（如"开启"、"关闭"）',
  `is_active` BOOLEAN DEFAULT TRUE COMMENT '规则是否启用',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '规则创建时间',
  FOREIGN KEY (`pond_id`) REFERENCES `ponds`(`id`) ON DELETE CASCADE,
  FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE CASCADE,
  INDEX `idx_pond_id` (`pond_id`),
  INDEX `idx_device_id` (`device_id`),
  INDEX `idx_is_active` (`is_active`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='设备自动化控制规则表';

-- ============================================================
-- 表7: alarms (告警事件表)
-- 记录系统产生的各类告警事件
-- ============================================================
CREATE TABLE IF NOT EXISTS `alarms` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '告警编号',
  `alarm_type` VARCHAR(50) NOT NULL COMMENT '告警类型（水质告警、设备报警、系统告警）',
  `pond_id` INT COMMENT '相关的鱼池编号',
  `device_id` INT COMMENT '相关的设备编号',
  `severity` VARCHAR(20) DEFAULT '中' COMMENT '告警等级（低、中、高、严重）',
  `message` TEXT NOT NULL COMMENT '告警消息内容',
  `status` VARCHAR(20) DEFAULT '未处理' COMMENT '告警状态（未处理、处理中、已处理、已忽略）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '告警产生时间',
  `resolved_at` DATETIME COMMENT '告警解决时间',
  FOREIGN KEY (`pond_id`) REFERENCES `ponds`(`id`) ON DELETE SET NULL,
  FOREIGN KEY (`device_id`) REFERENCES `devices`(`id`) ON DELETE SET NULL,
  INDEX `idx_alarm_type` (`alarm_type`),
  INDEX `idx_pond_id` (`pond_id`),
  INDEX `idx_severity` (`severity`),
  INDEX `idx_status` (`status`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警事件表';

-- ============================================================
-- 表8: system_logs (系统操作日志表)
-- 记录所有用户操作行为与系统重要事件
-- ============================================================
CREATE TABLE IF NOT EXISTS `system_logs` (
  `id` BIGINT AUTO_INCREMENT PRIMARY KEY COMMENT '日志编号',
  `user_id` INT COMMENT '执行操作的用户编号',
  `action` VARCHAR(100) NOT NULL COMMENT '执行的操作名称',
  `resource_type` VARCHAR(50) COMMENT '操作涉及的资源类型（如pond、device、user）',
  `resource_id` INT COMMENT '操作涉及的资源编号',
  `details` TEXT COMMENT '操作详细信息',
  `ip_address` VARCHAR(50) COMMENT '操作来源IP地址',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作执行时间',
  FOREIGN KEY (`user_id`) REFERENCES `users`(`id`) ON DELETE SET NULL,
  INDEX `idx_user_id` (`user_id`),
  INDEX `idx_resource_type` (`resource_type`),
  INDEX `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统操作日志表';

-- ============================================================
-- 索引说明
-- ============================================================
-- 
-- 表 ponds 的索引：
--   - idx_status: 用于快速查询特定状态的鱼池
--   - idx_created_at: 用于时间序列查询
--
-- 表 sensor_data 的索引：
--   - idx_pond_id: 单池快查
--   - idx_recorded_at: 时间范围查询
--   - idx_pond_recorded: 复合索引，用于快速查询特定鱼池的历史数据
--
-- 表 devices 的索引：
--   - idx_pond_id: 鱼池内设备快查
--   - idx_device_type: 设备类型统计
--   - idx_status: 设备状态过滤
--   - idx_last_active: 离线设备检测
--
-- ============================================================

-- ============================================================
-- 初始化测试数据（可选）
-- ============================================================

-- 插入示例鱼池数据
INSERT INTO `ponds` (`pond_name`, `fish_type`, `fish_count`, `volume`, `status`) VALUES
('一号池', '草鱼', 5000, 500.0, '正常'),
('二号池', '鲈鱼', 3000, 300.0, '正常'),
('三号池', '鲤鱼', 4000, 400.0, '维护中');

-- 插入示例设备数据
INSERT INTO `devices` (`pond_id`, `device_name`, `device_type`, `device_model`, `status`, `power_consumption`) VALUES
(1, '1号增氧机', '增氧机', 'AX-5000', '在线', 2200.0),
(1, '1号投喂机', '投喂机', 'FX-2000', '在线', 500.0),
(2, '2号增氧机', '增氧机', 'AX-3000', '离线', 1500.0),
(2, '2号水泵', '水泵', 'PX-1000', '在线', 750.0);

-- 插入示例用户数据
-- 密码：admin123 (bcrypt 哈希后的值，这里仅作示意，实际需要生成真正的哈希值)
INSERT INTO `users` (`username`, `email`, `password_hash`, `full_name`, `role`, `is_active`) VALUES
('admin', 'admin@smartfishery.com', '$2b$12$WQQSsJ0B8h/sj8i8sj8i8ejXmM5DK5DK5DK5DK5DK', '系统管理员', 'admin', TRUE),
('operator001', 'op001@smartfishery.com', '$2b$12$WQQSsJ0B8h/sj8i8sj8i8ejXmM5DK5DK5DK5DK5DK', '渔场操作员', 'operator', TRUE),
('viewer001', 'view001@smartfishery.com', '$2b$12$WQQSsJ0B8h/sj8i8sj8i8ejXmM5DK5DK5DK5DK5DK', '数据观察员', 'viewer', TRUE);

-- ============================================================
-- 数据库初始化完成
-- ============================================================
