"""agent.py：影视检索 Agent（运行层）。

与 03-tool-calling/agent.py 同构：循环 + 消息回填 + 终止控制。
区别只在系统提示词和工具清单，Agent 本身不关心检索是怎么实现的。
"""

import argparse
import json
import pathlib
import sys

# 确保 04-rag 根目录在 sys.path，支持 `python agent/agent.py` 直接运行
PROJECT_ROOT = str(pathlib.Path(__file__).resolve().parents[1])
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import requests

from tools import TOOLS, execute_tool

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 180
MAX_STEPS = 8

SYSTEM_PROMPT = """你是一个影视检索 Agent，负责理解用户需求并决定是否使用影视检索工具。

决策规则：
1. 用户问题涉及影视信息（电影、电视剧、演员、导演、类型、标签、剧情等）时，
   必须调用 search_movies，content 填用户真正想查询的自然语言条件。
2. 只是闲聊、问候、或与影视知识库无关时，直接回答，不要调用工具。
3. 查询条件模糊但可以检索时，优先调用工具做模糊检索，不要反复询问用户。
4. 不要自行添加用户没有提供的条件，不要猜测片名/演员/导演/年份等。
5. 检索是 search_movies 工具内部的事，不要在回答里解释检索过程。

最终回答：
- 调用工具后，根据工具返回结果回答，不要编造工具没有返回的信息；
- 未调用工具时，正常回答用户。"""


def call_llm(messages):
    payload = {
        "model": MODEL,
        "messages": messages,
        "stream": False,
        "tools": TOOLS,
    }
    response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    response.raise_for_status()
    return response.json()


def run_agent(user_input):
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]

    for step in range(1, MAX_STEPS + 1):
        result = call_llm(messages)
        message = result["message"]
        messages.append(message)  # assistant 消息（含 tool_calls）必须完整回填

        tool_calls = message.get("tool_calls")
        if not tool_calls:
            print(f"[第 {step} 步] 模型直接回答：")
            print(message["content"])
            return

        print(f"[第 {step} 步] 模型请求 {len(tool_calls)} 个工具调用")
        for tool_call in tool_calls:
            fn = tool_call["function"]
            raw = fn["arguments"]
            # 兼容两种返回：dict（新版 Ollama）或 JSON 字符串（部分版本/端点）
            arguments = raw if isinstance(raw, dict) else json.loads(raw)
            print(f"  -> {fn['name']}({arguments})")
            result_text = execute_tool(fn["name"], arguments)
            messages.append(
                {"role": "tool", "content": result_text, "tool_call_id": tool_call["id"]}
            )

    print(f"[超限] 达到 {MAX_STEPS} 步仍未结束，强制停止。")


def main(argv=None):
    parser = argparse.ArgumentParser(description="影视检索 Agent（RAG）")
    parser.add_argument("question", help="问 Agent 的问题")
    args = parser.parse_args(argv)
    try:
        run_agent(args.question)
    except requests.RequestException as exc:
        print(f"请求失败：{exc}")
        return 1
    return 0



