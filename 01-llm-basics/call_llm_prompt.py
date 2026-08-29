"""call_llm_prompt.py：角色消息 + Temperature。

对应学习点：System / User / Assistant 角色、Prompt、Temperature。

- /api/chat 用 messages 数组表达角色；/api/generate 只有一段文本，没有角色概念
- system：定义行为/规则/约束；user：任务输入；assistant：模型回答
- temperature 越低越稳定，越高越发散
"""

import requests

URL = "http://localhost:11434/api/chat"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 120


def chat(messages, temperature):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "options": {"temperature": temperature},
    }
    response = requests.post(URL, json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()["message"]["content"]


messages = [
    {"role": "system", "content": "你是 Python 专家。回答不超过 3 句话，用中文。"},
    {"role": "user", "content": "什么是装饰器？"},
]

print("=== temperature=0（低随机性，结果稳定）===")
print(chat(messages, 0))

print("\n=== temperature=1.2（高随机性，结果发散）===")
print(chat(messages, 1.2))

# 多轮对话的写法：把 assistant 回答追加回 messages，历史对话就变成了上下文
# messages.append({"role": "assistant", "content": 上一次的回答})
# messages.append({"role": "user", "content": "那它和闭包有什么关系？"})
