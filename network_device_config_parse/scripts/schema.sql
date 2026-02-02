-- Network Device Config Parser - PostgreSQL Database Schema
-- 网络设备配置解析系统数据库结构设计

-- ============================================================================
-- 1. 设备元数据表
-- ============================================================================
-- 存储识别出的设备特征信息
CREATE TABLE IF NOT EXISTS device_metadata (
    id SERIAL PRIMARY KEY,
    vendor VARCHAR(50) NOT NULL,              -- 厂商 (Cisco, Huawei, etc.)
    device_type VARCHAR(50) NOT NULL,         -- 设备类型 (Router, Switch, etc.)
    model VARCHAR(100),                       -- 型号 (Catalyst 2960, etc.)
    software_version VARCHAR(100),            -- 软件版本
    config_format VARCHAR(50),               -- 配置格式 (Cisco IOS, Huawei VRP, etc.)

    -- 唯一约束：同一厂商+设备类型+型号+版本组合唯一
    CONSTRAINT unique_device_combo UNIQUE (vendor, device_type, model, software_version),

    -- 创建和更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引：提高查询性能
CREATE INDEX IF NOT EXISTS idx_device_vendor ON device_metadata(vendor);
CREATE INDEX IF NOT EXISTS idx_device_type ON device_metadata(device_type);

-- ============================================================================
-- 2. 解析规则表
-- ============================================================================
-- 存储自动生成的解析正则表达式规则
CREATE TABLE IF NOT EXISTS parsing_rules (
    id SERIAL PRIMARY KEY,
    rule_name VARCHAR(255) NOT NULL UNIQUE,   -- 规则名称
    rule_category VARCHAR(50) NOT NULL,       -- 规则类别 (hostname, interface, vlan, etc.)

    -- 关联设备元数据
    device_metadata_id INTEGER REFERENCES device_metadata(id) ON DELETE CASCADE,

    -- 正则表达式规则
    regex_pattern TEXT NOT NULL,              -- 正则表达式
    pattern_description TEXT,                  -- 规则描述
    priority INTEGER DEFAULT 0,                -- 优先级（数字越小优先级越高）

    -- 规则状态
    is_active BOOLEAN DEFAULT TRUE,            -- 是否启用
    success_rate DECIMAL(5,2) DEFAULT 1.00,    -- 成功率 (0.00-1.00)
    total_attempts INTEGER DEFAULT 0,          -- 总尝试次数
    success_count INTEGER DEFAULT 0,            -- 成功次数

    -- 创建和更新时间
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_rule_category ON parsing_rules(rule_category);
CREATE INDEX IF NOT EXISTS idx_rule_device ON parsing_rules(device_metadata_id);
CREATE INDEX IF NOT EXISTS idx_rule_active ON parsing_rules(is_active);

-- ============================================================================
-- 3. 配置文件表
-- ============================================================================
-- 存储原始配置文件信息
CREATE TABLE IF NOT EXISTS config_files (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,          -- 文件名
    file_path TEXT,                           -- 文件路径（可选）
    file_hash VARCHAR(64) UNIQUE,              -- 文件MD5哈希（去重）
    file_size BIGINT,                         -- 文件大小（字节）

    -- 配置内容（可存储，也可只存路径）
    content TEXT,                              -- 配置文件内容
    content_preview TEXT,                      -- 内容预览（前1000字符）

    -- 关联识别的设备元数据
    identified_device_id INTEGER REFERENCES device_metadata(id) ON DELETE SET NULL,

    -- 文件状态
    is_parsed BOOLEAN DEFAULT FALSE,           -- 是否已解析
    parse_status VARCHAR(20) DEFAULT 'pending', -- 解析状态 (pending, success, failed)

    -- 上传和处理时间
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    parsed_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_config_file_hash ON config_files(file_hash);
CREATE INDEX IF NOT EXISTS idx_config_device ON config_files(identified_device_id);
CREATE INDEX IF NOT EXISTS idx_config_status ON config_files(parse_status);

-- ============================================================================
-- 4. 解析结果表
-- ============================================================================
-- 存储解析出的设备配置数据
CREATE TABLE IF NOT EXISTS parse_results (
    id SERIAL PRIMARY KEY,

    -- 关联配置文件和设备元数据
    config_file_id INTEGER NOT NULL REFERENCES config_files(id) ON DELETE CASCADE,
    device_metadata_id INTEGER REFERENCES device_metadata(id) ON DELETE CASCADE,

    -- 解析质量指标
    quality_score DECIMAL(5,2) NOT NULL,      -- 质量分数 (0.00-1.00)
    completeness_score DECIMAL(5,2),         -- 完整性分数
    accuracy_score DECIMAL(5,2),              -- 准确性分数

    -- 解析状态
    validation_status VARCHAR(20) DEFAULT 'unknown', -- 校验状态 (valid, invalid, unknown)
    validation_warnings TEXT[],               -- 校验警告列表
    validation_errors TEXT[],                  -- 校验错误列表

    -- 解析使用的规则版本
    parsing_rule_version VARCHAR(50),         -- 规则版本

    -- 解析时间
    parsed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_result_config ON parse_results(config_file_id);
CREATE INDEX IF NOT EXISTS idx_result_device ON parse_results(device_metadata_id);
CREATE INDEX IF NOT EXISTS idx_result_quality ON parse_results(quality_score);
CREATE INDEX IF NOT EXISTS idx_result_status ON parse_results(validation_status);

-- ============================================================================
-- 5. 设备基础信息表
-- ============================================================================
-- 存储提取的设备基本信息
CREATE TABLE IF NOT EXISTS device_info (
    id SERIAL PRIMARY KEY,

    -- 关联解析结果
    parse_result_id INTEGER NOT NULL UNIQUE REFERENCES parse_results(id) ON DELETE CASCADE,

    -- 基础信息
    hostname VARCHAR(255),                     -- 主机名
    management_ip VARCHAR(45),                 -- 管理 IP 地址
    mac_address VARCHAR(45),                   -- MAC 地址
    serial_number VARCHAR(100),                -- 序列号

    -- 字段有效性标记
    hostname_valid BOOLEAN DEFAULT NULL,         -- 主机名是否有效
    management_ip_valid BOOLEAN DEFAULT NULL,   -- IP 地址是否有效
    mac_address_valid BOOLEAN DEFAULT NULL,     -- MAC 地址是否有效
    serial_number_valid BOOLEAN DEFAULT NULL,    -- 序列号是否有效

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_device_info_hostname ON device_info(hostname);
CREATE INDEX IF NOT EXISTS idx_device_info_ip ON device_info(management_ip);

-- ============================================================================
-- 6. 接口配置表
-- ============================================================================
-- 存储提取的接口配置信息
CREATE TABLE IF NOT EXISTS interface_config (
    id SERIAL PRIMARY KEY,

    -- 关联解析结果
    parse_result_id INTEGER NOT NULL REFERENCES parse_results(id) ON DELETE CASCADE,

    -- 接口信息
    interface_name VARCHAR(100) NOT NULL,       -- 接口名称
    interface_type VARCHAR(50),                -- 接口类型 (GigabitEthernet, FastEthernet, etc.)
    ip_address VARCHAR(45),                    -- IP 地址
    subnet_mask VARCHAR(45),                   -- 子网掩码
    description TEXT,                          -- 接口描述
    status VARCHAR(20),                        -- 状态 (up, down, administratively_down)

    -- VLAN 信息（如果适用）
    vlan_id INTEGER,                            -- VLAN ID
    vlan_name VARCHAR(100),                    -- VLAN 名称

    -- 有效性标记
    ip_valid BOOLEAN DEFAULT NULL,              -- IP 是否有效
    mask_valid BOOLEAN DEFAULT NULL,            -- 掩码是否有效

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_interface_result ON interface_config(parse_result_id);
CREATE INDEX IF NOT EXISTS idx_interface_name ON interface_config(interface_name);
CREATE INDEX IF NOT EXISTS idx_interface_ip ON interface_config(ip_address);

-- ============================================================================
-- 7. 解析日志表
-- ============================================================================
-- 记录解析过程的日志
CREATE TABLE IF NOT EXISTS parse_logs (
    id SERIAL PRIMARY KEY,

    -- 关联配置文件
    config_file_id INTEGER REFERENCES config_files(id) ON DELETE CASCADE,

    -- 日志级别和信息
    log_level VARCHAR(20) NOT NULL,             -- 日志级别 (INFO, WARNING, ERROR)
    log_message TEXT NOT NULL,                 -- 日志消息
    log_details TEXT,                          -- 详细信息（JSON 格式）

    -- 性能指标
    parse_duration_ms INTEGER,                  -- 解析耗时（毫秒）

    -- 时间戳
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_log_config ON parse_logs(config_file_id);
CREATE INDEX IF NOT EXISTS idx_log_level ON parse_logs(log_level);
CREATE INDEX IF NOT EXISTS idx_log_created ON parse_logs(created_at);

-- ============================================================================
-- 8. 规则优化历史表
-- ============================================================================
-- 记录规则的优化历史
CREATE TABLE IF NOT EXISTS rule_optimization_history (
    id SERIAL PRIMARY KEY,

    -- 关联解析规则
    parsing_rule_id INTEGER NOT NULL REFERENCES parsing_rules(id) ON DELETE CASCADE,

    -- 优化信息
    old_pattern TEXT,                           -- 旧的正则表达式
    new_pattern TEXT NOT NULL,                 -- 新的正则表达式
    optimization_reason TEXT,                  -- 优化原因
    failed_sample_count INTEGER,                -- 失败样本数量

    -- 优化效果对比
    old_success_rate DECIMAL(5,2),            -- 优化前成功率
    new_success_rate DECIMAL(5,2),            -- 优化后成功率
    improvement DECIMAL(5,2),                  -- 提升幅度

    -- 优化时间
    optimized_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 索引
CREATE INDEX IF NOT EXISTS idx_opt_rule ON rule_optimization_history(parsing_rule_id);
CREATE INDEX IF NOT EXISTS idx_opt_time ON rule_optimization_history(optimized_at);

-- ============================================================================
-- 9. 触发器
-- ============================================================================

-- 自动更新 updated_at 字段
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- 为需要的表添加更新时间触发器
DROP TRIGGER IF EXISTS update_device_metadata_updated_at ON device_metadata;
CREATE TRIGGER update_device_metadata_updated_at BEFORE UPDATE ON device_metadata
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_parsing_rules_updated_at ON parsing_rules;
CREATE TRIGGER update_parsing_rules_updated_at BEFORE UPDATE ON parsing_rules
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- 10. 视图
-- ============================================================================

-- 视图：解析结果摘要
CREATE OR REPLACE VIEW v_parse_summary AS
SELECT
    pr.id AS result_id,
    cf.file_name,
    cf.file_path,
    cf.parse_status,
    dm.vendor,
    dm.device_type,
    dm.model,
    pr.quality_score,
    pr.validation_status,
    pr.parsed_at
FROM parse_results pr
JOIN config_files cf ON pr.config_file_id = cf.id
LEFT JOIN device_metadata dm ON pr.device_metadata_id = dm.id
ORDER BY pr.parsed_at DESC;

-- 视图：规则性能统计
CREATE OR REPLACE VIEW v_rule_performance AS
SELECT
    pr.rule_name,
    pr.rule_category,
    dm.vendor,
    dm.device_type,
    pr.regex_pattern,
    pr.success_rate,
    pr.total_attempts,
    pr.success_count,
    pr.is_active
FROM parsing_rules pr
JOIN device_metadata dm ON pr.device_metadata_id = dm.id
ORDER BY pr.total_attempts DESC, pr.success_rate DESC;

-- 视图：设备统计
CREATE OR REPLACE VIEW v_device_statistics AS
SELECT
    dm.vendor,
    dm.device_type,
    dm.model,
    COUNT(DISTINCT cf.id) AS file_count,
    AVG(pr.quality_score) AS avg_quality_score,
    MAX(pr.parsed_at) AS last_parsed
FROM device_metadata dm
LEFT JOIN config_files cf ON cf.identified_device_id = dm.id
LEFT JOIN parse_results pr ON pr.config_file_id = cf.id
GROUP BY dm.vendor, dm.device_type, dm.model
ORDER BY file_count DESC;

-- ============================================================================
-- 11. 数据清理策略
-- ============================================================================

-- 定期清理超过 90 天的解析日志
CREATE OR REPLACE FUNCTION cleanup_old_logs()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM parse_logs
    WHERE created_at < CURRENT_TIMESTAMP - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- ============================================================================
-- 12. 初始化数据
-- ============================================================================

-- 插入常用厂商的默认设备元数据（可选）
INSERT INTO device_metadata (vendor, device_type, model, config_format) VALUES
    ('Cisco', 'Router', 'ISR 4000', 'Cisco IOS'),
    ('Cisco', 'Switch', 'Catalyst 2960', 'Cisco IOS'),
    ('Cisco', 'Switch', 'Catalyst 9300', 'Cisco IOS'),
    ('Huawei', 'Router', 'NE40E', 'Huawei VRP'),
    ('Huawei', 'Switch', 'S5700', 'Huawei VRP'),
    ('Huawei', 'Switch', 'S12700', 'Huawei VRP'),
    ('H3C', 'Switch', 'S5120', 'H3C Comware'),
    ('H3C', 'Switch', 'S10500', 'H3C Comware'),
    ('Juniper', 'Router', 'MX960', 'Juniper JunOS'),
    ('Juniper', 'Switch', 'EX4300', 'Juniper JunOS'),
    ('Juniper', 'Firewall', 'SRX1500', 'Juniper JunOS'),
    ('Ruijie', 'Switch', 'S2620', 'Ruijie OS'),
    ('Ruijie', 'Switch', 'S5750', 'Ruijie OS')
ON CONFLICT (vendor, device_type, model, software_version) DO NOTHING;

-- ============================================================================
-- 说明
-- ============================================================================
--
-- 表结构设计原则：
-- 1. 规范化：遵循第三范式，消除数据冗余
-- 2. 可扩展性：预留扩展字段，支持未来需求
-- 3. 性能优化：合理创建索引，提高查询效率
-- 4. 数据完整性：使用外键约束，保证数据一致性
-- 5. 审计追踪：记录创建和更新时间，支持追溯
--
-- 使用建议：
-- 1. 定期清理 parse_logs 表中的旧日志数据
-- 2. 监控 parsing_rules 表的成功率，及时优化低效规则
-- 3. 使用视图进行常用查询，简化复杂 SQL
-- 4. 对大表的 content 字段考虑使用 TOAST 存储
-- 5. 定期备份解析结果数据
--
-- 安全建议：
-- 1. 限制数据库用户权限
-- 2. 使用 SSL 连接数据库
-- 3. 定期更新数据库密码
-- 4. 敏感字段考虑加密存储