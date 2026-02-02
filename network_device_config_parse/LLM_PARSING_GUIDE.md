# LLM 增强解析功能使用指南

## 概述

本系统集成了智谱AI GLM-4-Plus模型，提供基于大语言模型的智能配置解析功能，能够深度理解网络设备配置文件并提取丰富的元数据。

## 优势对比

### 传统正则表达式解析
- ✅ 速度快
- ✅ 成本低
- ❌ 需要为每种配置编写规则
- ❌ 厂商语法差异需要适配
- ❌ 提取信息有限
- ❌ 格式变化会导致解析失败

### LLM智能解析
- ✅ 深度语义理解
- ✅ 自动适应不同厂商语法
- ✅ 提取信息丰富完整
- ✅ 提供配置质量评估
- ✅ 不依赖固定格式
- ⚠️ 需要API调用
- ⚠️ 有一定成本

## 安装依赖

```bash
pip install -r requirements.txt
```

新增依赖：
- `requests>=2.28.0` - 用于调用智谱AI API

## 配置API Key

### 方法1: 环境变量（推荐）

```bash
export ZHIPUAI_API_KEY='your-api-key-here'
```

### 方法2: .env 文件

在项目根目录创建 `.env` 文件：

```
ZHIPUAI_API_KEY=your-api-key-here
```

**注意**：.env 文件已在 .gitignore 中，不会被提交到版本库。

## 获取智谱AI API Key

1. 访问 [智谱AI开放平台](https://open.bigmodel.cn/)
2. 注册/登录账号
3. 在控制台获取 API Key
4. 充值（新用户通常有免费额度）

## 使用方法

### 快速测试

```bash
cd scripts
python llm_parser.py
```

这将测试LLM解析器，解析 `test_configs/cisco_router.txt` 并显示结果。

### 完整验证

```bash
cd scripts
python verify_llm_parsing.py
```

这将：
1. 解析所有3个测试配置文件
2. 提取完整的配置信息
3. 验证数据质量
4. 生成详细的JSON报告
5. 保存到 `output/` 目录

## 提取的信息

LLM解析器能够提取以下丰富信息：

### 1. 设备基础信息
- 主机名 (hostname)
- 管理IP (management_ip)
- 域名 (domain_name)
- MAC地址 (mac_address)
- 序列号 (serial_number)
- 位置描述 (location)
- 联系信息 (contact_info)

### 2. 接口配置
- 接口名称、类型
- IP地址、子网掩码
- 接口描述
- 状态（up/down）
- 双工模式、速率
- VLAN配置
- Trunk配置

### 3. 路由配置
- 静态路由
- OSPF配置（进程ID、Router ID、Areas）
- BGP配置（AS号、邻居、网络宣告）

### 4. VLAN配置
- VLAN ID、名称
- 关联接口列表

### 5. 安全配置
- AAA配置
- ACL规则
- 防火墙规则

### 6. 服务配置
- NTP服务器
- SNMP配置
- Syslog服务器
- DHCP服务

### 7. 高可用性配置
- HSRP配置
- VRRP配置

### 8. QoS配置
- 策略列表
- 规则详情

## 输出格式

解析结果以JSON格式输出，包含：

```json
{
  "device_info": {
    "hostname": "RT-CORE-01",
    "management_ip": "10.0.0.1",
    ...
  },
  "interfaces": [
    {
      "name": "GigabitEthernet0/0/0",
      "ip_address": "202.96.128.1",
      "subnet_mask": "255.255.255.252",
      "description": "WAN-Link-to-ISP",
      "status": "up",
      ...
    }
  ],
  "routing": {
    "ospf": [...],
    "bgp": [...],
    "static_routes": [...]
  },
  "vlans": [...],
  "security": {...},
  "services": {...},
  ...
}
```

## 质量评估

系统会自动评估解析质量：

- **质量分数** (0-100%)
- **有效性** (valid/invalid)
- **警告信息** (缺失的关键配置)

评估标准：
- 设备基础信息 (30%)
- 接口配置 (25%)
- 路由配置 (15%)
- VLAN配置 (10%)
- 安全配置 (10%)
- 服务配置 (10%)

## 性能考虑

- 单个配置文件解析时间：10-20秒
- 主要耗时在API调用和模型推理
- 建议批量处理时控制并发数

## 成本估算

以智谱AI GLM-4-Plus为例：
- 输入: 配置文件大小（约1-5KB）
- 输出: 解析结果JSON（约5-15KB）
- 单次成本: 约0.01-0.03元

**建议**：
- 小规模测试：使用LLM解析
- 大规模生产：正则表达式+LLM验证
- 定期更新：使用LLM优化正则规则

## 使用示例

### Python脚本调用

```python
from scripts.llm_parser import LLMConfigParser, LLMConfig
import os

# 创建解析器
config = LLMConfig(api_key=os.getenv('ZHIPUAI_API_KEY'))
parser = LLMConfigParser(config=config)

# 读取配置文件
with open('config.txt', 'r') as f:
    config_text = f.read()

# 识别设备
metadata = parser.identify_device(config_text)
print(f"厂商: {metadata['vendor']}")
print(f"类型: {metadata['device_type']}")

# 提取完整配置
full_config = parser.extract_full_config(
    config_text,
    metadata['vendor'],
    metadata['device_type']
)

# 验证质量
is_valid, quality_score, warnings = parser.validate_extracted_data(full_config)
print(f"质量分数: {quality_score:.2%}")
```

### 与数据库集成

```python
from scripts.llm_parser import LLMConfigParser
from scripts.db_manager import DatabaseManager

# 创建解析器和数据库管理器
parser = LLMConfigParser()
db_manager = DatabaseManager()

# 解析配置
metadata = parser.identify_device(config_text)
full_config = parser.extract_full_config(config_text, ...)

# 保存到数据库（扩展功能）
# 需要更新db_manager以支持更丰富的数据结构
```

## 故障排查

### 问题1: API Key错误

```
错误: [WARN] 未设置 ZHIPUAI_API_KEY 环境变量
```

**解决**：设置环境变量或创建.env文件

### 问题2: 网络连接失败

```
错误: LLM API调用失败: ConnectionError
```

**解决**：
1. 检查网络连接
2. 确认可以访问 open.bigmodel.cn
3. 检查代理设置

### 问题3: JSON解析失败

```
错误: 无法从响应中提取有效的JSON
```

**解决**：
1. 检查配置文件格式是否正确
2. 查看完整错误信息
3. 可能需要调整prompt

## 下一步开发

- [ ] 集成到数据库管理器
- [ ] 创建混合解析模式（正则+LLM）
- [ ] 添加规则自动生成功能
- [ ] 支持流式输出提高响应速度
- [ ] 添加配置对比功能

## 相关文件

- `scripts/llm_parser.py` - LLM解析器核心模块
- `scripts/verify_llm_parsing.py` - LLM验证脚本
- `test_configs/` - 测试配置文件
- `output/` - 解析结果输出目录