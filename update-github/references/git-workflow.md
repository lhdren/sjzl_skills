# Git 工作流程最佳实践

## 基本工作流

1. **拉取最新代码** (在开始工作前)
   ```bash
   git pull origin <branch>
   ```

2. **检查状态**
   ```bash
   git status
   ```

3. **暂存文件**
   ```bash
   git add .              # 暂存所有更改
   git add <file>         # 暂存单个文件
   git add *.py           # 暂存所有 Python 文件
   ```

4. **提交更改**
   ```bash
   git commit -m "描述性提交消息"
   ```

5. **推送到远程**
   ```bash
   git push origin <branch>
   ```

## 常用命令

| 命令 | 说明 |
|------|------|
| `git log --oneline` | 查看简洁的提交历史 |
| `git diff` | 查看未暂存的更改 |
| `git diff --staged` | 查看已暂存的更改 |
| `git branch` | 列出所有分支 |
| `git branch -a` | 列出所有分支（包括远程） |
| `git checkout -b <branch>` | 创建并切换到新分支 |
| `git merge <branch>` | 合并指定分支 |

## 提交消息格式

遵循约定式提交 (Conventional Commits) 格式：

```
<类型>(<范围>): <描述>

[可选的正文]

[可选的脚注]
```

### 类型

- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更改
- `style`: 代码格式（不影响代码运行）
- `refactor`: 重构
- `test`: 添加测试
- `chore`: 构建过程或辅助工具的变动

### 示例

```bash
git commit -m "feat(skills): 添加 update-github 技能"
git commit -m "fix: 修复提交消息编码问题"
git commit -m "docs: 更新 README 说明"
```

## 技能更新专用流程

对于 skills 仓库，使用以下提交格式：

```
更新技能: <简短摘要>

更新时间: YYYY-MM-DD HH:MM:SS
变更内容:
- 新增: <skill-name>
- 修改: <skill-name>
- 删除: <skill-name>

Co-Authored-By: Claude Sonnet 4.5 <noreply@anthropic.com>
```
