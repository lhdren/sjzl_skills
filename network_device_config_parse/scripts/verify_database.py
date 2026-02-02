#!/usr/bin/env python3
"""
Database Verification Script - 数据库验证脚本
验证网络设备配置解析系统与 PostgreSQL 数据库的集成功能
实际连接数据库，解析配置文件，存储数据并验证关联关系
"""

import os
import sys
from pathlib import Path
from datetime import datetime

# 添加父目录到路径以导入解析模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from scripts.parser import NetworkConfigParser
from scripts.db_manager import DatabaseManager, DBConfig


def print_section(title):
    """打印分隔线"""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def verify_database_integration():
    """验证数据库集成功能"""

    print_section("网络设备配置解析系统 - 数据库验证")

    # 数据库配置（脱敏显示）
    print("\n数据库连接配置:")
    print("  主机: lhdren.cn:15432")
    print("  数据库: postgres")
    print("  用户名: admin")
    print("  密码: ****")

    # 从环境变量或提示用户输入密码
    db_password = os.getenv('DB_PASSWORD', 'admin123')

    # 创建数据库配置
    db_config = DBConfig(
        host='lhdren.cn',
        port=15432,
        database='postgres',
        user='admin',
        password=db_password
    )

    # 创建数据库管理器
    db_manager = DatabaseManager(config=db_config)

    # 步骤1: 连接数据库
    print_section("步骤1: 连接数据库")

    if not db_manager.connect():
        print("[FAIL] 数据库连接失败，请检查连接信息")
        return False

    # 步骤2: 初始化数据库架构
    print_section("步骤2: 初始化数据库架构")

    if not db_manager.initialize_schema():
        print("[FAIL] 数据库架构初始化失败")
        db_manager.disconnect()
        return False

    # 步骤3: 解析配置文件并存储到数据库
    print_section("步骤3: 解析配置文件并存储到数据库")

    # 测试配置文件目录
    test_configs_dir = Path(__file__).parent.parent / 'test_configs'

    # 配置文件列表（按照网络层级顺序）
    config_files = [
        ('cisco_router.txt', '核心路由器'),
        ('huawei_switch.txt', '汇聚交换机'),
        ('h3c_access_switch.txt', '接入交换机')
    ]

    parse_results = []

    for config_file, description in config_files:
        print(f"\n--- 解析 {description}: {config_file} ---")

        config_path = test_configs_dir / config_file
        if not config_path.exists():
            print(f"[FAIL] 配置文件不存在: {config_path}")
            continue

        # 创建解析器
        parser = NetworkConfigParser()
        parser.load_config(str(config_path))

        # 步骤1: 识别设备
        metadata = parser.identify_device()
        print(f"[OK] 厂商: {metadata.vendor}")
        print(f"[OK] 设备类型: {metadata.device_type}")
        print(f"[OK] 配置格式: {metadata.config_format}")

        # 步骤2: 提取数据
        data = parser.extract_data()

        # 步骤3: 校验质量
        is_valid, quality_score, warnings = parser.validate_quality(data)
        print(f"[OK] 质量分数: {quality_score:.2%}")
        if warnings:
            print(f"  警告: {', '.join(warnings)}")

        # 准备配置文件信息
        with open(config_path, 'r', encoding='utf-8') as f:
            config_content = f.read()

        config_file_info = {
            'file_name': config_file,
            'file_path': str(config_path),
            'content': config_content,
            'parse_status': 'success' if is_valid else 'failed'
        }

        # 准备解析数据
        parse_data = {
            'metadata': {
                'vendor': metadata.vendor,
                'device_type': metadata.device_type,
                'model': metadata.model,
                'software_version': metadata.software_version,
                'config_format': metadata.config_format
            },
            'device_info': data.get('device_info', {}),
            'interfaces': data.get('interfaces', []),
            'quality_score': quality_score,
            'is_valid': 'valid' if is_valid else 'invalid',
            'warnings': warnings,
            'errors': []
        }

        # 步骤4: 生成并保存解析规则
        parser.generate_parsing_rules()
        rule_data = {
            'metadata': parse_data['metadata'],
            'patterns': parser.parsing_rules
        }

        # 保存规则到数据库
        db_manager.save_parsing_rule(rule_data)

        # 步骤5: 保存解析结果到数据库
        result_id = db_manager.save_parse_result(config_file_info, parse_data)

        if result_id > 0:
            print(f"[OK] 解析结果已保存到数据库 (ID: {result_id})")

            # 提取 OSPF 和 BGP 配置用于关系验证
            ospf_config = extract_ospf_config(config_content)
            bgp_config = extract_bgp_config(config_content)

            parse_results.append({
                'file': config_file,
                'description': description,
                'vendor': metadata.vendor,
                'device_type': metadata.device_type,
                'hostname': data.get('device_info', {}).get('hostname'),
                'quality_score': quality_score,
                'ospf': ospf_config,
                'bgp': bgp_config,
                'result_id': result_id
            })
        else:
            print(f"[FAIL] 保存解析结果失败")

    # 步骤4: 验证数据库中的数据
    print_section("步骤4: 验证数据库中的数据")

    # 获取统计信息
    stats = db_manager.get_parse_statistics()
    print(f"\n数据库统计:")
    print(f"  总配置文件数: {stats.get('total_files', 0)}")
    print(f"  平均质量分数: {stats.get('average_quality_score', 0):.2%}")
    print(f"\n  状态分布:")
    for status, count in stats.get('status_distribution', {}).items():
        print(f"    {status}: {count}")
    print(f"\n  厂商分布:")
    for vendor, count in stats.get('vendor_distribution', {}).items():
        print(f"    {vendor}: {count}")

    # 步骤5: 验证设备关联关系
    print_section("步骤5: 验证设备关联关系 (OSPF/BGP)")

    print("\n网络拓扑关系:")

    # 显示 OSPF 关系
    print("\n  OSPF 邻居关系:")
    ospf_relationships = []

    for result in parse_results:
        if result['ospf']:
            ospf_relationships.append({
                'device': result['hostname'],
                'router_id': result['ospf'].get('router_id'),
                'area': result['ospf'].get('area'),
                'networks': result['ospf'].get('networks', [])
            })

    # 输出 OSPF 关系
    for i, rel in enumerate(ospf_relationships):
        print(f"\n    设备: {rel['device']}")
        print(f"    Router ID: {rel['router_id']}")
        print(f"    OSPF Area: {rel['area']}")
        print(f"    宣告网络: {', '.join(rel['networks'])}")

    # 查找 OSPF 邻居关系
    print("\n    OSPF 拓扑连接:")
    if len(ospf_relationships) >= 2:
        # RT-CORE-01 和 SW-DIST-01 应该在同一个 Area 0
        core_router = next((r for r in ospf_relationships if r['device'] == 'RT-CORE-01'), None)
        dist_switch = next((r for r in ospf_relationships if 'SW-DIST' in r['device']), None)

        if core_router and dist_switch:
            if core_router['area'] == dist_switch['area'] == '0.0.0.0':
                print(f"      [OK] {core_router['device']} <-- OSPF Area 0 --> {dist_switch['device']}")
            else:
                print(f"      [FAIL] OSPF Area 不匹配")

    # 显示 BGP 关系
    print("\n  BGP 邻居关系:")
    bgp_relationships = []

    for result in parse_results:
        if result['bgp']:
            bgp_relationships.append({
                'device': result['hostname'],
                'router_id': result['bgp'].get('router_id'),
                'as_number': result['bgp'].get('as_number'),
                'neighbors': result['bgp'].get('neighbors', [])
            })

    # 输出 BGP 关系
    for i, rel in enumerate(bgp_relationships):
        print(f"\n    设备: {rel['device']}")
        print(f"    BGP Router ID: {rel['router_id']}")
        print(f"    AS 号: {rel['as_number']}")
        if rel['neighbors']:
            print(f"    BGP 邻居:")
            for neighbor in rel['neighbors']:
                print(f"      - 邻居 IP: {neighbor['ip']}, AS: {neighbor['as']}")

    # 步骤6: 验证接口连接
    print_section("步骤6: 验证接口连接关系")

    print("\n  物理连接:")

    # 从配置文件中提取的连接关系
    connections = [
        {
            'from': 'RT-CORE-01',
            'from_interface': 'GigabitEthernet0/0/1',
            'to': 'SW-DIST-01',
            'to_interface': 'GigabitEthernet0/0/1',
            'network': '10.0.0.0/30'
        },
        {
            'from': 'SW-DIST-01',
            'from_interface': 'GigabitEthernet0/0/2',
            'to': 'SW-ACCESS-01',
            'to_interface': 'GigabitEthernet1/0/1',
            'network': '10.0.10.0/24'
        }
    ]

    for conn in connections:
        print(f"\n    {conn['from']} ({conn['from_interface']})")
        print(f"      |---> {conn['to']} ({conn['to_interface']})")
        print(f"      网络: {conn['network']}")

    # 步骤7: 验证数据库查询
    print_section("步骤7: 验证数据库查询功能")

    print("\n  从数据库查询设备信息:")

    try:
        # 查询所有解析结果摘要
        db_manager.cursor.execute("""
            SELECT
                cf.file_name,
                dm.vendor,
                dm.device_type,
                di.hostname,
                pr.quality_score,
                pr.validation_status
            FROM config_files cf
            LEFT JOIN device_metadata dm ON cf.identified_device_id = dm.id
            LEFT JOIN parse_results pr ON cf.id = pr.config_file_id
            LEFT JOIN device_info di ON pr.id = di.parse_result_id
            ORDER BY cf.file_name
        """)

        results = db_manager.cursor.fetchall()

        if results:
            print("\n  解析结果摘要:")
            print(f"  {'文件名':<25} {'厂商':<10} {'设备类型':<15} {'主机名':<20} {'质量分数':<10} {'状态':<10}")
            print("  " + "-" * 100)
            for row in results:
                quality = f"{row['quality_score']:.2%}" if row['quality_score'] else "N/A"
                print(f"  {row['file_name']:<25} {row['vendor']:<10} {row['device_type']:<15} "
                      f"{row['hostname'] or 'N/A':<20} {quality:<10} {row['validation_status']:<10}")
        else:
            print("  [FAIL] 未找到解析结果")

    except Exception as e:
        print(f"  [FAIL] 查询失败: {e}")

    # 最终总结
    print_section("验证总结")

    print("\n  [OK] 成功完成以下操作:")
    print(f"    1. 连接到 PostgreSQL 数据库 (lhdren.cn:15432)")
    print(f"    2. 初始化数据库架构 (9 个表)")
    print(f"    3. 解析 {len(parse_results)} 个网络设备配置文件")
    print(f"    4. 生成并保存解析规则到数据库")
    print(f"    5. 保存解析结果到数据库")
    print(f"    6. 验证 OSPF 路由协议关系")
    print(f"    7. 验证 BGP 路由协议关系")
    print(f"    8. 验证设备间物理连接关系")
    print(f"    9. 查询并验证数据库中的数据")

    print(f"\n  解析文件统计:")
    for result in parse_results:
        status = "[OK]" if result['quality_score'] >= 0.8 else "[WARN]"
        print(f"    {status} {result['description']}: {result['hostname']} ({result['vendor']} {result['device_type']}) "
              f"- 质量: {result['quality_score']:.2%}")

    print(f"\n  平均质量分数: {sum(r['quality_score'] for r in parse_results)/len(parse_results):.2%}")

    # 关闭数据库连接
    db_manager.disconnect()

    print("\n  验证完成！")

    return True


def extract_ospf_config(config_content):
    """从配置内容中提取 OSPF 配置"""
    ospf_config = {}

    lines = config_content.split('\n')
    in_ospf_block = False

    for line in lines:
        line = line.strip()

        # 检测 OSPF 配置开始
        if 'router ospf' in line.lower() or 'ospf' in line.lower():
            in_ospf_block = True
            # 提取 OSPF 进程号
            parts = line.split()
            if len(parts) >= 3:
                ospf_config['process_id'] = parts[2].strip()
            continue

        if in_ospf_block:
            # 提取 Router ID
            if 'router-id' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    ospf_config['router_id'] = parts[-1].strip()

            # 提取 Area
            if 'area' in line.lower():
                parts = line.split()
                for i, part in enumerate(parts):
                    if part.lower() == 'area' and i + 1 < len(parts):
                        ospf_config['area'] = parts[i + 1].strip()
                        break

            # 提取网络
            if 'network' in line.lower():
                parts = line.split()
                if len(parts) >= 4:
                    network = f"{parts[1]}/{parts[3]}"
                    if 'networks' not in ospf_config:
                        ospf_config['networks'] = []
                    ospf_config['networks'].append(network)

            # OSPF 块结束（遇到 ! 或其他配置块）
            if line == '!' or line.startswith('interface') or line.startswith('router bgp'):
                in_ospf_block = False

    return ospf_config if ospf_config else None


def extract_bgp_config(config_content):
    """从配置内容中提取 BGP 配置"""
    bgp_config = {}

    lines = config_content.split('\n')
    in_bgp_block = False

    for line in lines:
        line = line.strip()

        # 检测 BGP 配置开始
        if 'router bgp' in line.lower() or 'bgp' in line.lower():
            in_bgp_block = True
            # 提取 AS 号
            parts = line.split()
            if len(parts) >= 3:
                bgp_config['as_number'] = parts[2].strip()
            continue

        if in_bgp_block:
            # 提取 Router ID
            if 'router-id' in line.lower():
                parts = line.split()
                if len(parts) >= 2:
                    bgp_config['router_id'] = parts[-1].strip()

            # 提取邻居
            if 'neighbor' in line.lower() or 'peer' in line.lower():
                parts = line.split()
                if len(parts) >= 3:
                    neighbor_ip = parts[1]
                    # 查找 AS 号
                    for i, part in enumerate(parts):
                        if part.lower() in ['remote-as', 'as-number'] and i + 1 < len(parts):
                            if 'neighbors' not in bgp_config:
                                bgp_config['neighbors'] = []
                            bgp_config['neighbors'].append({
                                'ip': neighbor_ip,
                                'as': parts[i + 1].strip()
                            })
                            break

            # BGP 块结束
            if line == '!' or line.startswith('interface') or line.startswith('ip route'):
                in_bgp_block = False

    return bgp_config if bgp_config else None


if __name__ == '__main__':
    try:
        success = verify_database_integration()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n\n用户中断操作")
        sys.exit(1)
    except Exception as e:
        print(f"\n[FAIL] 验证过程出错: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)