#!/usr/bin/env python3
"""
List Skills - 列出所有本地技能文件

使用方法：
    python list_skills.py
"""

from pathlib import Path


def list_all_skills():
    """列出所有 skills"""
    skills_dir = Path(__file__).parent.parent
    skill_files = list(skills_dir.glob("*/SKILL.md"))

    print("=" * 50)
    print(f"本地技能列表 (共 {len(skill_files)} 个)")
    print("=" * 50)

    for skill_file in sorted(skill_files):
        skill_name = skill_file.parent.name
        # 读取 skill 描述
        try:
            with open(skill_file, "r", encoding="utf-8") as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith("description:"):
                        desc = line.split(":", 1)[1].strip()
                        print(f"\n[{skill_name}]")
                        print(f"  {desc[:80]}{'...' if len(desc) > 80 else ''}")
                        break
        except Exception as e:
            print(f"\n[{skill_name}]")
            print(f"  (无法读取描述: {e})")

    print("\n" + "=" * 50)


if __name__ == "__main__":
    list_all_skills()
