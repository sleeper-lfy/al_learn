"""agent.py：Agent 运行时（工具调用循环）。

职责：只做循环，不关心具体工具——
1. 向模型提供工具清单（TOOLS）和系统规则；
2. 模型返回 tool_calls 后交给 execute_tool 执行；
3. 结果作为 tool 消息回填上下文，直到模型直接回答或达到步数上限。

新增工具只需要改 tools.py，本文件一行都不用动。
"""

import argparse
import json
import sys

import requests

from tools import TOOLS, execute_tool

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 120
MAX_STEPS = 8  # 循环上限，防止模型无限调用工具

SYSTEM_PROMPT = """你是一个商城订单 Agent。根据用户需求选择合适的工具。
规则：
1. 数字计算必须调用 calculator，content 必须是完整可计算的数学表达式（如 "123+456"），严禁夹带文字。
2. 查询用户调用 select_user，user_name 或 user_role 至少有一个有值。
3. 查询订单调用 select_order，status / max_amount / min_amount / product / user_id 至少有一个有值。
   status 只能是：已完成、已取消、进行中 之一，且必须是用户明确提到的。
4. 工具参数缺失时不要编造，先向用户询问。
5. 用户提到人名但没给用户ID时，可以先 select_user 查出 id，再用它查订单。
6. 工具结果返回后，基于结果给出最终回答。"""


def call_llm(messages):
    """调 /api/chat，返回完整响应。"""
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
    parser = argparse.ArgumentParser(description="商城订单 Agent：工具工程化")
    parser.add_argument("question", help="问 Agent 的问题")
    args = parser.parse_args(argv)
    try:
        run_agent(args.question)
    except requests.RequestException as exc:
        print(f"请求失败：{exc}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
