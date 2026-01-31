# Claude API 集成指南

本指南详细介绍如何在前端页面中集成 Claude API。

## 目录

1. [获取 API Key](#获取-api-key)
2. [基础 API 调用](#基础-api-调用)
3. [流式响应](#流式响应)
4. [错误处理](#错误处理)
5. [最佳实践](#最佳实践)

---

## 获取 API Key

1. 访问 [Anthropic Console](https://console.anthropic.com/)
2. 登录或注册账户
3. 进入 API Keys 页面
4. 创建新的 API Key
5. **重要**：妥善保管 API Key，不要提交到代码仓库

---

## 基础 API 调用

### 请求格式

```javascript
const response = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': 'your-api-key',
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json',
    'dangerously-allow-browser': 'true'  // 仅用于开发测试
  },
  body: JSON.stringify({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 4096,
    messages: [
      { role: 'user', content: 'Hello, Claude!' }
    ]
  })
});
```

### 可用模型

| 模型 | 用途 | 最大 token |
|------|------|------------|
| `claude-3-5-sonnet-20241022` | 通用，平衡性能和成本 | 200,000 |
| `claude-3-5-haiku-20241022` | 快速响应 | 200,000 |
| `claude-3-opus-20240229` | 最强性能 | 200,000 |

### 响应格式

```json
{
  "id": "msg_xxx",
  "type": "message",
  "role": "assistant",
  "content": [
    {
      "type": "text",
      "text": "回复内容..."
    }
  ],
  "model": "claude-3-5-sonnet-20241022",
  "stop_reason": "end_turn",
  "usage": {
    "input_tokens": 10,
    "output_tokens": 20
  }
}
```

---

## 流式响应

流式响应可以实时显示 Claude 的生成过程，提升用户体验。

### 启用流式

在请求中添加 `stream: true`：

```javascript
const response = await fetch('https://api.anthropic.com/v1/messages', {
  method: 'POST',
  headers: {
    'x-api-key': apiKey,
    'anthropic-version': '2023-06-01',
    'content-type': 'application/json'
  },
  body: JSON.stringify({
    model: 'claude-3-5-sonnet-20241022',
    max_tokens: 4096,
    stream: true,  // 启用流式
    messages: [{ role: 'user', content: prompt }]
  })
});
```

### 处理流式响应

```javascript
const reader = response.body.getReader();
const decoder = new TextDecoder();
let fullText = '';

while (true) {
  const { done, value } = await reader.read();
  if (done) break;

  const chunk = decoder.decode(value);
  const lines = chunk.split('\n');

  for (const line of lines) {
    if (line.startsWith('data: ')) {
      const data = line.slice(6);
      if (data === '[DONE]') continue;

      const parsed = JSON.parse(data);

      // 处理不同类型的事件
      if (parsed.type === 'content_block_delta') {
        const text = parsed.delta?.text || '';
        fullText += text;
        // 实时更新 UI
        updateUI(fullText);
      }
    }
  }
}
```

### 流式事件类型

| 事件类型 | 说明 |
|----------|------|
| `message_start` | 消息开始 |
| `content_block_start` | 内容块开始 |
| `content_block_delta` | 新增文本内容 |
| `content_block_stop` | 内容块结束 |
| `message_delta` | 消息增量（包含 usage） |
| `message_stop` | 消息结束 |

---

## 错误处理

### 常见错误

| 错误代码 | 说明 | 解决方案 |
|----------|------|----------|
| 401 | API Key 无效 | 检查 API Key 是否正确 |
| 429 | 速率限制 | 减少请求频率或升级套餐 |
| 400 | 请求格式错误 | 检查请求参数 |
| 500 | 服务器错误 | 稍后重试 |

### 错误处理示例

```javascript
try {
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({ /* ... */ })
  });

  if (!response.ok) {
    const error = await response.json();

    // 处理特定错误
    switch (response.status) {
      case 401:
        showError('API Key 无效，请检查配置');
        break;
      case 429:
        showError('请求过于频繁，请稍后再试');
        break;
      case 400:
        showError(`请求错误: ${error.error?.message}`);
        break;
      default:
        showError(`服务器错误: ${error.error?.message}`);
    }
    return;
  }

  const data = await response.json();
  // 处理成功响应

} catch (error) {
  showError(`网络错误: ${error.message}`);
}
```

---

## 最佳实践

### 1. 安全性

**❌ 不推荐**：在前端硬编码 API Key

```javascript
const apiKey = 'sk-ant-api03-...';  // 危险！
```

**✅ 推荐**：使用后端代理

```javascript
// 前端调用后端
const response = await fetch('/api/chat', {
  method: 'POST',
  body: JSON.stringify({ prompt: userMessage })
});
```

**后端代理示例**：

```python
# Flask 后端
from flask import Flask, request, jsonify
from anthropic import Anthropic

app = Flask(__name__)
client = Anthropic(api_key=os.environ.get('ANTHROPIC_API_KEY'))

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    message = client.messages.create(
        model='claude-3-5-sonnet-20241022',
        max_tokens=4096,
        messages=[{'role': 'user', 'content': data['prompt']}]
    )
    return jsonify({'response': message.content[0].text})
```

### 2. 上下文管理

对于多轮对话，需要维护对话历史：

```javascript
let conversationHistory = [];

async function sendMessage(userMessage) {
  // 添加用户消息
  conversationHistory.push({
    role: 'user',
    content: userMessage
  });

  // 调用 API
  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: { /* ... */ },
    body: JSON.stringify({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      messages: conversationHistory  // 包含历史
    })
  });

  const data = await response.json();

  // 添加助手回复
  conversationHistory.push({
    role: 'assistant',
    content: data.content[0].text
  });

  return data.content[0].text;
}
```

### 3. 参数调优

| 参数 | 推荐值 | 说明 |
|------|--------|------|
| `max_tokens` | 4096 | 输出最大长度 |
| `temperature` | 0.7 | 控制随机性 (0-1) |
| `top_p` | 0.9 | 核采样参数 |
| `top_k` | 40 | 采样候选数 |

```javascript
body: JSON.stringify({
  model: 'claude-3-5-sonnet-20241022',
  max_tokens: 4096,
  temperature: 0.7,  // 创造性任务可以设为 0.9-1.0
  top_p: 0.9,
  messages: [{ role: 'user', content: prompt }]
})
```

### 4. 用户体验

**加载状态**：

```javascript
function setLoading(isLoading) {
  const btn = document.getElementById('sendBtn');
  btn.disabled = isLoading;
  btn.textContent = isLoading ? '发送中...' : '发送';
}
```

**自动滚动**：

```javascript
function scrollToBottom() {
  const chatArea = document.getElementById('chatArea');
  chatArea.scrollTop = chatArea.scrollHeight;
}
```

**Markdown 渲染**（可选）：

```javascript
// 使用 marked.js 库
import { marked } from 'marked';

function renderMessage(text) {
  return marked.parse(text);
}
```

### 5. 成本优化

- 使用 `claude-3-5-haiku` 处理简单任务
- 缓存常见问题的回答
- 限制上下文长度，删除过期消息

```javascript
// 限制上下文为最近 10 条消息
const MAX_CONTEXT = 10;

function trimHistory(history) {
  return history.slice(-MAX_CONTEXT);
}
```

---

## 完整示例

```javascript
class ClaudeChat {
  constructor(apiKey, model = 'claude-3-5-sonnet-20241022') {
    this.apiKey = apiKey;
    this.model = model;
    this.history = [];
  }

  async sendMessage(content, onChunk = null) {
    this.history.push({ role: 'user', content });

    const response = await fetch('https://api.anthropic.com/v1/messages', {
      method: 'POST',
      headers: {
        'x-api-key': this.apiKey,
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json'
      },
      body: JSON.stringify({
        model: this.model,
        max_tokens: 4096,
        messages: this.history
      })
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }

    const data = await response.json();
    const assistantMessage = data.content[0].text;

    this.history.push({ role: 'assistant', content: assistantMessage });

    return assistantMessage;
  }

  clearHistory() {
    this.history = [];
  }
}

// 使用示例
const chat = new ClaudeChat('your-api-key');

async function handleSend() {
  const input = document.getElementById('userInput');
  const message = input.value;

  try {
    const response = await chat.sendMessage(message);
    console.log('Claude:', response);
  } catch (error) {
    console.error('Error:', error);
  }
}
```

---

## 参考资源

- [Anthropic API 官方文档](https://docs.anthropic.com/)
- [Messages API 参考](https://docs.anthropic.com/claude/reference/messages_post)
- [流式响应文档](https://docs.anthropic.com/claude/reference/streaming)
