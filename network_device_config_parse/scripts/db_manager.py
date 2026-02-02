#!/usr/bin/env python3
"""
Database Manager - 数据库管理模块
提供安全的数据库连接、配置管理和数据存储功能
敏感信息安全处理，配置文件不存储敏感信息
"""

import os
import getpass
import hashlib
import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path
import psycopg2
from psycopg2.extras import RealDictCursor, Json
from datetime import datetime


@dataclass
class DBConfig:
    """数据库配置（敏感信息）"""
    host: str
    port: int
    database: str
    user: str
    password: str

    def get_connection_string(self):
        """获取脱敏的连接字符串（用于日志）"""
        return f"{self.user}@{self.host}:{self.port}/{self.database}"

    def to_dict(self):
        """转换为字典（包含密码）"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': self.password
        }

    @classmethod
    def from_env(cls):
        """从环境变量加载配置"""
        return cls(
            host=os.getenv('DB_HOST', 'localhost'),
            port=int(os.getenv('DB_PORT', '5432')),
            database=os.getenv('DB_NAME', 'postgres'),
            user=os.getenv('DB_USER', 'postgres'),
            password=os.getenv('DB_PASSWORD', '')
        )

    @classmethod
    def from_prompt(cls):
        """从用户输入获取配置"""
        print("请输入数据库连接信息：")
        return cls(
            host=input("主机地址 [lhdren.cn]: ").strip() or 'lhdren.cn',
            port=int(input("端口 [15432]: ").strip() or '15432'),
            database=input("数据库 [postgres]: ").strip() or 'postgres',
            user=input("用户名 [admin]: ").strip() or 'admin',
            password=getpass.getpass("密码: ")  # 安全输入，不显示明文
        )

    def get_safe_dict(self):
        """获取安全的字典（不含密码，用于显示）"""
        return {
            'host': self.host,
            'port': self.port,
            'database': self.database,
            'user': self.user,
            'password': '****'  # 隐藏密码
        }


class DatabaseManager:
    """数据库管理器"""

    def __init__(self, config: Optional[DBConfig] = None):
        """
        初始化数据库管理器

        Args:
            config: 数据库配置，如果为 None 则从环境变量或提示用户输入
        """
        self.config = config
        self.connection = None
        self.cursor = None

    def connect(self) -> bool:
        """连接数据库"""
        try:
            if self.config is None:
                # 尝试从环境变量加载
                self.config = DBConfig.from_env()

                # 如果环境变量没有完整配置，提示用户输入
                if not self.config.password:
                    print("\n未检测到完整的环境变量配置")
                    self.config = DBConfig.from_prompt()

            print(f"\n正在连接数据库: {self.config.get_connection_string()}")

            self.connection = psycopg2.connect(
                host=self.config.host,
                port=self.config.port,
                database=self.config.database,
                user=self.config.user,
                password=self.config.password,
                cursor_factory=RealDictCursor
            )

            self.cursor = self.connection.cursor()

            # 测试连接
            self.cursor.execute("SELECT version()")
            version = self.cursor.fetchone()
            print(f"✓ 数据库连接成功")
            print(f"  PostgreSQL 版本: {version['version']}")

            return True

        except Exception as e:
            print(f"✗ 数据库连接失败: {e}")
            return False

    def disconnect(self):
        """断开数据库连接"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("\n数据库连接已关闭")

    def initialize_schema(self, schema_file: Optional[str] = None) -> bool:
        """
        初始化数据库架构

        Args:
            schema_file: SQL 架构文件路径，如果为 None 则使用默认路径
        """
        try:
            if schema_file is None:
                schema_file = Path(__file__).parent.parent / 'scripts' / 'schema.sql'

            if not Path(schema_file).exists():
                print(f"架构文件不存在: {schema_file}")
                return False

            print(f"\n正在初始化数据库架构...")

            with open(schema_file, 'r', encoding='utf-8') as f:
                sql = f.read()

            # 执行 SQL（分批执行，处理多条语句）
            self.cursor.execute(sql)

            self.connection.commit()
            print("✓ 数据库架构初始化成功")
            return True

        except Exception as e:
            print(f"✗ 架构初始化失败: {e}")
            self.connection.rollback()
            return False

    def save_parse_result(self, config_file_info: Dict[str, Any],
                         parse_data: Dict[str, Any]) -> int:
        """
        保存解析结果到数据库

        Args:
            config_file_info: 配置文件信息
            parse_data: 解析出的数据

        Returns:
            解析结果 ID
        """
        try:
            import hashlib

            # 1. 插入或获取设备元数据
            self.cursor.execute("""
                INSERT INTO device_metadata (vendor, device_type, model, software_version, config_format)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (vendor, device_type, model, software_version)
                DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                parse_data.get('metadata', {}).get('vendor'),
                parse_data.get('metadata', {}).get('device_type'),
                parse_data.get('metadata', {}).get('model'),
                parse_data.get('metadata', {}).get('software_version'),
                parse_data.get('metadata', {}).get('config_format')
            ))
            device_metadata_id = self.cursor.fetchone()['id']

            # 2. 插入配置文件记录
            file_content = config_file_info.get('content', '')
            file_hash = hashlib.md5(file_content.encode()).hexdigest() if file_content else ''

            self.cursor.execute("""
                INSERT INTO config_files
                (file_name, file_path, file_hash, file_size, content, content_preview,
                 identified_device_id, is_parsed, parse_status, uploaded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (file_hash) DO UPDATE SET
                    parsed_at = EXCLUDED.parsed_at,
                    parse_status = EXCLUDED.parse_status
                RETURNING id
            """, (
                config_file_info.get('file_name'),
                config_file_info.get('file_path'),
                file_hash,
                len(file_content),
                file_content,
                file_content[:1000] if file_content else None,
                device_metadata_id,
                True,  # is_parsed
                config_file_info.get('parse_status', 'success'),
                datetime.now()
            ))
            config_file_id = self.cursor.fetchone()['id']

            # 3. 插入解析结果
            self.cursor.execute("""
                INSERT INTO parse_results
                (config_file_id, device_metadata_id, quality_score, validation_status,
                 validation_warnings, validation_errors, parsed_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            """, (
                config_file_id,
                device_metadata_id,
                parse_data.get('quality_score', 0.0),
                parse_data.get('is_valid', 'unknown'),
                parse_data.get('warnings', []),
                parse_data.get('errors', []),
                datetime.now()
            ))
            parse_result_id = self.cursor.fetchone()['id']

            # 4. 插入设备基础信息
            device_info = parse_data.get('device_info', {})
            self.cursor.execute("""
                INSERT INTO device_info
                (parse_result_id, hostname, management_ip, mac_address, serial_number,
                 hostname_valid, management_ip_valid, mac_address_valid)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                parse_result_id,
                device_info.get('hostname'),
                device_info.get('management_ip'),
                device_info.get('mac_address'),
                device_info.get('serial_number'),
                device_info.get('hostname_valid'),
                device_info.get('management_ip_valid'),
                device_info.get('mac_address_valid')
            ))

            # 5. 插入接口配置
            interfaces = parse_data.get('interfaces', [])
            for interface in interfaces:
                self.cursor.execute("""
                    INSERT INTO interface_config
                    (parse_result_id, interface_name, interface_type, ip_address, subnet_mask,
                     description, status, vlan_id, vlan_name)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, (
                    parse_result_id,
                    interface.get('name'),
                    None,  # interface_type
                    interface.get('ip_address'),
                    interface.get('subnet_mask'),
                    interface.get('description'),
                    interface.get('status'),
                    None,  # vlan_id
                    None   # vlan_name
                ))

            self.connection.commit()
            print(f"✓ 解析结果已保存到数据库 (ID: {parse_result_id})")
            return parse_result_id

        except Exception as e:
            print(f"✗ 保存解析结果失败: {e}")
            self.connection.rollback()
            return 0

    def save_parsing_rule(self, rule_data: Dict[str, Any]) -> int:
        """
        保存解析规则到数据库

        Args:
            rule_data: 规则数据

        Returns:
            规则 ID
        """
        try:
            # 先获取或创建设备元数据
            metadata = rule_data.get('metadata', {})
            self.cursor.execute("""
                INSERT INTO device_metadata (vendor, device_type, model, software_version, config_format)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (vendor, device_type, model, software_version)
                DO UPDATE SET updated_at = CURRENT_TIMESTAMP
                RETURNING id
            """, (
                metadata.get('vendor'),
                metadata.get('device_type'),
                metadata.get('model'),
                metadata.get('software_version'),
                metadata.get('config_format')
            ))
            device_metadata_id = self.cursor.fetchone()['id']

            # 插入解析规则
            patterns = rule_data.get('patterns', {})
            for rule_name, pattern in patterns.items():
                category = self._infer_category_from_rule_name(rule_name)

                self.cursor.execute("""
                    INSERT INTO parsing_rules
                    (rule_name, rule_category, device_metadata_id, regex_pattern,
                     pattern_description, priority, is_active)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (rule_name) DO UPDATE SET
                        regex_pattern = EXCLUDED.regex_pattern,
                        updated_at = CURRENT_TIMESTAMP
                    RETURNING id
                """, (
                    rule_name,
                    category,
                    device_metadata_id,
                    pattern,
                    f"自动生成的 {category} 解析规则",
                    0,  # priority
                    True  # is_active
                ))

            self.connection.commit()
            print(f"✓ 解析规则已保存到数据库")
            return device_metadata_id

        except Exception as e:
            print(f"✗ 保存解析规则失败: {e}")
            self.connection.rollback()
            return 0

    def _infer_category_from_rule_name(self, rule_name: str) -> str:
        """从规则名称推断类别"""
        rule_lower = rule_name.lower()
        if 'hostname' in rule_lower:
            return 'hostname'
        elif 'interface' in rule_lower:
            return 'interface'
        elif 'vlan' in rule_lower:
            return 'vlan'
        elif 'ip' in rule_lower or 'address' in rule_lower:
            return 'ip_address'
        elif 'mac' in rule_lower:
            return 'mac_address'
        elif 'serial' in rule_lower:
            return 'serial_number'
        elif 'description' in rule_lower:
            return 'description'
        else:
            return 'general'

    def load_parsing_rules(self, vendor: str, device_type: str) -> List[Dict[str, Any]]:
        """
        从数据库加载解析规则

        Args:
            vendor: 厂商
            device_type: 设备类型

        Returns:
            规则列表
        """
        try:
            self.cursor.execute("""
                SELECT pr.rule_name, pr.rule_category, pr.regex_pattern,
                       pr.priority, pr.is_active, pr.success_rate
                FROM parsing_rules pr
                JOIN device_metadata dm ON pr.device_metadata_id = dm.id
                WHERE dm.vendor = %s AND dm.device_type = %s AND pr.is_active = true
                ORDER BY pr.priority, pr.rule_name
            """, (vendor, device_type))

            rules = []
            for row in self.cursor.fetchall():
                rules.append({
                    'rule_name': row['rule_name'],
                    'category': row['rule_category'],
                    'pattern': row['regex_pattern'],
                    'priority': row['priority'],
                    'success_rate': row['success_rate']
                })

            return rules

        except Exception as e:
            print(f"✗ 加载解析规则失败: {e}")
            return []

    def log_parse_event(self, config_file_id: int, level: str, message: str,
                        details: Optional[Dict] = None, duration_ms: Optional[int] = None):
        """记录解析日志"""
        try:
            self.cursor.execute("""
                INSERT INTO parse_logs
                (config_file_id, log_level, log_message, log_details, parse_duration_ms)
                VALUES (%s, %s, %s, %s, %s)
            """, (
                config_file_id,
                level,
                message,
                json.dumps(details) if details else None,
                duration_ms
            ))
            self.connection.commit()

        except Exception as e:
            print(f"✗ 记录日志失败: {e}")

    def get_parse_statistics(self) -> Dict[str, Any]:
        """获取解析统计信息"""
        try:
            # 配置文件统计
            self.cursor.execute("SELECT COUNT(*) as total FROM config_files")
            total_files = self.cursor.fetchone()['total']

            # 按状态统计
            self.cursor.execute("""
                SELECT parse_status, COUNT(*) as count
                FROM config_files
                GROUP BY parse_status
            """)
            status_stats = {row['parse_status']: row['count'] for row in self.cursor.fetchall()}

            # 平均质量分数
            self.cursor.execute("""
                SELECT AVG(quality_score) as avg_quality
                FROM parse_results
            """)
            avg_quality = self.cursor.fetchone()['avg_quality']

            # 厂商分布
            self.cursor.execute("""
                SELECT vendor, COUNT(*) as count
                FROM device_metadata dm
                JOIN config_files cf ON cf.identified_device_id = dm.id
                GROUP BY vendor
                ORDER BY count DESC
            """)
            vendor_dist = {row['vendor']: row['count'] for row in self.cursor.fetchall()}

            return {
                'total_files': total_files,
                'status_distribution': status_stats,
                'average_quality_score': float(avg_quality) if avg_quality else 0.0,
                'vendor_distribution': vendor_dist
            }

        except Exception as e:
            print(f"✗ 获取统计信息失败: {e}")
            return {}

    def __enter__(self):
        """支持 with 语句"""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """支持 with 语句"""
        if exc_type is None:
            self.disconnect()
        else:
            print(f"\n发生异常，正在关闭连接...")
            self.disconnect()


def save_connection_config_template(save_path: Optional[str] = None):
    """
    保存连接配置模板（不包含敏感信息）

    Args:
        save_path: 保存路径，如果为 None 则使用默认路径
    """
    template = {
        "DB_HOST": "lhdren.cn",
        "DB_PORT": "15432",
        "DB_NAME": "postgres",
        "DB_USER": "admin",
        "DB_PASSWORD": "YOUR_PASSWORD_HERE"
    }

    if save_path is None:
        save_path = Path(__file__).parent.parent / '.env.template'

    try:
        with open(save_path, 'w', encoding='utf-8') as f:
            f.write("# Database Configuration Template\n")
            f.write("# 复制此文件为 .env 并填入真实密码\n\n")
            for key, value in template.items():
                f.write(f"{key}={value}\n")

        print(f"✓ 配置模板已保存到: {save_path}")
        print(f"  提示: 请复制模板为 .env 文件，并修改 DB_PASSWORD 为真实密码")
        print(f"  警告: .env 文件包含敏感信息，请勿提交到版本控制系统")

        # 更新 .gitignore（如果需要）
        gitignore_path = Path(__file__).parent.parent / '.gitignore'
        if gitignore_path.exists():
            with open(gitignore_path, 'r', encoding='utf-8') as f:
                content = f.read()
            if '.env' not in content:
                with open(gitignore_path, 'a', encoding='utf-8') as f:
                    f.write("\n# Database credentials\n.env\n")
                print("✓ 已更新 .gitignore，防止 .env 文件被提交")

    except Exception as e:
        print(f"✗ 保存配置模板失败: {e}")


def main():
    """示例用法"""
    print("=" * 60)
    print("Network Device Config Parser - Database Manager")
    print("=" * 60)

    # 创建数据库管理器
    db = DatabaseManager()

    # 连接数据库
    if db.connect():
        # 初始化架构
        db.initialize_schema()

        # 获取统计信息
        stats = db.get_parse_statistics()
        print(f"\n数据库统计:")
        print(f"  总配置文件数: {stats.get('total_files', 0)}")
        print(f"  平均质量分数: {stats.get('average_quality_score', 0):.2%}")
        print(f"  状态分布: {stats.get('status_distribution', {})}")
        print(f"  厂商分布: {stats.get('vendor_distribution', {})}")

        # 断开连接
        db.disconnect()

    # 保存配置模板
    print("\n" + "=" * 60)
    save_connection_config_template()


if __name__ == '__main__':
    main()