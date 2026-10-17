from flask import Flask, render_template, request
import sys
import os
import json
import re
import urllib.request
from pathlib import Path
from dotenv import load_dotenv
from openai import OpenAI

# ① 先加载 .env（必须在创建 client 之前）
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

# ② 创建 client 与常量
client = OpenAI(
    base_url=os.getenv('OPENAI_BASE_URL'),
    api_key=os.getenv('OPENAI_API_KEY'),
)
MODEL = os.getenv('OPENAI_MODEL', 'deepseek-chat')
AIHOT_UA = 'aihot-skill/2.0.0 (+https://aihot.news/aihot-skill/)'
PERSONA = '面向零基础观众的「学 AI / 亲手做东西」博主；化工转 AI 的大学生；人设是翻车但真实的陪练，不说教、有态度、信息密度高。'

# ③ 让 Python 能找到 agent 模块
sys.path.append(str(Path(__file__).resolve().parents[1]))
from agent_content_v2 import run_topic

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


@app.route('/history')
def history():
    out_dir = Path(__file__).resolve().parents[1] / 'output'
    files = sorted(out_dir.glob('*.json'), reverse=True)[:5]
    items = []
    for f in files:
        try:
            data = json.loads(f.read_text(encoding='utf-8'))
            topic = data.get('topic', '')
            if not topic:
                continue
            items.append({'topic': topic, 'time': f.stem})
        except Exception:
            continue
    return items


@app.route('/hot')
def hot():
    source = request.args.get('source', 'aihot')

    if source == 'news':
        news_dir = Path(r"C:\Users\haar\Documents\ChatGPT\knowledge base\00_灵感库")
        files = sorted(news_dir.glob('*-AI新闻个人影响.md'), reverse=True)[:5]
        items = []
        for f in files:
            try:
                text = f.read_text(encoding='utf-8')
                m = re.search(r'^title:\s*(.+)$', text, re.M)
                if not m:
                    continue
                inner = re.search(r'（(.+)）', m.group(1))
                if not inner:
                    continue
                for t in inner.group(1).split(' / '):
                    t = t.strip()
                    if t:
                        items.append({'topic': t, 'date': f.name[:10]})
            except Exception:
                continue
        return items

    if source == 'smart':
        candidates = []

        try:
            url = 'https://aihot.news/api/v1/agent/latest?window=7d&limit=30'
            req = urllib.request.Request(url, headers={'User-Agent': AIHOT_UA})
            with urllib.request.urlopen(req, timeout=20) as resp:
                text = resp.read().decode('utf-8')
            for t in re.findall(r'$$(.+?)$$\(https://aihot\.news/items/', text):
                candidates.append('【AI行业】' + t)
        except Exception:
            pass

        try:
            news_dir = Path(r"C:\Users\haar\Documents\ChatGPT\knowledge base\00_灵感库")
            for f in sorted(news_dir.glob('*-AI新闻个人影响.md'), reverse=True)[:3]:
                text = f.read_text(encoding='utf-8')
                m = re.search(r'^title:\s*(.+)$', text, re.M)
                if not m:
                    continue
                inner = re.search(r'（(.+)）', m.group(1))
                if inner:
                    for t in inner.group(1).split(' / '):
                        if t.strip():
                            candidates.append('【新闻】' + t.strip())
        except Exception:
            pass

        if not candidates:
            return []

        prompt = (
            f'账号定位：{PERSONA}\n\n'
            '以下是候选素材：\n' +
            '\n'.join(f'{i+1}. {c}' for i, c in enumerate(candidates[:40])) +
            '\n\n任务：从中挑出 5 条最适合这个账号拍摄的选题。'
            '每条给出：topic（口语化选题，能直接当视频主题）、reason（为什么适合这个账号，一句话）、angle（建议的切入角度，一句话）。'
            '只输出 JSON 数组，不要任何其他文字：'
            '[{"topic":"...","reason":"...","angle":"..."}]'
        )

        resp = client.chat.completions.create(
            model=MODEL,
            messages=[{'role': 'user', 'content': prompt}],
            temperature=0.7,
        )
        text = resp.choices[0].message.content.strip().strip('`').removeprefix('json').strip()
        try:
            return json.loads(text)
        except Exception:
            return [{'topic': text[:200], 'reason': '(解析失败，原样返回)', 'angle': ''}]

    url = 'https://aihot.news/api/v1/agent/hot'
    req = urllib.request.Request(url, headers={'User-Agent': AIHOT_UA})
    with urllib.request.urlopen(req, timeout=20) as resp:
        text = resp.read().decode('utf-8')
    titles = re.findall(r'$$(.+?)$$\(https://aihot\.news/items/', text)
    return [{'topic': t, 'date': 'AI热点'} for t in titles]


@app.route('/generate', methods=['POST'])
def generate():
    data = request.get_json()
    topic = data.get('topic', '')
    result = run_topic(topic)
    return {
        'title': result['title'],
        'hook': result['hook'],
        'script': result['script'],
        'image_prompts': result['image_prompts'],
        'hashtags': result['hashtags'],
    }


if __name__ == '__main__':
    app.run(debug=True)
