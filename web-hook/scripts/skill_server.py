#!/usr/bin/env python3
"""
Skill Manager Server
提供 skill 创建和使用的后端服务
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Optional
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# 配置
SKILLS_BASE_DIR = Path(os.path.expanduser('~/.claude/skills'))
STATIC_DIR = Path(__file__).parent.parent / 'templates'

def get_all_skills() -> List[Dict]:
    """获取所有 skills 列表"""
    skills = []

    for skill_dir in SKILLS_BASE_DIR.iterdir():
        if not skill_dir.is_dir() or skill_dir.name.startswith('.'):
            continue

        skill_md = skill_dir / 'SKILL.md'
        if skill_md.exists():
            # 读取 SKILL.md 获取描述
            content = skill_md.read_text(encoding='utf-8')
            description = extract_description(content)

            skills.append({
                'name': skill_dir.name,
                'description': description,
                'path': str(skill_dir)
            })

    return skills

def extract_description(skill_md_content: str) -> str:
    """从 SKILL.md 提取描述"""
    # 查找第一段描述
    lines = skill_md_content.split('\n')
    description_lines = []

    for line in lines[2:10]:  # 跳过标题，取前几行
        line = line.strip()
        if line and not line.startswith('#') and not line.startswith('|'):
            description_lines.append(line)
        if description_lines and len(description_lines) > 2:
            break

    return ' '.join(description_lines)[:150] if description_lines else '暂无描述'

def get_skill_content(skill_name: str) -> Optional[Dict]:
    """获取 skill 完整内容"""
    skill_dir = SKILLS_BASE_DIR / skill_name
    if not skill_dir.exists():
        return None

    skill_md = skill_dir / 'SKILL.md'
    if not skill_md.exists():
        return None

    return {
        'name': skill_name,
        'content': skill_md.read_text(encoding='utf-8'),
        'path': str(skill_dir)
    }

def call_claude_api(message: str, config: Dict, skill_context: Optional[str] = None) -> str:
    """调用 Claude API"""
    import requests

    headers = {
        'x-api-key': config['authToken'],
        'anthropic-version': '2023-06-01',
        'content-type': 'application/json',
        'dangerously-allow-browser': 'true'
    }

    # 构建系统提示
    if skill_context:
        system_prompt = f"""You are a skill management assistant. The user is working with the following skill:

{skill_context}

Help the user use this skill effectively. Do NOT suggest modifying the skill content - skills are read-only.
"""
    else:
        system_prompt = """You are a skill creation assistant. Help users create new skills by:
1. Understanding their requirements
2. Suggesting appropriate skill structure
3. Generating SKILL.md content
4. Providing any additional files needed

IMPORTANT: You can only CREATE new skills, never MODIFY existing ones."""

    messages = [{
        'role': 'user',
        'content': message
    }]

    body = {
        'model': config.get('model', 'claude-3-5-sonnet-20241022'),
        'max_tokens': 4096,
        'system': system_prompt,
        'messages': messages
    }

    url = f"{config['baseUrl'].rstrip('/')}/v1/messages"
    response = requests.post(url, headers=headers, json=body, timeout=30)
    response.raise_for_status()

    data = response.json()
    return data['content'][0]['text']

def create_skill_from_description(name: str, description: str, config: Dict) -> Dict:
    """根据描述创建新 skill"""
    # 验证 skill 名称
    if not re.match(r'^[a-z0-9-]+$', name):
        return {'success': False, 'error': 'Skill 名称只能包含小写字母、数字和连字符'}

    # 检查是否已存在
    skill_dir = SKILLS_BASE_DIR / name
    if skill_dir.exists():
        return {'success': False, 'error': 'Skill 已存在'}

    try:
        # 调用 Claude 生成 skill 内容
        prompt = f"""Create a new skill called "{name}" with this description:
{description}

Generate the SKILL.md file content following this format:
---
# Skill Name

A brief one-line description of what this skill does.

## Description
Detailed description of the skill's purpose and functionality.

## Use Cases
When to use this skill (triggers).

## Features
Key features and capabilities.

## Files
List of files in this skill (if any).
---

Only output the SKILL.md content, nothing else.
"""

        response = call_claude_api(prompt, config)

        # 创建 skill 目录
        skill_dir.mkdir(parents=True, exist_ok=True)

        # 写入 SKILL.md
        skill_md = skill_dir / 'SKILL.md'
        skill_md.write_text(response, encoding='utf-8')

        return {
            'success': True,
            'skill': {
                'name': name,
                'description': description,
                'path': str(skill_dir)
            }
        }
    except Exception as e:
        return {'success': False, 'error': str(e)}

@app.route('/')
def index():
    """主页"""
    return send_from_directory(STATIC_DIR, 'skill-manager.html')

@app.route('/api/skills', methods=['GET'])
def list_skills():
    """获取所有 skills"""
    try:
        skills = get_all_skills()
        return jsonify(skills)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/skills/<skill_name>', methods=['GET'])
def get_skill(skill_name: str):
    """获取 skill 详情"""
    try:
        skill = get_skill_content(skill_name)
        if not skill:
            return jsonify({'error': 'Skill not found'}), 404
        return jsonify(skill)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/chat', methods=['POST'])
def chat():
    """处理聊天请求"""
    try:
        data = request.json
        message = data.get('message', '')
        skill = data.get('skill')
        config = data.get('config', {})
        intent = data.get('intent', 'chat')

        if not message:
            return jsonify({'error': 'Message is required'}), 400

        if not config.get('authToken'):
            return jsonify({'error': 'API config is required'}), 400

        # 如果是使用 skill
        if skill and intent == 'use_skill':
            skill_content = get_skill_content(skill)
            if not skill_content:
                return jsonify({'error': 'Skill not found'}), 404

            skill_context = f"Skill: {skill}\n\n{skill_content['content'][:2000]}"
            response = call_claude_api(message, config, skill_context)

            return jsonify({
                'response': response,
                'action': 'skill_used',
                'skill': skill
            })

        # 如果是创建 skill
        elif intent == 'create_skill':
            # 尝试从消息中提取 skill 名称和描述
            skill_name, skill_desc = extract_skill_info(message)

            if skill_name:
                result = create_skill_from_description(skill_name, skill_desc, config)
                if result['success']:
                    return jsonify({
                        'response': f"✅ Skill '{skill_name}' 创建成功！\n\n{result['skill']['description']}",
                        'action': 'skill_created',
                        'skill': result['skill']
                    })
                else:
                    return jsonify({
                        'response': f"❌ 创建失败: {result['error']}",
                        'action': 'error'
                    })
            else:
                # 让 Claude 帮助明确需求
                response = call_claude_api(
                    f"User wants to create a skill. Their message: {message}\n\n"
                    "Ask clarifying questions to understand what skill they want to create. "
                    "Specifically ask for: 1) Skill name, 2) What it should do.",
                    config
                )
                return jsonify({'response': response, 'action': 'clarify'})

        # 普通对话
        else:
            response = call_claude_api(message, config)
            return jsonify({'response': response, 'action': 'chat'})

    except Exception as e:
        return jsonify({'error': str(e)}), 500

def extract_skill_info(message: str) -> tuple[Optional[str], str]:
    """从消息中提取 skill 信息"""
    # 简单的模式匹配
    patterns = [
        r'创建[一个]?\s*skill\s*[叫名为]?\s*["\']?([a-z0-9-]+)["\']?',
        r'create\s+a?\s*skill\s*(?:called\s+|named\s+)?["\']?([a-z0-9-]+)["\']?',
    ]

    for pattern in patterns:
        match = re.search(pattern, message, re.IGNORECASE)
        if match:
            return match.group(1), message

    return None, message

if __name__ == '__main__':
    print(f"🚀 Skill Manager Server")
    print(f"📁 Skills directory: {SKILLS_BASE_DIR}")
    print(f"🌐 Server running at: http://localhost:5000")
    print()

    app.run(host='0.0.0.0', port=5000, debug=True)