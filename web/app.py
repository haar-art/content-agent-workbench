from flask import Flask, render_template, request
import sys
from pathlib import Path
from dotenv import load_dotenv

# 让 Python 能找到上一级目录里的 agent 模块
sys.path.append(str(Path(__file__).resolve().parents[1]))
# 明确告诉它密钥文件在哪（agent_content_v2 的上一级有 .env）
load_dotenv(Path(__file__).resolve().parents[2] / '.env')

from agent_content_v2 import run_topic

app = Flask(__name__)


@app.route('/')
def home():
    return render_template('index.html')


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
