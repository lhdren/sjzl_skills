# 部署指南

本指南介绍如何部署 Claude 集成的 Web 应用。

## 目录

1. [本地部署](#本地部署)
2. [生产环境部署](#生产环境部署)
3. [云服务部署](#云服务部署)
4. [安全配置](#安全配置)

---

## 本地部署

### 方法 1: 静态 HTML 文件

最简单的方式，直接在浏览器中打开 HTML 文件。

```bash
# 克隆或下载模板文件
cd web-hook/templates

# 直接在浏览器中打开
# 或使用本地服务器
python -m http.server 8000

# 访问 http://localhost:8000/simple-chat.html
```

**注意**：此方法需要在前端配置 API Key，仅适用于测试。

### 方法 2: Python 后端服务

使用提供的后端代理服务。

```bash
# 安装依赖
pip install flask anthropic flask-cors

# 设置环境变量
export ANTHROPIC_API_KEY='sk-ant-api03-...'

# 运行服务
cd web-hook/scripts
python simple_server.py

# 访问 http://localhost:5000
```

### 方法 3: Node.js 服务器

```javascript
// server.js
const express = require('express');
const fetch = require('node-fetch');

const app = express();
app.use(express.json());
app.use(express.static('public'));

const API_KEY = process.env.ANTHROPIC_API_KEY;

app.post('/api/chat', async (req, res) => {
  const { prompt } = req.body;

  const response = await fetch('https://api.anthropic.com/v1/messages', {
    method: 'POST',
    headers: {
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01',
      'content-type': 'application/json'
    },
    body: JSON.stringify({
      model: 'claude-3-5-sonnet-20241022',
      max_tokens: 4096,
      messages: [{ role: 'user', content: prompt }]
    })
  });

  const data = await response.json();
  res.json({ response: data.content[0].text });
});

app.listen(3000);
```

```bash
# 安装依赖
npm install express node-fetch dotenv

# 创建 .env 文件
echo "ANTHROPIC_API_KEY=sk-ant-api03-..." > .env

# 运行
node server.js
```

---

## 生产环境部署

### 使用 Nginx + Python

**1. 安装依赖**

```bash
# Ubuntu/Debian
sudo apt update
sudo apt install nginx python3-pip python3-venv

# 创建虚拟环境
python3 -m venv /opt/claude-chat
source /opt/claude-chat/bin/activate
pip install gunicorn flask anthropic flask-cors
```

**2. 配置 Gunicorn**

```bash
# 创建启动脚本
cat > /opt/claude-chat/start.sh << 'EOF'
#!/bin/bash
cd /opt/claude-chat
source /opt/claude-chat/bin/activate
export ANTHROPIC_API_KEY='your-api-key'
gunicorn -w 4 -b 127.0.0.1:5000 simple_server:app
EOF

chmod +x /opt/claude-chat/start.sh
```

**3. 配置 Nginx**

```bash
sudo nano /etc/nginx/sites-available/claude-chat
```

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件缓存
    location /static {
        alias /opt/claude-chat/static;
        expires 30d;
    }
}
```

```bash
# 启用站点
sudo ln -s /etc/nginx/sites-available/claude-chat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx

# 使用 systemd 管理服务
sudo nano /etc/systemd/system/claude-chat.service
```

```ini
[Unit]
Description=Claude Chat Service
After=network.target

[Service]
Type=simple
User=www-data
WorkingDirectory=/opt/claude-chat
ExecStart=/opt/claude-chat/start.sh
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable claude-chat
sudo systemctl start claude-chat
```

### 使用 Docker

**1. 创建 Dockerfile**

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV ANTHROPIC_API_KEY=""

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "simple_server:app"]
```

**2. requirements.txt**

```
flask==3.0.0
anthropic==0.18.0
flask-cors==4.0.0
gunicorn==21.2.0
```

**3. docker-compose.yml**

```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    restart: unless-stopped
```

**4. 部署**

```bash
# 构建并运行
docker-compose up -d

# 查看日志
docker-compose logs -f

# 停止
docker-compose down
```

---

## 云服务部署

### Vercel (前端)

```bash
# 安装 Vercel CLI
npm i -g vercel

# 部署
cd templates
vercel

# 配置 vercel.json
{
  "version": 2,
  "builds": [
    {
      "src": "*.html",
      "use": "@vercel/static"
    }
  ]
}
```

### Railway (后端)

```bash
# 安装 Railway CLI
npm i -g @railway/cli

# 登录并部署
railway login
railway init
railway up

# 在 Railway 控制台设置环境变量
# ANTHROPIC_API_KEY=sk-ant-api03-...
```

### AWS (EC2 + Elastic Beanstalk)

**使用 Elastic Beanstalk:**

```bash
# 安装 EB CLI
pip install awsebcli

# 初始化
eb init -p python claude-chat

# 创建环境
eb create production

# 部署
eb deploy

# 设置环境变量
eb setenv ANTHROPIC_API_KEY=sk-ant-api03-...
```

### Google Cloud Run

```bash
# 构建并推送镜像
gcloud builds submit --tag gcr.io/PROJECT_ID/claude-chat

# 部署到 Cloud Run
gcloud run deploy claude-chat \
  --image gcr.io/PROJECT_ID/claude-chat \
  --platform managed \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars ANTHROPIC_API_KEY=sk-ant-api03-...
```

---

## 安全配置

### 1. API Key 管理

**❌ 不要**：
- 在前端代码中硬编码 API Key
- 将 API Key 提交到 Git 仓库
- 在客户端日志中打印 API Key

**✅ 应该**：
- 使用环境变量存储 API Key
- 使用后端代理 API 调用
- 使用密钥管理服务（如 AWS Secrets Manager）

### 2. CORS 配置

```python
from flask_cors import CORS

# 生产环境限制来源
CORS(app, resources={
    r"/api/*": {
        "origins": ["https://your-domain.com"]
    }
})
```

### 3. 速率限制

```python
from flask_limiter import Limiter

limiter = Limiter(
    app,
    key_func=lambda: request.headers.get('X-API-Key')
)

@app.route('/api/chat', methods=['POST'])
@limiter.limit("10 per minute")
def chat():
    # ...
```

### 4. 输入验证

```python
MAX_INPUT_LENGTH = 10000

@app.route('/api/chat', methods=['POST'])
def chat():
    data = request.json
    prompt = data.get('prompt', '')

    # 验证输入
    if not prompt or len(prompt) > MAX_INPUT_LENGTH:
        return jsonify({'error': 'Invalid input'}), 400

    # 过滤恶意内容
    if contains_malicious_content(prompt):
        return jsonify({'error': 'Content not allowed'}), 403
```

### 5. HTTPS 配置

使用 Let's Encrypt 免费证书：

```bash
# 安装 Certbot
sudo apt install certbot python3-certbot-nginx

# 获取证书
sudo certbot --nginx -d your-domain.com

# 自动续期
sudo certbot renew --dry-run
```

---

## 监控与日志

### 日志记录

```python
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),
        logging.StreamHandler()
    ]
)

@app.route('/api/chat', methods=['POST'])
def chat():
    logging.info(f'Chat request from {request.remote_addr}')
    # ...
```

### 性能监控

```python
import time

@app.before_request
def before_request():
    request.start_time = time.time()

@app.after_request
def after_request(response):
    duration = time.time() - request.start_time
    logging.info(f'Request took {duration:.2f}s')
    return response
```

---

## 故障排查

### 常见问题

**1. CORS 错误**

```
Access to fetch at 'https://api.anthropic.com' from origin 'http://localhost:3000'
has been blocked by CORS policy
```

解决：使用后端代理或添加 `dangerously-allow-browser: true`（仅开发环境）

**2. API Key 无效**

```
401 Unauthorized
```

解决：检查 API Key 是否正确，是否设置了环境变量

**3. 速率限制**

```
429 Too Many Requests
```

解决：实现请求队列和重试逻辑

---

## 成本估算

| 服务 | 免费额度 | 预计成本 |
|------|----------|----------|
| Railway | $5/月 | 付费计划 $5-20/月 |
| Vercel | 100GB 带宽 | $20/月起步 |
| AWS EC2 | 12个月免费 | t3.micro $8/月 |
| GCP Cloud Run | 200万请求/月 | 按使用量付费 |
| Claude API | - | Input: $3/百万token, Output: $15/百万token |

---

## 参考资源

- [Flask 部署文档](https://flask.palletsprojects.com/en/latest/deploying/)
- [Docker 部署指南](https://docs.docker.com/engine/deploy/)
- [Anthropic API 文档](https://docs.anthropic.com/)
