---
name: web-hook
description: >
  快速创建 Web 前端页面，收集用户指令，集成 Claude API 进行智能对话。
  Use when creating web interfaces that collect user input and process with Claude AI.
  Triggers on requests for "web page", "frontend", "chat interface", "Claude integration",
  "webhook", "对话界面", "前端页面", "网页开发", or "API 集成".
metadata:
  author: lhdren
  version: "1.0.0"
allowed-tools:
  - Read
  - Write
  - Edit
  - Bash
  - WebFetch
---

# Web Hook - Claude 集成前端页面生成工具

快速创建集成了 Claude API 的 Web 前端页面，用于收集用户指令并与 Claude 进行智能对话。

## 快速开始

### 核心功能

1. **前端页面生成** - 自动生成美观的 Web 界面
2. **指令收集** - 支持文本输入、参数配置等多种方式
3. **Claude API 集成** - 无缝对接 Claude API 进行智能对话
4. **响应展示** - 实时显示 Claude 的回复

### 适用场景

- 客服机器人界面
- 智能问答系统
- 命令行工具的 Web 封装
- 自动化脚本的可视化控制台
- Claude API 应用开发

---

## 工作流程

### 1. 选择页面模板

提供多种预置模板：

| 模板 | 适用场景 | 文件 |
|------|----------|------|
| **简单聊天** | 基础对话界面 | `templates/simple-chat.html` |
| **参数化指令** | 需要配置参数的任务 | `templates/command-form.html` |
| **流式输出** | 实时显示 Claude 回复 | `templates/streaming-chat.html` |
| **多轮对话** | 支持上下文的对话 | `templates/multi-turn-chat.html` |

### 2. 配置 Claude API

在生成的页面中配置 API：

```javascript
const claudeConfig = {
  apiKey: 'your-api-key',           // Claude API Key
  model: 'claude-3-5-sonnet-20241022', // 模型版本
  maxTokens: 4096,                   // 最大 token 数
  temperature: 0.7                   // 温度参数
};
```

### 3. 自定义页面（可选）

根据需求修改：
- UI 样式和布局
- 输入字段和参数
- API 调用逻辑
- 响应展示方式

### 4. 部署运行

```bash
# 使用 Python HTTP 服务器
python -m http.server 8000

# 或使用 Node.js
npx serve .

# 访问 http://localhost:8000
```

---

## 模板说明

### 模板 1: Simple Chat（简单聊天）

**文件**: `templates/simple-chat.html`

**特点**：
- 极简设计
- 基础对话功能
- 单轮提问回答
- 适合快速测试

**使用场景**：
- API 测试
- 简单问答
- 原型验证

### 模板 2: Command Form（指令表单）

**文件**: `templates/command-form.html`

**特点**：
- 结构化输入
- 参数配置
- 预设指令模板
- 表单验证

**使用场景**：
- 任务自动化
- 脚本执行
- 参数化查询

### 模板 3: Streaming Chat（流式聊天）

**文件**: `templates/streaming-chat.html`

**特点**：
- 实时流式输出
- 打字机效果
- 中断和继续
- 适合长文本生成

**使用场景**：
- 内容生成
- 代码编写
- 文档创作

### 模板 4: Multi-turn Chat（多轮对话）

**文件**: `templates/multi-turn-chat.html`

**特点**：
- 会话历史管理
- 上下文保持
- 导出对话记录
- 清空会话

**使用场景**：
- 复杂任务分解
- 迭代优化
- 知识问答

---

## API 集成指南

### Claude API 调用示例

```javascript
// 基础调用
async function callClaude(prompt, config) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': config.apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      model: config.model,
      max_tokens: config.maxTokens,
      messages: [{ role: 'user', content: prompt }]
    })
  });

  const data = await response.json();
  return data.content[0].text;
}

// 流式调用
async function callClaudeStream(prompt, config, onChunk) {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': config.apiKey,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      model: config.model,
      max_tokens: config.maxTokens,
      stream: true,
      messages: [{ role: 'user', content: prompt }]
    })
  });

  const reader = response.body.getReader();
  const decoder = new TextDecoder();

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;

    const chunk = decoder.decode(value);
    onChunk(chunk);
  }
}
```

---

## 常见使用模式

### 模式 1: 快速测试 API

```
1. 选择 simple-chat 模板
2. 配置 API Key
3. 在浏览器中打开
4. 输入问题，查看回复
```

### 模式 2: 构建客服机器人

```
1. 选择 multi-turn-chat 模板
2. 添加系统提示词
3. 自定义 UI 样式
4. 集成到现有网站
```

### 模式 3: 自动化工具界面

```
1. 选择 command-form 模板
2. 配置预设指令
3. 添加参数验证
4. 部署为内部工具
```

### 模式 4: 内容生成工具

```
1. 选择 streaming-chat 模板
2. 配置生成参数
3. 添加复制/下载功能
4. 包装为 SaaS 产品
```

---

## 最佳实践

### 安全性

1. **API Key 保护**
   - 不要在前端代码中硬编码 API Key
   - 使用后端代理 API 调用
   - 实施 CORS 策略

2. **输入验证**
   - 验证用户输入
   - 限制输入长度
   - 过滤敏感内容

3. **速率限制**
   - 限制请求频率
   - 实施配额管理
   - 缓存常见查询

### 用户体验

1. **加载状态**
   - 显示加载动画
   - 禁用提交按钮
   - 提供进度反馈

2. **错误处理**
   - 友好的错误提示
   - 重试机制
   - 降级方案

3. **响应式设计**
   - 支持移动端
   - 自适应布局
   - 触摸优化

---

## 扩展功能

### 后端服务

如果需要更强大的功能，可以部署后端服务：

```python
# scripts/simple_server.py
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic(api_key='your-api-key')

@app.route('/chat', methods=['POST'])
def chat():
    data = request.json
    message = client.messages.create(
        model='claude-3-5-sonnet-20241022',
        max_tokens=4096,
        messages=[{'role': 'user', 'content': data['prompt']}]
    )
    return jsonify({'response': message.content[0].text})

if __name__ == '__main__':
    app.run(port=5000)
```

### 数据持久化

```javascript
// 保存对话历史
function saveConversation(messages) {
  localStorage.setItem('chat-history', JSON.stringify(messages));
}

// 加载对话历史
function loadConversation() {
  const saved = localStorage.getItem('chat-history');
  return saved ? JSON.parse(saved) : [];
}
```

---

## 参考资源文件

| 文件 | 用途 |
|------|------|
| [templates/simple-chat.html](templates/simple-chat.html) | 简单聊天模板 |
| [templates/command-form.html](templates/command-form.html) | 指令表单模板 |
| [templates/streaming-chat.html](templates/streaming-chat.html) | 流式聊天模板 |
| [templates/multi-turn-chat.html](templates/multi-turn-chat.html) | 多轮对话模板 |
| [scripts/simple_server.py](scripts/simple_server.py) | Python 后端服务 |
| [references/API_GUIDE.md](references/API_GUIDE.md) | Claude API 详解 |
| [references/DEPLOYMENT.md](references/DEPLOYMENT.md) | 部署指南 |
