#!/usr/bin/env python3
"""
Claude API 后端代理服务

用于安全地代理前端到 Claude API 的请求，避免在前端暴露 API Key。

安装依赖:
    pip install flask anthropic cors

运行:
    python simple_server.py

访问:
    http://localhost:5000
"""

from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
from anthropic import Anthropic
import os

app = Flask(__name__)
CORS(app)

# 从环境变量读取 API Key
API_KEY = os.environ.get('ANTHROPIC_API_KEY', '')

# HTML 模板
HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <title>Claude Chat - Backend Proxy</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        .container {
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 100%;
            max-width: 600px;
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }
        .chat-area {
            height: 400px;
            overflow-y: auto;
            padding: 20px;
            background: #f8f9fa;
        }
        .message { margin-bottom: 16px; }
        .message.user { text-align: right; }
        .message.assistant { text-align: left; }
        .message-bubble {
            display: inline-block;
            max-width: 80%;
            padding: 12px 16px;
            border-radius: 12px;
            word-wrap: break-word;
        }
        .message.user .message-bubble {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .message.assistant .message-bubble {
            background: white;
            border: 1px solid #e0e0e0;
        }
        .input-area {
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            display: flex;
            gap: 10px;
        }
        .input-area input {
            flex: 1;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            outline: none;
        }
        .input-area input:focus { border-color: #667eea; }
        .input-area button {
            padding: 12px 24px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            cursor: pointer;
        }
        .input-area button:disabled { opacity: 0.5; cursor: not-allowed; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>Claude Chat (Backend Proxy)</h1>
        </div>
        <div class="chat-area" id="chatArea">
            <div class="message assistant">
                <div class="message-bubble">你好！我是 Claude，通过后端代理服务运行。有什么可以帮助你的吗？</div>
            </div>
        </div>
        <div class="input-area">
            <input type="text" id="userInput" placeholder="输入问题..." />
            <button id="sendBtn" onclick="sendMessage()">发送</button>
        </div>
    </div>
    <script>
        const chatArea = document.getElementById('chatArea');
        const userInput = document.getElementById('userInput');
        const sendBtn = document.getElementById('sendBtn');

        function addMessage(role, content) {
            const msg = document.createElement('div');
            msg.className = 'message ' + role;
            msg.innerHTML = '<div class="message-bubble">' + escapeHtml(content) + '</div>';
            chatArea.appendChild(msg);
            chatArea.scrollTop = chatArea.scrollHeight;
        }

        function escapeHtml(text) {
            const div = document.createElement('div');
            div.textContent = text;
            return div.innerHTML;
        }

        async function sendMessage() {
            const prompt = userInput.value.trim();
            if (!prompt) return;

            addMessage('user', prompt);
            userInput.value = '';
            userInput.disabled = true;
            sendBtn.disabled = true;

            try {
                const res = await fetch('/api/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt })
                });
                const data = await res.json();
                addMessage('assistant', data.response);
            } catch (err) {
                addMessage('assistant', '错误: ' + err.message);
            } finally {
                userInput.disabled = false;
                sendBtn.disabled = false;
                userInput.focus();
            }
        }

        userInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') sendMessage();
        });
    </script>
</body>
</html>
"""


@app.route('/')
def index():
    """返回聊天界面"""
    return render_template_string(HTML_TEMPLATE)


@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({'error': '请提供 prompt'}), 400

    if not API_KEY:
        return jsonify({'error': '服务器未配置 API Key'}), 500

    try:
        client = Anthropic(api_key=API_KEY)

        message = client.messages.create(
            model='claude-3-5-sonnet-20241022',
            max_tokens=4096,
            messages=[{'role': 'user', 'content': prompt}]
        )

        response_text = message.content[0].text

        return jsonify({
            'response': response_text,
            'model': message.model,
            'usage': {
                'input_tokens': message.usage.input_tokens,
                'output_tokens': message.usage.output_tokens
            }
        })

    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/stream', methods=['POST'])
def stream_chat():
    """流式聊天响应"""
    from flask import Response
    import json

    data = request.json
    prompt = data.get('prompt', '')

    if not prompt:
        return jsonify({'error': '请提供 prompt'}), 400

    if not API_KEY:
        return jsonify({'error': '服务器未配置 API Key'}), 500

    def generate():
        try:
            client = Anthropic(api_key=API_KEY)

            with client.messages.stream(
                model='claude-3-5-sonnet-20241022',
                max_tokens=4096,
                messages=[{'role': 'user', 'content': prompt}]
            ) as stream:
                for text in stream.text_stream:
                    yield f"data: {json.dumps({'text': text})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'error': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({
        'status': 'ok',
        'api_configured': bool(API_KEY)
    })


if __name__ == '__main__':
    print("=" * 50)
    print("Claude API 后端代理服务")
    print("=" * 50)
    print(f"API Key 配置: {'是' if API_KEY else '否'}")
    if not API_KEY:
        print("警告: 请设置环境变量 ANTHROPIC_API_KEY")
    print()
    print("访问地址: http://localhost:5000")
    print("API 端点: http://localhost:5000/api/chat")
    print("=" * 50)

    app.run(host='0.0.0.0', port=5000, debug=True)
