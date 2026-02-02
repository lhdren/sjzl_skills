#!/usr/bin/env python3
"""
Network Device Config Parser - 网络设备配置文件解析器
支持多厂商网络设备配置文件的自动识别、提取、校验
"""

import re
import json
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime


@dataclass
class DeviceMetadata:
    """设备元数据"""
    vendor: str = ""
    device_type: str = ""
    model: str = ""
    software_version: str = ""
    config_format: str = ""


@dataclass
class DeviceInfo:
    """设备基础信息"""
    hostname: str = ""
    management_ip: str = ""
    mac_address: str = ""
    serial_number: str = ""


@dataclass
class InterfaceInfo:
    """接口信息"""
    name: str = ""
    ip_address: str = ""
    subnet_mask: str = ""
    status: str = ""
    description: str = ""


class NetworkConfigParser:
    """网络设备配置解析器"""

    def __init__(self, rules_dir: Optional[Path] = None):
        self.rules_dir = rules_dir or Path(__file__).parent.parent / 'rules'
        self.metadata = DeviceMetadata()
        self.device_info = DeviceInfo()
        self.interfaces: List[InterfaceInfo] = []
        self.raw_config = ""
        self.parsing_rules = {}

    def load_config(self, config_file: str) -> bool:
        """加载配置文件"""
        try:
            with open(config_file, 'r', encoding='utf-8') as f:
                self.raw_config = f.read()
            return True
        except Exception as e:
            print(f"Error loading config: {e}")
            return False

    def load_config_string(self, config_string: str) -> None:
        """从字符串加载配置"""
        self.raw_config = config_string

    def identify_device(self) -> DeviceMetadata:
        """识别设备特征（步骤1）"""
        # 厂商特征识别
        vendor_patterns = {
            'Cisco': [
                (r'^(hostname|interface\s+\S+|vlan\s+\d+)', 'Cisco IOS'),
                (r'^(version\s+15|version\s+12)', 'Cisco IOS'),
            ],
            'Huawei': [
                (r'^(sysname|interface\s+\S+|vlan\s+\d+)', 'Huawei VRP'),
                (r'^\s*#\s*$', 'Huawei VRP'),
            ],
            'H3C': [
                (r'^(sysname|interface\s+\S+)', 'H3C Comware'),
            ],
            'Juniper': [
                (r'^(set\system\shostname|interfaces\s+\S+)', 'Juniper JunOS'),
            ],
            'Ruijie': [
                (r'^(hostname|interface\s+\S+)', 'Ruijie OS'),
            ]
        }

        config_lower = self.raw_config.lower()

        for vendor, patterns in vendor_patterns.items():
            for pattern, format_name in patterns:
                if re.search(pattern, self.raw_config, re.MULTILINE):
                    self.metadata.vendor = vendor
                    self.metadata.config_format = format_name

                    # 提取版本信息
                    self._extract_version()

                    # 识别设备类型和型号
                    self._identify_device_type()

                    return self.metadata

        # 未识别出厂商，返回默认值
        return self.metadata

    def _extract_version(self) -> None:
        """提取软件版本"""
        version_patterns = {
            'Cisco': r'version\s+([\d.()]+)',
            'Huawei': r'version\s+([\d.]+)',
            'H3C': r'version\s+([\d.]+)',
            'Juniper': r'Junos:\s+([\d.]+)',
        }

        if self.metadata.vendor in version_patterns:
            match = re.search(version_patterns[self.metadata.vendor], self.raw_config)
            if match:
                self.metadata.software_version = match.group(1)

    def _identify_device_type(self) -> None:
        """识别设备类型和型号"""
        # 根据特征关键字识别
        type_keywords = {
            'Router': ['router', 'serial', 'WAN'],
            'Switch': ['switch', 'vlan', 'trunk', r'interface\s+GigabitEthernet'],
            'Firewall': ['firewall', 'security-zone', 'policy'],
            'Load Balancer': ['load-balance', 'slb', 'serverfarm']
        }

        config_lower = self.raw_config.lower()
        for device_type, keywords in type_keywords.items():
            if any(re.search(keyword, config_lower) for keyword in keywords):
                self.metadata.device_type = device_type
                break

        # 型号识别（简化版）
        model_patterns = [
            r'Catalyst\s+(\S+)',
            r'NE\d+E?',
            r'S\d+',
            r'MX\d+',
            r'SRG\d+'
        ]

        for pattern in model_patterns:
            match = re.search(pattern, self.raw_config, re.IGNORECASE)
            if match:
                self.metadata.model = match.group(0)
                break

    def extract_data(self) -> Dict[str, Any]:
        """提取配置数据（步骤2）"""
        # 提取基础信息
        self._extract_device_info()

        # 提取接口配置
        self._extract_interfaces()

        # 返回提取的数据
        return {
            'metadata': asdict(self.metadata),
            'device_info': asdict(self.device_info),
            'interfaces': [asdict(i) for i in self.interfaces]
        }

    def _extract_device_info(self) -> None:
        """提取设备基础信息"""
        # Hostname
        hostname_patterns = {
            'Cisco': r'hostname\s+(\S+)',
            'Huawei': r'sysname\s+(\S+)',
            'H3C': r'sysname\s+(\S+)',
            'Juniper': r'set\system\shostname\s+"?(\S+)"?',
            'Ruijie': r'hostname\s+(\S+)'
        }

        if self.metadata.vendor in hostname_patterns:
            match = re.search(hostname_patterns[self.metadata.vendor], self.raw_config)
            if match:
                self.device_info.hostname = match.group(1)

        # MAC 地址
        mac_pattern = r'([0-9A-Fa-f]{2}:){5}[0-9A-Fa-f]{2}|' \
                     r'([0-9A-Fa-f]{2}\.){5}[0-9A-Fa-f]{2}|' \
                     r'([0-9A-Fa-f]{4}\.){2}[0-9A-Fa-f]{4}'
        match = re.search(mac_pattern, self.raw_config)
        if match:
            self.device_info.mac_address = match.group(0)

        # 序列号
        serial_pattern = r'System\s+[Ss]erial\s+[Nn]umber\s*:\s*(\S+)|' \
                        r'Processor\s+board ID\s+(\S+)'
        match = re.search(serial_pattern, self.raw_config, re.IGNORECASE)
        if match:
            self.device_info.serial_number = match.group(1) if match.group(1) else match.group(2)

        # 管理 IP（通常是第一个配置的 IP）
        ip_pattern = r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)'
        match = re.search(ip_pattern, self.raw_config)
        if match:
            self.device_info.management_ip = match.group(1)

    def _extract_interfaces(self) -> None:
        """提取接口配置"""
        interface_patterns = {
            'Cisco': r'interface\s+(\S+)(.*?)(?=interface|\Z)',
            'Huawei': r'interface\s+(\S+)(.*?)(?=interface|\Z)',
            'H3C': r'interface\s+(\S+)(.*?)(?=interface|\Z)',
        }

        if self.metadata.vendor not in interface_patterns:
            return

        pattern = interface_patterns[self.metadata.vendor]
        matches = re.findall(pattern, self.raw_config, re.DOTALL)

        for match in matches:
            if isinstance(match, tuple):
                interface_name = match[0]
                config_block = match[1] if len(match) > 1 else ''
            else:
                interface_name = match
                config_block = ''

            interface_info = InterfaceInfo(name=interface_name)

            # 提取 IP 地址
            ip_match = re.search(r'ip\s+address\s+(\d+\.\d+\.\d+\.\d+)\s+(\S+)', config_block)
            if ip_match:
                interface_info.ip_address = ip_match.group(1)
                interface_info.subnet_mask = ip_match.group(2)

            # 提取描述
            desc_match = re.search(r'description\s+(\S.*)', config_block)
            if desc_match:
                interface_info.description = desc_match.group(1).strip()

            # 提取状态
            if 'no shutdown' in config_block or 'enable' in config_block:
                interface_info.status = 'up'
            elif 'shutdown' in config_block:
                interface_info.status = 'down'

            self.interfaces.append(interface_info)

    def validate_quality(self, data: Optional[Dict[str, Any]] = None) -> Tuple[bool, float, List[str]]:
        """校验数据质量（步骤3）"""
        if data is None:
            data = {
                'device_info': asdict(self.device_info),
                'interfaces': [asdict(i) for i in self.interfaces]
            }

        warnings = []
        filled_fields = 0
        total_fields = 0

        # 校验必填字段
        required_fields = {
            'device_info': ['hostname', 'management_ip'],
            'interfaces': ['name']
        }

        # 校验设备信息
        device_info = data.get('device_info', {})
        for field in required_fields.get('device_info', []):
            total_fields += 1
            value = device_info.get(field, '')

            if not value or value.strip() == '':
                warnings.append(f"Missing required field: device_info.{field}")
            else:
                # 格式校验
                if field == 'hostname':
                    if not self._validate_hostname(value):
                        warnings.append(f"Invalid hostname format: {value}")
                    else:
                        filled_fields += 1
                elif field == 'management_ip':
                    if not self._validate_ip(value):
                        warnings.append(f"Invalid IP format: {value}")
                    else:
                        filled_fields += 1
                else:
                    filled_fields += 1

        # 校验接口信息
        interfaces = data.get('interfaces', [])
        total_fields += len(interfaces)  # 每个接口至少需要 name
        for idx, interface in enumerate(interfaces):
            if not interface.get('name'):
                warnings.append(f"Interface {idx}: Missing interface name")
            else:
                filled_fields += 1

            # 校验接口 IP（如果存在）
            if interface.get('ip_address'):
                total_fields += 1
                if not self._validate_ip(interface['ip_address']):
                    warnings.append(f"Interface {interface.get('name', idx)}: Invalid IP address")
                else:
                    filled_fields += 1

        # 计算质量分数
        quality_score = filled_fields / total_fields if total_fields > 0 else 0.0
        is_valid = quality_score >= 0.9 and len(warnings) == 0

        return is_valid, quality_score, warnings

    def _validate_hostname(self, hostname: str) -> bool:
        """校验主机名格式"""
        pattern = r'^[a-zA-Z][a-zA-Z0-9\-]{0,62}$'
        return bool(re.match(pattern, hostname))

    def _validate_ip(self, ip: str) -> bool:
        """校验 IP 地址格式"""
        pattern = r'^(\d{1,3}\.){3}\d{1,3}$'
        if not re.match(pattern, ip):
            return False
        # 检查每个段是否在 0-255 范围内
        octets = ip.split('.')
        return all(0 <= int(octet) <= 255 for octet in octets)

    def generate_parsing_rules(self) -> Dict[str, str]:
        """生成解析正则表达式（步骤4）"""
        rules = {}

        # 根据厂商和配置格式生成规则
        if self.metadata.vendor == 'Cisco':
            rules.update({
                'hostname': r'hostname\s+(?P<hostname>\S+)',
                'interface': r'interface\s+(?P<interface>\S+)',
                'ip_address': r'ip\s+address\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(?P<mask>\S+)',
                'vlan': r'vlan\s+(?P<vlan_id>\d+)',
                'description': r'description\s+(?P<description>.*)'
            })
        elif self.metadata.vendor == 'Huawei':
            rules.update({
                'hostname': r'sysname\s+(?P<hostname>\S+)',
                'interface': r'interface\s+(?P<interface>\S+)',
                'ip_address': r'ip\s+address\s+(?P<ip>\d+\.\d+\.\d+\.\d+)\s+(?P<mask>\S+)',
                'vlan': r'vlan\s+(?P<vlan_id>\d+)',
                'description': r'description\s+(?P<description>.*)'
            })

        self.parsing_rules = rules
        return rules

    def save_rules(self, rule_file: Optional[str] = None) -> bool:
        """保存解析规则到库（步骤4）"""
        if not self.parsing_rules:
            self.generate_parsing_rules()

        try:
            # 生成规则文件名
            if rule_file is None:
                vendor_slug = self.metadata.vendor.lower().replace(' ', '_')
                device_slug = self.metadata.device_type.lower().replace(' ', '_')
                rule_file = f"{vendor_slug}_{device_slug}.yaml"

            rule_path = self.rules_dir / 'parsers' / rule_file
            rule_path.parent.mkdir(parents=True, exist_ok=True)

            # 保存规则
            rule_data = {
                'metadata': asdict(self.metadata),
                'patterns': self.parsing_rules,
                'created_at': datetime.now().isoformat(),
                'version': '1.0.0'
            }

            with open(rule_path, 'w', encoding='utf-8') as f:
                yaml.dump(rule_data, f, default_flow_style=False, allow_unicode=True)

            print(f"Rules saved to: {rule_path}")
            return True

        except Exception as e:
            print(f"Error saving rules: {e}")
            return False

    def load_rules(self, rule_file: str) -> bool:
        """加载解析规则（步骤6）"""
        try:
            rule_path = self.rules_dir / 'parsers' / rule_file

            if not rule_path.exists():
                print(f"Rule file not found: {rule_path}")
                return False

            with open(rule_path, 'r', encoding='utf-8') as f:
                rule_data = yaml.safe_load(f)

            self.parsing_rules = rule_data.get('patterns', {})
            self.metadata = DeviceMetadata(**rule_data.get('metadata', {}))

            return True

        except Exception as e:
            print(f"Error loading rules: {e}")
            return False

    def parse_with_rules(self) -> Dict[str, Any]:
        """使用正则表达式解析文件（步骤5）"""
        if not self.parsing_rules:
            self.generate_parsing_rules()

        result = {
            'metadata': asdict(self.metadata),
            'device_info': {},
            'interfaces': [],
            'raw_data': {}
        }

        # 应用规则提取数据
        for field_name, pattern in self.parsing_rules.items():
            matches = re.finditer(pattern, self.raw_config, re.MULTILINE)
            values = []

            for match in matches:
                if match.groupdict():
                    values.append(match.groupdict())
                elif match.groups():
                    values.append(match.groups())
                else:
                    values.append(match.group(0))

            result['raw_data'][field_name] = values

        # 转换为结构化数据
        result['device_info'] = asdict(self.device_info)
        result['interfaces'] = [asdict(i) for i in self.interfaces]

        return result

    def optimize_rules(self, failed_samples: List[str]) -> Dict[str, str]:
        """优化解析规则（步骤6）"""
        optimized_rules = self.parsing_rules.copy()

        # 分析失败样本，识别模式变化
        for sample in failed_samples:
            # 尝试从失败样本中提取新的模式
            for field_name, pattern in optimized_rules.items():
                # 检查现有模式是否匹配
                if not re.search(pattern, sample):
                    # 尝试生成新的模式
                    new_pattern = self._generate_adaptive_pattern(field_name, sample)
                    if new_pattern:
                        optimized_rules[field_name] = new_pattern

        self.parsing_rules = optimized_rules
        return optimized_rules

    def _generate_adaptive_pattern(self, field_name: str, sample: str) -> Optional[str]:
        """生成自适应模式"""
        # 这里可以实现更复杂的模式学习算法
        # 目前返回简化版本

        if field_name == 'hostname':
            # 尝试多种 hostname 格式
            patterns = [
                r'hostname\s+(?P<hostname>\S+)',
                r'sysname\s+(?P<hostname>\S+)',
                r'set-system-hostname\s+"?(?P<hostname>\S+)"?',
                r'host-name\s+(?P<hostname>\S+)'
            ]

            for pattern in patterns:
                if re.search(pattern, sample):
                    return pattern

        return None

    def export_to_json(self, output_file: str) -> bool:
        """导出为 JSON 格式"""
        try:
            data = {
                'metadata': asdict(self.metadata),
                'device_info': asdict(self.device_info),
                'interfaces': [asdict(i) for i in self.interfaces],
                'exported_at': datetime.now().isoformat()
            }

            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            return True

        except Exception as e:
            print(f"Error exporting to JSON: {e}")
            return False

    def export_to_csv(self, output_file: str) -> bool:
        """导出为 CSV 格式"""
        try:
            import csv

            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)

                # 写入表头
                writer.writerow([
                    'hostname', 'management_ip', 'mac_address', 'serial_number',
                    'device_type', 'model', 'vendor'
                ])

                # 写入数据
                writer.writerow([
                    self.device_info.hostname,
                    self.device_info.management_ip,
                    self.device_info.mac_address,
                    self.device_info.serial_number,
                    self.metadata.device_type,
                    self.metadata.model,
                    self.metadata.vendor
                ])

            return True

        except Exception as e:
            print(f"Error exporting to CSV: {e}")
            return False


def main():
    """示例用法"""
    parser = NetworkConfigParser()

    # 示例配置文件
    sample_config = """
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
"""

    # 加载配置
    parser.load_config_string(sample_config)

    # 步骤1: 识别设备
    metadata = parser.identify_device()
    print(f"Device: {metadata.vendor} {metadata.device_type}")

    # 步骤2: 提取数据
    data = parser.extract_data()
    print(f"Hostname: {data['device_info']['hostname']}")

    # 步骤3: 校验质量
    is_valid, score, warnings = parser.validate_quality(data)
    print(f"Quality Score: {score:.2f}")
    if warnings:
        print("Warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    # 步骤4: 生成规则
    rules = parser.generate_parsing_rules()
    print(f"Generated {len(rules)} parsing rules")

    # 步骤5: 保存规则
    parser.save_rules()

    # 步骤6: 使用规则解析
    result = parser.parse_with_rules()
    print(f"Parsed {len(result['interfaces'])} interfaces")


if __name__ == '__main__':
    main()