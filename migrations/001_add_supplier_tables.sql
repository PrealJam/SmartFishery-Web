-- ============================================================
-- SmartFishery 多身份系统 & 供应商管理迁移脚本
-- 迁移版本: 001
-- 目标: 添加供应商、鱼苗产品、库存、采购订单相关表
-- 日期: 2026-04-18
-- ============================================================

-- 确保使用 utf8mb4 编码
/*!40101 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;

-- ============================================================
-- 步骤1: 修改 users 表 - 添加 supplier_id 字段
-- ============================================================
ALTER TABLE `users` 
ADD COLUMN `supplier_id` INT NULL COMMENT '供应商关联编号（仅供应商用户有值）' AFTER `role`,
ADD COLUMN `full_name` VARCHAR(100) COLLATE utf8mb4_unicode_ci COMMENT '真实姓名' AFTER `email`,
ADD INDEX `idx_supplier_id` (`supplier_id`),
MODIFY COLUMN `role` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT 'operator' COMMENT '用户角色（admin管理员、operator操作员、viewer观察员、supplier供应商）';

-- ============================================================
-- 步骤2: 修改 ponds 表 - 添加常用供应商字段
-- ============================================================
ALTER TABLE `ponds` 
ADD COLUMN `default_supplier_id` INT NULL COMMENT '常用供应商编号' AFTER `status`;

-- ============================================================
-- 步骤3: 创建 suppliers 表 - 供应商企业信息
-- ============================================================
CREATE TABLE `suppliers` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '供应商唯一编号',
  `name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '供应商企业名称',
  `contact_person` VARCHAR(50) COLLATE utf8mb4_unicode_ci COMMENT '主要联系人姓名',
  `phone` VARCHAR(20) COLLATE utf8mb4_unicode_ci COMMENT '联系电话',
  `email` VARCHAR(100) COLLATE utf8mb4_unicode_ci COMMENT '联系邮箱',
  `address` VARCHAR(255) COLLATE utf8mb4_unicode_ci COMMENT '企业地址',
  `registration_date` DATE COMMENT '注册时间',
  `status` VARCHAR(20) COLLATE utf8mb4_unicode_ci DEFAULT 'active' COMMENT '供应商状态（active激活、inactive停用、suspended暂停）',
  `notes` TEXT COLLATE utf8mb4_unicode_ci COMMENT '备注信息',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录最后更新时间',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_name` (`name`),
  KEY `idx_status` (`status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='供应商企业信息表';

-- ============================================================
-- 步骤4: 创建 seedling_products 表 - 鱼苗产品库
-- ============================================================
CREATE TABLE `seedling_products` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '鱼苗产品唯一编号',
  `supplier_id` INT NOT NULL COMMENT '所属供应商编号',
  `product_name` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '产品名称（如"一龄草鱼苗"）',
  `species` VARCHAR(50) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '鱼苗种类（草鱼、鲈鱼、鲤鱼等）',
  `grade` VARCHAR(50) COLLATE utf8mb4_unicode_ci COMMENT '鱼苗等级（一龄、二龄、健康、优质等）',
  `unit_price` DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '单价（元/尾）',
  `cost_price` DECIMAL(10, 2) COMMENT '成本价（元/尾）',
  `growth_cycle_days` INT COMMENT '生长周期（天）',
  `survival_rate` FLOAT COMMENT '存活率（%）',
  `image_url` VARCHAR(255) COLLATE utf8mb4_unicode_ci COMMENT '产品图片URL',
  `description` TEXT COLLATE utf8mb4_unicode_ci COMMENT '产品详细描述',
  `is_active` TINYINT(1) DEFAULT 1 COMMENT '产品是否上架（1上架、0下架）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录最后更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_species` (`species`),
  KEY `idx_is_active` (`is_active`),
  KEY `idx_created_at` (`created_at`),
  CONSTRAINT `fk_seedling_products_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='鱼苗产品库表';

-- ============================================================
-- 步骤5: 创建 seedling_inventory 表 - 库存管理
-- ============================================================
CREATE TABLE `seedling_inventory` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '库存记录唯一编号',
  `supplier_id` INT NOT NULL COMMENT '供应商编号',
  `product_id` INT NOT NULL COMMENT '产品编号',
  `quantity` INT NOT NULL DEFAULT 0 COMMENT '当前库存数量（尾）',
  `last_updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '最后更新时间',
  `updated_by` VARCHAR(50) COLLATE utf8mb4_unicode_ci COMMENT '更新人（用户名）',
  PRIMARY KEY (`id`),
  UNIQUE KEY `unique_supplier_product` (`supplier_id`, `product_id`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_product_id` (`product_id`),
  KEY `idx_supplier_product` (`supplier_id`, `product_id`),
  CONSTRAINT `fk_inventory_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_inventory_product` FOREIGN KEY (`product_id`) REFERENCES `seedling_products` (`id`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='鱼苗库存表';

-- ============================================================
-- 步骤6: 创建 purchase_orders 表 - 采购订单主表
-- ============================================================
CREATE TABLE `purchase_orders` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '采购订单唯一编号',
  `supplier_id` INT NOT NULL COMMENT '供应商编号',
  `pond_id` INT NOT NULL COMMENT '目标鱼池编号',
  `created_by` INT NOT NULL COMMENT '创建者用户编号',
  `order_date` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '订单下单时间',
  `expected_delivery_date` DATE COMMENT '预期交货日期',
  `actual_delivery_date` DATE COMMENT '实际交货日期',
  `status` VARCHAR(50) COLLATE utf8mb4_unicode_ci DEFAULT 'draft' COMMENT '订单状态（draft草稿、confirmed已确认、shipped已发货、received已收货、invoiced已对账、cancelled已取消）',
  `total_amount` DECIMAL(12, 2) DEFAULT 0 COMMENT '订单总金额（元）',
  `notes` TEXT COLLATE utf8mb4_unicode_ci COMMENT '订单备注',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  `updated_at` DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '记录最后更新时间',
  PRIMARY KEY (`id`),
  KEY `idx_supplier_id` (`supplier_id`),
  KEY `idx_pond_id` (`pond_id`),
  KEY `idx_status` (`status`),
  KEY `idx_order_date` (`order_date`),
  KEY `idx_created_by` (`created_by`),
  KEY `idx_supplier_status` (`supplier_id`, `status`),
  CONSTRAINT `fk_order_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_order_pond` FOREIGN KEY (`pond_id`) REFERENCES `ponds` (`id`) ON DELETE RESTRICT,
  CONSTRAINT `fk_order_creator` FOREIGN KEY (`created_by`) REFERENCES `users` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购订单主表';

-- ============================================================
-- 步骤7: 创建 order_items 表 - 订单详情（订单项目）
-- ============================================================
CREATE TABLE `order_items` (
  `id` INT NOT NULL AUTO_INCREMENT COMMENT '订单项唯一编号',
  `order_id` INT NOT NULL COMMENT '订单编号',
  `product_id` INT NOT NULL COMMENT '产品编号',
  `quantity` INT NOT NULL DEFAULT 0 COMMENT '采购数量（尾）',
  `unit_price` DECIMAL(10, 2) NOT NULL DEFAULT 0 COMMENT '单价（元/尾）',
  `subtotal` DECIMAL(12, 2) GENERATED ALWAYS AS (quantity * unit_price) STORED COMMENT '小计（自动计算）',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '记录创建时间',
  PRIMARY KEY (`id`),
  KEY `idx_order_id` (`order_id`),
  KEY `idx_product_id` (`product_id`),
  CONSTRAINT `fk_item_order` FOREIGN KEY (`order_id`) REFERENCES `purchase_orders` (`id`) ON DELETE CASCADE,
  CONSTRAINT `fk_item_product` FOREIGN KEY (`product_id`) REFERENCES `seedling_products` (`id`) ON DELETE RESTRICT
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='采购订单详情表';

-- ============================================================
-- 步骤8: 为已存在的 ponds 和 users 表添加外键约束
-- ============================================================
ALTER TABLE `ponds` 
ADD CONSTRAINT `fk_pond_default_supplier` FOREIGN KEY (`default_supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL;

ALTER TABLE `users` 
ADD CONSTRAINT `fk_user_supplier` FOREIGN KEY (`supplier_id`) REFERENCES `suppliers` (`id`) ON DELETE SET NULL;

-- ============================================================
-- 步骤9: 创建系统审计日志表（如果不存在）
-- ============================================================
CREATE TABLE IF NOT EXISTS `system_logs` (
  `id` BIGINT NOT NULL AUTO_INCREMENT COMMENT '日志唯一编号',
  `user_id` INT COMMENT '操作用户编号',
  `action` VARCHAR(100) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT '操作类型（如create_order、update_inventory等）',
  `resource_type` VARCHAR(50) COLLATE utf8mb4_unicode_ci COMMENT '操作的资源类型（如purchase_order、seedling_product）',
  `resource_id` INT COMMENT '资源编号',
  `old_value` TEXT COLLATE utf8mb4_unicode_ci COMMENT '修改前的值（JSON格式）',
  `new_value` TEXT COLLATE utf8mb4_unicode_ci COMMENT '修改后的值（JSON格式）',
  `ip_address` VARCHAR(50) COLLATE utf8mb4_unicode_ci COMMENT '操作者IP地址',
  `created_at` DATETIME DEFAULT CURRENT_TIMESTAMP COMMENT '操作时间',
  PRIMARY KEY (`id`),
  KEY `idx_user_id` (`user_id`),
  KEY `idx_action` (`action`),
  KEY `idx_resource_type` (`resource_type`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统审计日志表';

-- ============================================================
-- 迁移完成标记
-- ============================================================
-- 执行完上述SQL后，所有新表和字段将创建完成
-- 下一步: 更新 app.py 中的 ORM 模型定义
-- 最后: 执行 seed_data.py 创建测试数据
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
