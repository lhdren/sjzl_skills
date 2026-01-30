---
name: paper-writing
description: >
  学术论文写作助手，涵盖从选题、文献综述、方法设计、实验分析到论文撰写的全流程。
  Use when writing academic papers, thesis, dissertations, or research manuscripts.
  Triggers on requests for "paper writing", "research paper", "thesis", "manuscript", "论文写作",
  "literature review", "学术写作", or mentions of writing academic documents.
metadata:
  author: lhdren
  version: "1.0.0"
allowed-tools:
  - Read
  - Write
  - Edit
  - Glob
  - Grep
  - Bash
  - WebSearch
  - WebFetch
  - Task
---

# 论文写作助手 (Paper Writing Assistant)

系统化学术论文写作流程，从选题到投稿的完整指南。

## 快速开始

### 核心工作流（6 个阶段）

1. **选题与文献调研** - 确定研究方向，收集相关文献
2. **论文结构规划** - 制定大纲，设计章节结构
3. **文献综述撰写** - 分析现有研究，识别研究空白
4. **方法与实验设计** - 设计实验方案，定义评估指标
5. **论文正文撰写** - 按标准格式撰写各章节
6. **修改与投稿** - 格式调整，投稿准备

### 项目初始化

创建三个核心文件：
- `PROJECT_GUIDE.md` - 项目指南和写作规范
- `WRITING_PLAN.md` - 分阶段写作计划
- `manuscript.md` - 论文正文

---

## 写作规范

### 学术语言风格

**客观陈述**：
- 使用："results suggest", "demonstrates", "indicates"
- 避免："definitely", "absolutely", "undoubtedly"

**谨慎断言**（Hedging）：
- "This method may improve..."
- "The results appear to indicate..."
- "It is reasonable to assume..."

**避免主观表达**：
- ❌ "We believe this is groundbreaking"
- ✅ "This approach shows significant improvement"

### 段落结构模板

```
主题句（核心观点）
  ↓
支持证据（引用 + 数据）
  ↓
分析讨论（批判性评价）
  ↓
过渡句（连接下一段）
```

### 引用规范

```markdown
# 单一引用
"...achieves 95% accuracy [15]"

# 多引用
"Several studies have reported... [12, 15, 23]"

# 对比引用
"While Method A [12] focuses on..., Method B [15] addresses..."

# 综述引用
"Recent advances in X include [1-5, 8, 10]"
```

---

## 标准论文结构

```markdown
# [标题]
## 摘要
## 1. 引言
### 1.1 研究背景
### 1.2 问题陈述
### 1.3 研究贡献

## 2. 相关工作
### 2.1 [领域1]研究现状
### 2.2 [领域2]研究现状
### 2.3 研究空白

## 3. 方法
### 3.1 总体框架
### 3.2 [具体方法1]
### 3.3 [具体方法2]

## 4. 实验
### 4.1 实验设置
  - 数据集（表1）
  - 评估指标
  - 实现细节
### 4.2 实验结果
  - 主要结果（表2，图1）
  - 消融实验（表3）
### 4.3 分析与讨论

## 5. 讨论
### 5.1 结果解读
### 5.2 局限性
### 5.3 未来工作

## 6. 结论
## 参考文献
```

---

## 文献来源策略

| 来源 | 适用场景 | 工具 |
|------|----------|------|
| Google Scholar | 综合文献搜索 | WebSearch |
| ArXiv | 最新预印本 | WebFetch |
| 知网/万方 | 中文文献 | WebSearch |
| PubMed | 生物医学 | WebSearch |

---

## 写作检查清单

### 内容完整性
- [ ] 摘要包含研究背景、方法、结果、结论
- [ ] 引言明确阐述研究问题和贡献
- [ ] 相关工作覆盖主要文献
- [ ] 方法描述充分可复现
- [ ] 实验部分包含数据集、指标、对比方法
- [ ] 结论总结贡献并指出局限性

### 语言质量
- [ ] 无语法和拼写错误
- [ ] 学术用语准确
- [ ] 逻辑连贯，段落过渡自然
- [ ] 避免冗余表达

### 格式规范
- [ ] 图表编号连续
- [ ] 参考文献格式统一
- [ ] 页面设置符合要求
- [ ] 字体字号统一

---

## 参考资源文件

| 文件 | 用途 |
|------|------|
| [references/WORKFLOW.md](references/WORKFLOW.md) | 6阶段详细工作流 |
| [references/TEMPLATES.md](references/TEMPLATES.md) | 项目文件模板 |
| [references/WRITING_GUIDELINES.md](references/WRITING_GUIDELINES.md) | 写作规范详解 |
| [references/SECTION_TEMPLATES.md](references/SECTION_TEMPLATES.md) | 各章节写作模板 |
