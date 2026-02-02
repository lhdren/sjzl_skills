---
name: network_device_config_parse
description: >
  网络设备配置文件智能解析系统。
  自动识别厂商、型号、类型，提取和校验配置数据（IP、MAC、Hostname 等），
  生成并优化解析规则，支持多厂商网络设备的自动化配置解析。
  适用于 Cisco、Huawei、H3C、Juniper、Ruijie 等主流网络厂商设备。
metadata:
  author: lhdren
  version: "1.0.0"
  category: network-automation
tags:
  - network
  - config-parser
  - automation
  - regex
  - data-validation
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - Glob
  - Grep
---

# Network Device Config Parser - 网络设备配置文件解析系统

智能网络设备配置文件解析工具，支持自动识别、提取、校验和优化网络配置数据。

## 核心功能

### 1. 配置文件特征识别

自动识别网络设备配置文件的元数据和特征：

| 特征维度 | 说明 | 示例 |
|---------|------|------|
| **厂商** | 设备制造商 | Cisco, Huawei, H3C, Juniper, Ruijie |
| **类型** | 设备类型 | Router, Switch, Firewall, Load Balancer |
| **型号** | 具体型号 | Catalyst 2960, NE40E, S12500 |
| **版本** | 软件版本 | IOS 15.2, VRP 8.180, Comware 7.1 |
| **配置格式** | 格式特征 | Cisco IOS, Huawei VRP, Juniper JunOS |

### 2. 数据提取

从配置文件中提取关键网络数据：

**基础信息**：
- Hostname（主机名）
- Management IP（管理 IP）
- MAC Address（MAC 地址）
- Serial Number（序列号）

**网络配置**：
- Interface 配置（接口信息）
- VLAN 配置（虚拟局域网）
- Routing 配置（路由信息）
- ACL 配置（访问控制列表）
- NAT 配置（网络地址转换）

**安全配置**：
- User accounts（用户账户）
- Password policies（密码策略）
- SSH/AAA 配置

### 3. 数据质量校验

自动校验提取数据的完整性和正确性：

```python
# 必填字段校验
required_fields = {
    'hostname': r'^[a-zA-Z0-9\-]+$',
    'management_ip': r'^(\d{1,3}\.){3}\d{1,3}$',
    'mac_address': r'^([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}$'
}

# 格式校验
validation_rules = {
    'ip_address': validate_ipv4,
    'mac_address': validate_mac,
    'hostname': validate_hostname
}
```

**校验规则**：
- ✅ 必填字段非空
- ✅ 格式符合规范
- ✅ 取值范围合理
- ✅ 关联字段一致

### 4. 解析规则生成

基于样本配置文件自动生成正则表达式：

```python
# 示例：提取 Cisco 接口配置
pattern = r'interface (?P<interface>\S+)\n.*?ip address (?P<ip>\S+) (?P<mask>\S+)'

# 示例：提取 Huawei VLAN
pattern = r'vlan (?P<vlan_id>\d+)\n.*?description (?P<description>.*)'
```

**规则存储结构**：
```
rules/
├── cisco_router.yaml
├── cisco_switch.yaml
├── huawei_router.yaml
├── h3c_switch.yaml
└── juniper_firewall.yaml
```

### 5. 智能解析流程

```
┌─────────────┐
│  输入配置文件  │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  特征识别    │  ← 检查是否为已知设备类型
└──────┬──────┘
       │
       ├─→ 已知类型 → 调用现有规则解析 → 数据校验 → 输出
       │
       └─→ 未知类型 → 特征分析 → 生成规则 → 存储规则 → 解析 → 校验 → 输出
```

### 6. 规则优化机制

当解析数据质量不合规时，自动优化解析规则：

**优化触发条件**：
- 必填字段缺失率 > 10%
- 格式错误率 > 5%
- 用户反馈解析结果错误

**优化策略**：
1. 分析失败样本
2. 识别模式变化
3. 调整正则表达式
4. 验证优化效果
5. 更新规则库

## 使用场景

### 场景 1：首次解析新设备配置

```python
# 输入：未知厂商配置文件
config = """
hostname SW-CORE-01
interface GigabitEthernet0/1
 ip address 192.168.1.1 255.255.255.0
"""

# 处理流程
parser = NetworkConfigParser(config)
parser.identify_device()  # 识别为 Cisco Switch
parser.generate_rules()   # 生成解析规则
parser.extract_data()     # 提取数据
parser.validate()         # 校验质量
parser.save_rules()       # 保存规则
```

### 场景 2：批量解析已知设备

```python
# 使用已有规则批量处理
parser = NetworkConfigParser()
parser.load_rules('cisco_switch.yaml')
results = parser.batch_process(config_files)
```

### 场景 3：规则优化

```python
# 检测到解析质量下降
parser.analyze_quality()
if parser.quality_score < 0.9:
    parser.optimize_rules()
    parser.validate_optimization()
```

## 支持的厂商和设备

| 厂商 | 设备类型 | 配置格式 | 支持状态 |
|------|---------|----------|----------|
| **Cisco** | Router/Switch | Cisco IOS | ✅ 已支持 |
| **Huawei** | Router/Switch | Huawei VRP | ✅ 已支持 |
| **H3C** | Switch | Comware | ✅ 已支持 |
| **Juniper** | Router/Firewall | JunOS | ✅ 已支持 |
| **Ruijie** | Switch | Ruijie OS | ✅ 已支持 |
| **Maipu** | Router | Maipu OS | 🚧 开发中 |
| **F5** | Load Balancer | F5 BIG-IP | 🚧 开发中 |

## 输出格式

### JSON 格式输出

```json
{
  "metadata": {
    "vendor": "Cisco",
    "device_type": "Switch",
    "model": "Catalyst 2960",
    "software_version": "IOS 15.2(2)E7"
  },
  "device_info": {
    "hostname": "SW-CORE-01",
    "management_ip": "192.168.1.1",
    "mac_address": "00:1A:2B:3C:4D:5E",
    "serial_number": "FHK12345678"
  },
  "interfaces": [
    {
      "name": "GigabitEthernet0/1",
      "ip_address": "192.168.1.1",
      "subnet_mask": "255.255.255.0",
      "status": "up"
    }
  ],
  "quality_score": 0.95,
  "validation_warnings": []
}
```

### CSV 格式输出

```csv
hostname,management_ip,mac_address,serial_number,device_type,model
SW-CORE-01,192.168.1.1,00:1A:2B:3C:4D:5E,FHK12345678,Switch,Catalyst 2960
```

## 配置文件示例

### Cisco 示例

```cisco
hostname SW-CORE-01
!
interface GigabitEthernet0/1
 description Uplink to Core
 ip address 192.168.1.1 255.255.255.0
 no shutdown
!
vlan 10
 name SALES
!
```

### Huawei 示例

```huawei
sysname SW-CORE-01
#
interface GigabitEthernet0/0/1
 description Uplink to Core
 ip address 192.168.1.1 255.255.255.0
 undo shutdown
#
vlan 10
 description SALES
#
```

## 规则库结构

```
rules/
├── metadata/
│   ├── vendor_signatures.yaml    # 厂商特征签名
│   └── device_patterns.yaml      # 设备模式识别
├── parsers/
│   ├── cisco_ios.yaml            # Cisco IOS 解析规则
│   ├── huawei_vrp.yaml           # Huawei VRP 解析规则
│   ├── h3c_comware.yaml          # H3C Comware 解析规则
│   └── juniper_junos.yaml        # Juniper JunOS 解析规则
└── validators/
    ├── network_standards.yaml    # 网络标准校验规则
    └── custom_rules.yaml         # 自定义校验规则
```

## 扩展性

### 添加新厂商支持

1. 在 `rules/vendor_signatures.yaml` 添加厂商特征
2. 创建对应的解析规则文件
3. 定义数据校验规则
4. 测试样本文件
5. 保存到规则库

### 自定义校验规则

```yaml
# custom_rules.yaml
validation:
  hostname:
    pattern: '^[a-zA-Z][a-zA-Z0-9\-]*$'
    max_length: 63
    forbidden: ['localhost', 'switch']

  ip_range:
    private_ranges:
      - '10.0.0.0/8'
      - '172.16.0.0/12'
      - '192.168.0.0/16'
```

## 参考资源

| 文件 | 说明 |
|------|------|
| [scripts/parser.py](scripts/parser.py) | 核心解析引擎 |
| [scripts/rule_generator.py](scripts/rule_generator.py) | 规则生成器 |
| [scripts/validator.py](scripts/validator.py) | 数据校验器 |
| [rules/](rules/) | 解析规则库 |
| [templates/config_template.html](templates/config_template.html) | 配置文件模板 |