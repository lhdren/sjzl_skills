#!/usr/bin/env python3
"""
LLM-based Config Parser - 基于大语言模型的配置解析器
使用智谱AI GLM模型进行智能配置解析和元数据提取
"""

import os
import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from pathlib import Path
import requests
from datetime import datetime


@dataclass
class LLMConfig:
    """LLM配置"""
    api_key: str
    base_url: str = "https://open.bigmodel.cn/api/paas/v4/"
    model: str = "glm-4-plus"  # 使用最强大的模型
    temperature: float = 0.1  # 降低随机性，提高准确性
    max_tokens: int = 8000

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            api_key=os.getenv('ZHIPUAI_API_KEY', ''),
            model=os.getenv('ZHIPUAI_MODEL', 'glm-4-plus')
        )


class LLMConfigParser:
    """基于LLM的配置解析器"""

    def __init__(self, config: Optional[LLMConfig] = None):
        """
        初始化LLM解析器

        Args:
            config: LLM配置，如果为None则从环境变量加载
        """
        self.config = config or LLMConfig.from_env()
        self.api_url = f"{self.config.base_url}chat/completions"

    def call_llm(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """
        调用智谱AI API

        Args:
            prompt: 用户提示词
            system_prompt: 系统提示词（可选）

        Returns:
            模型响应文本
        """
        if not self.config.api_key:
            raise ValueError("ZHIPUAI_API_KEY environment variable not set")

        headers = {
            "Authorization": f"Bearer {self.config.api_key}",
            "Content-Type": "application/json"
        }

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.config.model,
            "messages": messages,
            "temperature": self.config.temperature,
            "max_tokens": self.config.max_tokens
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=60)
            response.raise_for_status()

            result = response.json()
            return result["choices"][0]["message"]["content"]

        except requests.exceptions.RequestException as e:
            raise Exception(f"LLM API调用失败: {e}")

    def extract_json_from_response(self, response: str) -> Dict[str, Any]:
        """
        从LLM响应中提取JSON数据

        Args:
            response: LLM响应文本

        Returns:
            解析出的JSON数据
        """
        # 尝试直接解析
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass

        # 尝试提取JSON代码块
        json_match = re.search(r'```json\s*(.*?)\s*```', response, re.DOTALL)
        if json_match:
            try:
                return json.loads(json_match.group(1))
            except json.JSONDecodeError:
                pass

        # 尝试提取花括号内容
        brace_match = re.search(r'\{.*\}', response, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass

        raise ValueError(f"无法从响应中提取有效的JSON: {response[:200]}...")

    def parse_config(self, config_text: str, prompt_template: str,
                     output_schema: Dict[str, Any]) -> Dict[str, Any]:
        """
        使用LLM解析配置文件

        Args:
            config_text: 配置文件内容
            prompt_template: 提示词模板
            output_schema: 输出schema（用于验证）

        Returns:
            解析结果（结构化数据）
        """
        # 构建完整提示词
        prompt = prompt_template.replace("{{CONFIG}}", config_text)

        # 添加JSON输出要求
        prompt += "\n\n请以JSON格式返回结果，严格按照提供的schema结构。"

        # 调用LLM
        system_prompt = """你是一个专业的网络设备配置分析专家。
你精通各大厂商（Cisco、Huawei、H3C、Juniper等）的设备配置语法。
你的任务是分析网络设备配置文件，提取结构化的配置信息。
请准确、完整地提取信息，如果某个配置项不存在，请返回null或空数组。"""

        response = self.call_llm(prompt, system_prompt)

        # 提取JSON结果
        result = self.extract_json_from_response(response)

        return result

    def identify_device(self, config_text: str) -> Dict[str, Any]:
        """
        识别设备元数据

        Args:
            config_text: 配置文件内容

        Returns:
            设备元数据
        """
        prompt = """分析以下网络设备配置文件，识别设备的基本信息。

配置文件：
```
{{CONFIG}}
```

请提取以下信息并以JSON格式返回：
{
  "vendor": "厂商名称（Cisco/Huawei/H3C/Juniper/Ruijie等）",
  "device_type": "设备类型（Router/Switch/Firewall/Load_Balancer等）",
  "model": "设备型号（如果能识别）",
  "software_version": "软件版本",
  "config_format": "配置格式（Cisco_IOS/Huawei_VRP/H3C_Comware等）",
  "confidence": "识别置信度（high/medium/low）",
  "evidence": ["识别依据1", "识别依据2"]
}

注意：
1. 根据命令语法特征识别厂商（如Cisco用"interface"，华为用"sysname"）
2. 根据配置内容判断设备类型（有路由协议则为Router，有VLAN则为Switch）
3. 提供准确的识别依据
"""

        return self.parse_config(config_text, prompt, {})

    def extract_full_config(self, config_text: str, vendor: str,
                           device_type: str) -> Dict[str, Any]:
        """
        提取完整配置信息

        Args:
            config_text: 配置文件内容
            vendor: 厂商
            device_type: 设备类型

        Returns:
            完整的配置信息
        """
        prompt = f"""深度分析以下{vendor} {device_type}的配置文件，提取所有关键配置信息。

配置文件：
```
{{CONFIG}}
```

请提取以下信息并以JSON格式返回：

{{
  "device_info": {{
    "hostname": "设备主机名",
    "management_ip": "管理IP地址",
    "domain_name": "域名",
    "mac_address": "MAC地址（如果能找到）",
    "serial_number": "序列号（如果能找到）",
    "location": "设备位置描述",
    "contact_info": "联系信息"
  }},

  "interfaces": [
    {{
      "name": "接口名称",
      "type": "接口类型（GigabitEthernet/FastEthernet/TenGigE/Loopback/VLAN等）",
      "ip_address": "IP地址",
      "subnet_mask": "子网掩码",
      "description": "接口描述",
      "status": "状态（up/down/administratively_down）",
      "duplex": "双工模式",
      "speed": "速率",
      "vlan_id": "VLAN ID（如果配置）",
      "ip_helper": "DHCP中继地址列表",
      "is_trunk": "是否为Trunk口",
      "allowed_vlans": "允许的VLAN列表",
      "is_shutdown": "是否关闭"
    }}
  ],

  "routing": {{
    "static_routes": [
      {{
        "destination": "目标网络",
        "mask": "子网掩码",
        "next_hop": "下一跳",
        "metric": "管理距离"
      }}
    ],
    "ospf": [
      {{
        "process_id": "进程ID",
        "router_id": "Router ID",
        "areas": [
          {{
            "area_id": "区域ID",
            "networks": ["网络1", "网络2"]
          }}
        ]
      }}
    ],
    "bgp": [
      {{
        "as_number": "本地AS号",
        "router_id": "Router ID",
        "neighbors": [
          {{
            "ip": "邻居IP",
            "remote_as": "远端AS号",
            "description": "邻居描述"
          }}
        ],
        "networks": ["宣告的网络列表"],
        "redistribute": ["重分发的协议"]
      }}
    ]
  }},

  "vlans": [
    {{
      "id": "VLAN ID",
      "name": "VLAN名称",
      "description": "描述",
      "interfaces": ["关联的接口列表"]
    }}
  ],

  "security": {{
    "aaa": {{
      "authentication": "认证配置",
      "authorization": "授权配置",
      "accounting": "计费配置"
    }},
    "acl_rules": [
      {{
        "name": "ACL名称",
        "type": "类型（standard/extended）",
        "rules": ["规则列表"]
      }}
    ],
    "firewall_rules": [
      {{
        "from": "源区域",
        "to": "目标区域",
        "policy": "策略"
      }}
    ]
  }},

  "services": {{
    "ntp": {{
      "servers": ["NTP服务器列表"],
      "source_interface": "源接口"
    }},
    "snmp": {{
      "community": ["SNMP团体字"],
      "trap_hosts": ["Trap主机列表"]
    }},
    "syslog": {{
      "servers": ["Syslog服务器列表"],
      "facility": "设施类型"
    }},
    "dhcp": {{
      "enabled": "是否启用DHCP服务",
      "pools": [
        {{
          "name": "地址池名称",
          "network": "网络地址",
          "mask": "子网掩码",
          "default_router": "默认网关",
          "dns_servers": ["DNS服务器列表"]
        }}
      ]
    }}
  }},

  "high_availability": {{
    "hsrp": {{
      "groups": [
        {{
          "group_id": "组号",
          "virtual_ip": "虚拟IP",
          "priority": "优先级",
          "authentication": "认证方式"
        }}
      ]
    }},
    "vrrp": {{
      "groups": [
        {{
          "group_id": "组号",
          "virtual_ip": "虚拟IP",
          "priority": "优先级"
        }}
      ]
    }}
  }},

  "qos": {{
    "policies": [
      {{
        "name": "策略名称",
        "type": "类型",
        "rules": ["规则列表"]
      }}
    ]
  }},

  "other_config": {{
    "banner": "标语信息",
    "boot_config": "启动配置",
    "line_consoles": ["Console配置"],
    "line_vtys": ["VTY配置"]
  }}
}}

注意事项：
1. 仔细提取所有配置项，不要遗漏
2. 如果某个配置项不存在，返回null或空数组
3. 保持配置的层次结构
4. 确保提取的信息准确完整
5. 特别注意路由协议、VLAN、安全配置等关键信息
"""

        return self.parse_config(config_text, prompt, {})

    def validate_extracted_data(self, data: Dict[str, Any]) -> tuple[bool, float, List[str]]:
        """
        验证提取的数据质量

        Args:
            data: 提取的数据

        Returns:
            (是否有效, 质量分数, 警告列表)
        """
        warnings = []
        scores = []

        # 检查设备基础信息
        device_info = data.get('device_info', {})
        if device_info.get('hostname'):
            scores.append(0.2)
        else:
            warnings.append("Missing hostname")

        if device_info.get('management_ip'):
            scores.append(0.1)
        else:
            warnings.append("Missing management IP")

        # 检查接口配置
        interfaces = data.get('interfaces', [])
        if interfaces:
            scores.append(0.2)
            for iface in interfaces:
                if iface.get('name') and iface.get('ip_address'):
                    scores.append(0.05)
        else:
            warnings.append("No interfaces found")

        # 检查路由配置
        routing = data.get('routing', {})
        if any(routing.values()):
            scores.append(0.15)
        else:
            warnings.append("No routing configuration found")

        # 检查VLAN配置（如果是交换机）
        vlans = data.get('vlans', [])
        if vlans:
            scores.append(0.1)

        # 检查安全配置
        security = data.get('security', {})
        if any(security.values()):
            scores.append(0.1)

        # 检查服务配置
        services = data.get('services', {})
        if any(services.values()):
            scores.append(0.1)

        quality_score = sum(scores) if scores else 0.0
        is_valid = quality_score >= 0.6

        return is_valid, quality_score, warnings


def main():
    """测试LLM解析器"""
    print("LLM Config Parser - 测试模式")

    # 检查API Key
    api_key = os.getenv('ZHIPUAI_API_KEY')
    if not api_key:
        print("错误: 未设置 ZHIPUAI_API_KEY 环境变量")
        print("请设置: export ZHIPUAI_API_KEY='your-api-key'")
        return

    # 创建解析器
    parser = LLMConfigParser()

    # 读取测试配置
    test_config = Path(__file__).parent.parent / 'test_configs' / 'cisco_router.txt'
    if not test_config.exists():
        print(f"测试配置文件不存在: {test_config}")
        return

    with open(test_config, 'r', encoding='utf-8') as f:
        config_text = f.read()

    # 识别设备
    print("\n=== 识别设备 ===")
    metadata = parser.identify_device(config_text)
    print(json.dumps(metadata, indent=2, ensure_ascii=False))

    # 提取完整配置
    print("\n=== 提取完整配置 ===")
    full_config = parser.extract_full_config(
        config_text,
        metadata.get('vendor', 'Unknown'),
        metadata.get('device_type', 'Unknown')
    )
    print(json.dumps(full_config, indent=2, ensure_ascii=False))

    # 验证质量
    print("\n=== 验证数据质量 ===")
    is_valid, quality_score, warnings = parser.validate_extracted_data(full_config)
    print(f"是否有效: {is_valid}")
    print(f"质量分数: {quality_score:.2%}")
    if warnings:
        print("警告:")
        for warning in warnings:
            print(f"  - {warning}")


if __name__ == '__main__':
    main()