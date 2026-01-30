#!/usr/bin/env python3
"""
Update Skills - 自动更新本地技能文件到 GitHub 仓库

功能：
1. 获取所有本地 skill 文件
2. 执行 git add、commit、push
3. 记录更新时间和变更内容

使用方法：
    python update_skills.py [--message "自定义提交消息"]
"""

import sys
import subprocess
from datetime import datetime
from pathlib import Path


def run_command(cmd, description=""):
    """执行 shell 命令并返回结果"""
    try:
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if result.returncode != 0:
            print(f"错误: {description} 失败")
            print(f"错误信息: {result.stderr}")
            return False, result.stderr
        return True, result.stdout
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False, str(e)


def get_all_skills():
    """获取所有本地 skill 文件"""
    skills_dir = Path(__file__).parent.parent
    skill_files = list(skills_dir.glob("*/SKILL.md"))
    return [f.parent.name for f in skill_files]


def get_current_branch():
    """获取当前 git 分支"""
    success, output = run_command("git rev-parse --abbrev-ref HEAD", "获取分支")
    if success:
        return output.strip()
    return None


def get_git_status():
    """获取 git 状态"""
    success, output = run_command("git status --short", "获取状态")
    if success:
        return output.strip()
    return ""


def update_github(custom_message=None):
    """主函数：更新 GitHub 仓库"""
    print("=" * 50)
    print("GitHub Skills 更新工具")
    print("=" * 50)

    # 1. 检查是否在 git 仓库中
    success, _ = run_command("git rev-parse --git-dir", "检查 git 仓库")
    if not success:
        print("错误: 当前目录不是一个 git 仓库")
        return False

    # 2. 获取所有 skills
    print("\n[1/4] 扫描本地 skills...")
    skills = get_all_skills()
    print(f"找到 {len(skills)} 个技能:")
    for skill in sorted(skills):
        print(f"  - {skill}")

    # 3. 检查变更
    print("\n[2/4] 检查文件变更...")
    status = get_git_status()
    if not status:
        print("没有检测到变更，无需更新")
        return True
    print("检测到以下变更:")
    print(status)

    # 4. 获取当前分支
    print("\n[3/4] 准备提交...")
    branch = get_current_branch()
    if not branch:
        print("错误: 无法获取当前分支")
        return False
    print(f"当前分支: {branch}")

    # 5. 暂存所有文件
    print("\n暂存文件...")
    success, _ = run_command("git add .", "暂存文件")
    if not success:
        return False

    # 6. 创建提交
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if custom_message:
        commit_msg = custom_message
    else:
        commit_msg = f"""更新技能文件

更新时间: {timestamp}
变更内容:
- 同步本地技能到 GitHub 仓库
- 更新 {len(skills)} 个技能文件

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"""

    print(f"\n提交消息:")
    print("-" * 40)
    print(commit_msg)
    print("-" * 40)

    success, output = run_command(
        f'git commit -m "{commit_msg}"',
        "创建提交"
    )
    if not success:
        print("注意: 没有新的变更需要提交")
        return True
    print("提交成功!")

    # 7. 推送到 GitHub
    print(f"\n[4/4] 推送到 GitHub (分支: {branch})...")
    success, output = run_command(
        f"git push origin {branch}",
        "推送"
    )
    if not success:
        return False
    print("推送成功!")

    print("\n" + "=" * 50)
    print("更新完成!")
    print(f"时间: {timestamp}")
    print("=" * 50)
    return True


def main():
    """命令行入口"""
    custom_message = None
    if len(sys.argv) > 1 and sys.argv[1] == "--message":
        if len(sys.argv) > 2:
            custom_message = sys.argv[2]
        else:
            print("错误: --message 参数需要提供消息内容")
            sys.exit(1)

    success = update_github(custom_message)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
