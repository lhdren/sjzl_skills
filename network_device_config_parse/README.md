# Network Device Config Parser 使用指南

## 快速开始

### 1. 基本使用

```python
from network_device_config_parse.scripts.parser import NetworkConfigParser

# 创建解析器实例
parser = NetworkConfigParser()

# 加载配置文件
parser.load_config('path/to/config.txt')

# 步骤1: 识别设备
metadata = parser.identify_device()
print(f"厂商: {metadata.vendor}")
print(f"设备类型: {metadata.device_type}")
print(f"配置格式: {metadata.config_format}")

# 步骤2: 提取数据
data = parser.extract_data()

# 步骤3: 校验质量
is_valid, quality_score, warnings = parser.validate_quality(data)
print(f"质量分数: {quality_score:.2%}")
if warnings:
    for warning in warnings:
        print(f"警告: {warning}")

# 步骤4: 生成解析规则
rules = parser.generate_parsing_rules()

# 步骤5: 保存规则到库
parser.save_rules()

# 导出结果
parser.export_to_json('output.json')
parser.export_to_csv('output.csv')
```

### 2. 处理已知设备类型

```python
# 对于已知设备，直接加载规则
parser = NetworkConfigParser()

# 加载现有规则
if parser.load_rules('cisco_router.yaml'):
    # 使用规则解析
    result = parser.parse_with_rules()

    # 校验质量
    is_valid, quality_score, warnings = parser.validate_quality(result)

    if quality_score >= 0.9:
        print("解析成功，质量良好")
        parser.export_to_json('result.json')
    else:
        print(f"质量不达标({quality_score:.2%})，需要优化规则")
        # 优化规则...
```

### 3. 处理未知设备

```python
parser = NetworkConfigParser()
parser.load_config('unknown_device.txt')

# 识别设备特征
metadata = parser.identify_device()

# 提取数据
data = parser.extract_data()

# 校验质量
is_valid, quality_score, warnings = parser.validate_quality(data)

# 生成并保存新规则
if quality_score >= 0.8:
    parser.generate_parsing_rules()
    parser.save_rules()  # 自动生成文件名
    print(f"新设备规则已保存: {metadata.vendor}_{metadata.device_type}.yaml")
else:
    print("配置文件质量不佳，无法自动生成规则，需要人工分析")
```

### 4. 批量处理

```python
from pathlib import Path

parser = NetworkConfigParser()
config_files = Path('configs').glob('*.txt')

results = []
for config_file in config_files:
    parser.load_config(str(config_file))
    metadata = parser.identify_device()

    # 尝试加载规则
    rule_file = f"{metadata.vendor.lower()}_{metadata.device_type.lower()}.yaml"

    if parser.load_rules(rule_file):
        # 使用现有规则解析
        result = parser.parse_with_rules()
    else:
        # 生成新规则
        parser.generate_parsing_rules()
        parser.save_rules(rule_file)
        result = parser.extract_data()

    is_valid, quality_score, warnings = parser.validate_quality(result)

    results.append({
        'file': config_file.name,
        'vendor': metadata.vendor,
        'device_type': metadata.device_type,
        'quality_score': quality_score,
        'is_valid': is_valid
    })

# 输出统计
print(f"处理完成: {len(results)} 个文件")
print(f"平均质量分数: {sum(r['quality_score'] for r in results)/len(results):.2%}")
```

### 5. 规则优化

```python
parser = NetworkConfigParser()

# 当发现解析质量不达标时
failed_samples = [
    'sample1.txt',
    'sample2.txt',
    'sample3.txt'
]

# 加载失败样本并优化规则
for sample in failed_samples:
    parser.load_config(sample)
    parser.identify_device()

# 基于失败样本优化规则
optimized_rules = parser.optimize_rules(failed_samples)

# 保存优化后的规则
parser.parsing_rules = optimized_rules
parser.save_rules()

# 验证优化效果
parser.load_config('test.txt')
result = parser.parse_with_rules()
is_valid, quality_score, warnings = parser.validate_quality(result)
print(f"优化后质量分数: {quality_score:.2%}")
```

## 输出格式说明

### JSON 输出

```json
{
  "metadata": {
    "vendor": "Cisco",
    "device_type": "Switch",
    "model": "Catalyst 2960",
    "software_version": "15.2(2)E7",
    "config_format": "Cisco IOS"
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
      "status": "up",
      "description": "Uplink to Core"
    }
  ],
  "exported_at": "2025-01-30T12:00:00"
}
```

### CSV 输出

```csv
hostname,management_ip,mac_address,serial_number,device_type,model,vendor
SW-CORE-01,192.168.1.1,00:1A:2B:3C:4D:5E,FHK12345678,Switch,Catalyst 2960,Cisco
```

## 规则库结构

```
rules/
├── metadata/
│   └── vendor_signatures.yaml    # 厂商特征签名
├── parsers/
│   ├── cisco_router.yaml         # Cisco 路由器解析规则
│   ├── cisco_switch.yaml         # Cisco 交换机解析规则
│   ├── huawei_router.yaml        # Huawei 路由器解析规则
│   └── ...
└── validators/
    ├── network_standards.yaml    # 网络标准校验规则
    └── custom_rules.yaml         # 自定义校验规则
```

## 添加新厂商支持

### 1. 添加厂商特征签名

编辑 `rules/metadata/vendor_signatures.yaml`:

```yaml
vendors:
  NewVendor:
    priority: 7
    signatures:
      - pattern: '特征正则表达式'
        format: '配置格式名称'
        confidence: high
    device_types:
      Router:
        keywords: ['keyword1', 'keyword2']
    common_models:
      - 'Model-Name'
```

### 2. 创建解析规则

在 `rules/parsers/` 目录创建新文件:

```yaml
metadata:
  vendor: NewVendor
  device_type: Router
  model: Model-Name
  software_version: 1.0
  config_format: NewVendor OS

patterns:
  hostname: 'hostname\\s+(?P<hostname>\\S+)'
  interface: 'interface\\s+(?P<interface>\\S+)'
  ip_address: 'ip\\s+address\\s+(?P<ip>\\d+\\.\\d+\\.\\d+\\.\\d+)\\s+(?P<mask>\\S+)'

created_at: '2025-01-30T12:00:00'
version: '1.0.0'
```

### 3. 添加校验规则（可选）

编辑 `rules/validators/network_standards.yaml` 添加特定厂商的校验规则。

## 常见问题

### Q: 如何处理配置文件中的注释？

A: 解析器会自动过滤以 `!` 或 `#` 开头的注释行。

### Q: 如何处理加密的配置？

A: 目前不支持加密配置的解析。需要先解密配置文件。

### Q: 质量分数低于多少需要优化规则？

A: 建议质量分数低于 0.9（90%）时进行规则优化。

### Q: 如何批量测试解析规则？

A: 使用测试脚本遍历样本文件，统计解析成功率和质量分数。

### Q: 支持哪些配置格式？

A: 目前支持纯文本格式的配置文件，不支持专有二进制格式。

## 性能优化建议

1. **批量处理**: 使用多线程/多进程并行处理多个文件
2. **缓存规则**: 将常用规则加载到内存中避免重复读取
3. **增量解析**: 只解析配置变更部分而非整个文件
4. **异步校验**: 数据校验可以异步进行

## 扩展开发

### 自定义数据提取器

```python
from network_device_config_parse.scripts.parser import NetworkConfigParser

class CustomParser(NetworkConfigParser):
    def extract_custom_field(self, field_name):
        """提取自定义字段"""
        pattern = self.parsing_rules.get(field_name)
        if pattern:
            matches = re.findall(pattern, self.raw_config)
            return matches
        return []
```

### 自定义校验器

```python
def custom_validator(data):
    """自定义校验逻辑"""
    # 实现你的校验规则
    warnings = []

    # 示例：检查是否配置了 NTP
    if 'ntp' not in str(data).lower():
        warnings.append("NTP 未配置")

    return len(warnings) == 0, warnings
```

## 贡献指南

如果你添加了新厂商支持或发现了 Bug，欢迎提交 Pull Request。

## 许可证

MIT License