"""call_llm.py：基础调用 + Token 统计。

对应学习点：Token、Context Window。

- /api/generate 是最朴素的“文本进、文本出”接口
- 响应里的 prompt_eval_count / eval_count 是 Token 的直观证据
- options.num_ctx 控制上下文窗口：模型一次最多能“看到”多少 token
"""

import requests

URL = "http://localhost:11434/api/generate"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 120

payload = {
    "model": MODEL,
    "prompt": "用三句话介绍 Python 的 GIL。",
    "stream": False,
    "options": {
        "num_ctx": 4096,  # 上下文窗口（token 数），超出会被截断
    },
}

response = requests.post(URL, json=payload, timeout=TIMEOUT)
response.raise_for_status()
data = response.json()

print("=== 回答 ===")
print(data["response"])

print("\n=== Token 统计（来自响应元数据）===")
prompt_tokens = data["prompt_eval_count"]
output_tokens = data["eval_count"]
eval_seconds = data["eval_duration"] / 1e9
print(f"输入(prompt) tokens : {prompt_tokens}")
print(f"输出(生成)  tokens : {output_tokens}")
print(f"生成速度           : {output_tokens / eval_seconds:.1f} tok/s")
