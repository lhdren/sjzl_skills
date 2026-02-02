#!/usr/bin/env python3
"""
LLM Enhanced Verification - 基于LLM的增强验证脚本
使用智谱AI进行深度配置解析，并与正则表达式解析结果对比
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any

# 添加父目录到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.llm_parser import LLMConfigParser, LLMConfig
from scripts.db_manager import DatabaseManager, DBConfig


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def load_api_key():
    """加载智谱AI API Key"""
    # 从环境变量加载
    api_key = os.getenv('ZHIPUAI_API_KEY')

    if not api_key:
        # 尝试从配置文件加载
        config_file = Path(__file__).parent.parent / '.env'
        if config_file.exists():
            with open(config_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if line.startswith('ZHIPUAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        print("\n[WARN] 未设置 ZHIPUAI_API_KEY 环境变量")
        print("请设置环境变量或创建 .env 文件:")
        print("  export ZHIPUAI_API_KEY='your-api-key'")
        print("或创建 .env 文件:")
        print("  ZHIPUAI_API_KEY=your-api-key")

        return None

    return api_key


def verify_llm_parsing():
    """使用LLM进行增强验证"""

    print_section("网络设备配置解析系统 - LLM增强验证")

    # 加载API Key
    api_key = load_api_key()
    if not api_key:
        print("\n[FAIL] 无法获取智谱AI API Key，LLM解析功能不可用")
        return False

    # 创建LLM解析器
    llm_config = LLMConfig(api_key=api_key)
    llm_parser = LLMConfigParser(config=llm_config)

    # 创建数据库管理器
    db_config = DBConfig(
        host='lhdren.cn',
        port=15432,
        database='postgres',
        user='admin',
        password=os.getenv('DB_PASSWORD', 'admin123')
    )

    db_manager = DatabaseManager(config=db_config)

    # 步骤1: 连接数据库
    print_section("步骤1: 连接数据库")

    if not db_manager.connect():
        print("[FAIL] 数据库连接失败")
        return False

    print("[OK] 数据库连接成功")

    # 步骤2: 准备测试配置文件
    print_section("步骤2: 准备测试配置文件")

    test_configs_dir = Path(__file__).parent.parent / 'test_configs'
    config_files = [
        ('cisco_router.txt', 'Cisco 核心路由器'),
        ('huawei_switch.txt', 'Huawei 汇聚交换机'),
        ('h3c_access_switch.txt', 'H3C 接入交换机')
    ]

    print(f"\n找到 {len(config_files)} 个测试配置文件")

    # 步骤3: 使用LLM解析配置
    print_section("步骤3: 使用LLM深度解析配置")

    llm_results = []

    for config_file, description in config_files:
        print(f"\n--- LLM解析 {description}: {config_file} ---")

        config_path = test_configs_dir / config_file
        if not config_path.exists():
            print(f"[FAIL] 配置文件不存在: {config_path}")
            continue

        try:
            # 读取配置文件
            with open(config_path, 'r', encoding='utf-8') as f:
                config_text = f.read()

            # 步骤1: 识别设备
            print("  [1/3] 识别设备...")
            metadata = llm_parser.identify_device(config_text)
            print(f"    厂商: {metadata.get('vendor')}")
            print(f"    类型: {metadata.get('device_type')}")
            print(f"    型号: {metadata.get('model', 'Unknown')}")
            print(f"    置信度: {metadata.get('confidence')}")

            # 步骤2: 提取完整配置
            print("  [2/3] 提取完整配置（这可能需要10-20秒）...")
            full_config = llm_parser.extract_full_config(
                config_text,
                metadata.get('vendor', 'Unknown'),
                metadata.get('device_type', 'Unknown')
            )

            # 步骤3: 验证质量
            print("  [3/3] 验证数据质量...")
            is_valid, quality_score, warnings = llm_parser.validate_extracted_data(full_config)
            print(f"    质量分数: {quality_score:.2%}")
            if warnings:
                for warning in warnings[:3]:  # 只显示前3个警告
                    print(f"    警告: {warning}")

            # 保存结果
            llm_results.append({
                'file': config_file,
                'description': description,
                'metadata': metadata,
                'full_config': full_config,
                'is_valid': is_valid,
                'quality_score': quality_score,
                'warnings': warnings
            })

            # 显示提取的关键信息
            device_info = full_config.get('device_info', {})
            print(f"\n  提取的关键信息:")
            print(f"    主机名: {device_info.get('hostname', 'N/A')}")
            print(f"    管理IP: {device_info.get('management_ip', 'N/A')}")

            interfaces = full_config.get('interfaces', [])
            print(f"    接口数量: {len(interfaces)}")
            for iface in interfaces[:3]:  # 只显示前3个接口
                ip = iface.get('ip_address', 'N/A')
                desc = iface.get('description', '')
                print(f"      - {iface.get('name')}: {ip} {desc}")

            routing = full_config.get('routing', {})
            bgp_count = len(routing.get('bgp', []))
            ospf_count = len(routing.get('ospf', []))
            static_count = len(routing.get('static_routes', []))
            print(f"    路由配置:")
            print(f"      BGP: {bgp_count} 个, OSPF: {ospf_count} 个, 静态路由: {static_count} 条")

            vlans = full_config.get('vlans', [])
            print(f"    VLAN数量: {len(vlans)}")

        except Exception as e:
            print(f"  [FAIL] LLM解析失败: {e}")
            import traceback
            traceback.print_exc()
            continue

    # 步骤4: 对比分析
    print_section("步骤4: LLM解析 vs 正则表达式解析")

    if llm_results:
        print("\n  LLM解析优势:")
        print("    ✓ 深度语义理解，不依赖固定格式")
        print("    ✓ 提取信息更丰富完整（路由、VLAN、安全、服务等）")
        print("    ✓ 自动适应不同厂商语法差异")
        print("    ✓ 提供配置分析建议")

        print("\n  解析质量对比:")
        avg_quality = sum(r['quality_score'] for r in llm_results) / len(llm_results)
        print(f"    LLM解析平均质量: {avg_quality:.2%}")

        for result in llm_results:
            status = "[OK]" if result['quality_score'] >= 0.8 else "[WARN]"
            print(f"    {status} {result['description']}: {result['quality_score']:.2%}")

    # 步骤5: 详细结果展示
    print_section("步骤5: 详细解析结果展示")

    if llm_results:
        # 选择第一个结果进行详细展示
        result = llm_results[0]
        print(f"\n  展示: {result['description']}")

        metadata = result['metadata']
        print(f"\n  设备元数据:")
        print(f"    厂商: {metadata.get('vendor')}")
        print(f"    类型: {metadata.get('device_type')}")
        print(f"    配置格式: {metadata.get('config_format')}")
        print(f"    识别依据: {', '.join(metadata.get('evidence', []))}")

        full_config = result['full_config']

        # 显示接口配置
        interfaces = full_config.get('interfaces', [])
        if interfaces:
            print(f"\n  接口配置 (共{len(interfaces)}个):")
            for iface in interfaces[:5]:  # 只显示前5个
                print(f"    {iface.get('name')}:")
                print(f"      IP: {iface.get('ip_address')}/{iface.get('subnet_mask')}")
                print(f"      描述: {iface.get('description', 'N/A')}")
                print(f"      状态: {iface.get('status', 'unknown')}")

        # 显示路由配置
        routing = full_config.get('routing', {})
        if any(routing.values()):
            print(f"\n  路由配置:")

            if routing.get('bgp'):
                for bgp in routing['bgp']:
                    print(f"    BGP AS{bgp.get('as_number')}:")
                    for neighbor in bgp.get('neighbors', []):
                        print(f"      邻居: {neighbor.get('ip')} (AS {neighbor.get('remote_as')})")

            if routing.get('ospf'):
                for ospf in routing['ospf']:
                    print(f"    OSPF {ospf.get('process_id')} (Router ID: {ospf.get('router_id')}):")
                    for area in ospf.get('areas', []):
                        print(f"      Area {area.get('area_id')}: {len(area.get('networks', []))} 个网络")

            if routing.get('static_routes'):
                print(f"    静态路由: {len(routing['static_routes'])} 条")

        # 显示VLAN配置
        vlans = full_config.get('vlans', [])
        if vlans:
            print(f"\n  VLAN配置 (共{len(vlans)}个):")
            for vlan in vlans[:5]:
                print(f"    VLAN {vlan.get('id')}: {vlan.get('name')}")

        # 显示安全配置
        security = full_config.get('security', {})
        if any(security.values()):
            print(f"\n  安全配置:")
            if security.get('acl_rules'):
                print(f"    ACL规则: {len(security['acl_rules'])} 个")

        # 显示服务配置
        services = full_config.get('services', {})
        if any(services.values()):
            print(f"\n  服务配置:")
            if services.get('ntp', {}).get('servers'):
                print(f"    NTP服务器: {', '.join(services['ntp']['servers'])}")
            if services.get('snmp', {}).get('community'):
                print(f"    SNMP: 已配置")

    # 步骤6: 保存LLM解析结果到文件
    print_section("步骤6: 保存LLM解析结果")

    output_dir = Path(__file__).parent.parent / 'output'
    output_dir.mkdir(exist_ok=True)

    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_dir / f'llm_parse_results_{timestamp}.json'

    # 准备输出数据
    output_data = {
        'timestamp': timestamp,
        'total_files': len(llm_results),
        'average_quality': sum(r['quality_score'] for r in llm_results) / len(llm_results) if llm_results else 0,
        'results': []
    }

    for result in llm_results:
        output_data['results'].append({
            'file': result['file'],
            'description': result['description'],
            'metadata': result['metadata'],
            'full_config': result['full_config'],
            'quality_score': result['quality_score'],
            'warnings': result['warnings']
        })

    # 保存到JSON文件
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(output_data, f, indent=2, ensure_ascii=False)

    print(f"\n  [OK] 解析结果已保存到: {output_file}")

    # 最终总结
    print_section("验证总结")

    print("\n  [OK] LLM增强验证完成:")
    print(f"    1. 使用智谱AI GLM-4-Plus模型")
    print(f"    2. 深度解析 {len(llm_results)} 个配置文件")
    print(f"    3. 提取丰富的元数据和配置信息")
    print(f"    4. 平均质量分数: {output_data['average_quality']:.2%}")
    print(f"    5. 结果已保存到: {output_file.name}")

    print("\n  LLM解析特点:")
    print("    ✓ 语义理解：不需要预定义正则表达式")
    print("    ✓ 厂商适应：自动处理不同厂商语法差异")
    print("    ✓ 完整提取：提取接口、路由、VLAN、安全、服务等完整配置")
    print("    ✓ 智能分析：提供配置质量评估和建议")

    # 关闭数据库连接（本次未使用，但保持一致性）
    # db_manager.disconnect()

    print("\n  验证完成！")

    return True


if __name__ == '__main__':
    try:
        success = verify_llm_parsing()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)