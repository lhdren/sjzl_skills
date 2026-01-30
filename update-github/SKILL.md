---
name: update-github
description: GitHub 仓库自动更新工具，用于技能文件同步。当用户需要以下操作时使用：(1) 获取所有本地 skill 文件，(2) 更新 GitHub 仓库中的技能更改，(3) 记录更新时间和更新内容。自动执行 git 操作包括 add、commit 和 push 实现技能同步。
---

# Update GitHub

自动化将本地技能文件更新到 GitHub 仓库的流程，包括记录更新时间戳和变更日志。

## 前置条件

- 当前目录必须是一个 git 仓库
- Git 必须已安装并配置
- Remote origin 必须正确配置

## 工作流程

### 1. 获取所有本地 Skill 文件

使用 Glob 查找所有 skill 文件：

```
模式: **/SKILL.md
```

这会检索所有子目录中的 SKILL.md 文件，识别所有可用的技能。

### 2. 暂存并提交更改

暂存所有技能相关文件并创建带有格式化消息的提交：

```bash
git add .
git commit -m "更新技能: <变更摘要>

更新时间: <时间戳>
变更内容:
- <列出更新的技能>
- <列出其他变更>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>"
```

### 3. 推送到 GitHub

将提交的更改推送到远程仓库：

```bash
git push origin <分支名>
```

或使用当前分支：

```bash
git push
```

## 更新日志格式

每次更新应包含：

1. **时间戳** - 更新时间（推荐使用 ISO 8601 格式，如：2026-01-30 14:30:00）
2. **摘要** - 简要描述更新了什么
3. **详细变更** - 具体变更列表：
   - 新增/修改/删除的技能
   - 配置更改
   - 文档更新

## 资源文件

### scripts/

- `update_skills.py` - 执行完整工作流程的主自动化脚本
- `list_skills.py` - 列出所有可用技能的工具

### references/

- `git-workflow.md` - Git 工作流程最佳实践
- `commit-message-format.md` - 提交消息格式指南
