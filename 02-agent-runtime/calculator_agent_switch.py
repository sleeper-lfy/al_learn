"""calculator_agent_switch.py：Agent 基础——工具调用循环。

核心循环（ReAct 骨架）：
    用户输入 -> LLM 决定工具调用 -> 程序执行工具
    -> 工具结果作为 tool 消息回填上下文 -> LLM 继续
    -> LLM 不再调用工具，直接回答 -> 结束

两个工具：
- calculator：真实计算（SafeCalculator，AST 白名单求值）
- weather：模拟工具，返回固定值

关键机制：
1. tools 数组 = 告诉模型“有什么工具、参数长什么样”
2. 原生 function calling：模型返回 message.tool_calls
3. tool 消息用 tool_call_id 回填，模型才能把结果关联到这次调用
"""

import argparse
import json
import sys

import requests

from safe_calculator import SafeCalculator

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 120
MAX_STEPS = 8  # 循环上限，防止模型无限调用工具

SYSTEM_PROMPT = """你是一个 Agent，负责根据用户需求选择并调用工具。
规则：
1. 数字计算必须调用 calculator，content 必须是完整可计算的数学表达式（如 "123+456"），严禁夹带文字。
2. 查询天气调用 weather，content 必须是用户明确提供的城市名；没有提供城市时禁止猜测，先向用户询问。
3. 工具参数缺失时不要编造，向用户询问缺失信息。
4. 工具结果返回后，基于结果给出最终回答。"""

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": "计算数学表达式",
            "parameters": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {"type": "string", "description": "完整可计算的数学表达式"}
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "weather",
            "description": "查询天气",
            "parameters": {
                "type": "object",
                "required": ["content"],
                "properties": {
                    "content": {"type": "string", "description": "用户明确提供的城市名"}
                },
            },
        },
    },
]


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


def dispatch(tool_name, arguments):
    """工具分发：根据名字执行对应工具，返回字符串结果。

    参数缺失不抛异常，而是返回错误文本——错误对模型也是观察，
    模型会据此向用户询问缺失信息，形成纠错闭环。
    """
    if tool_name == "calculator":
        expr = arguments.get("content", "").strip()
        if not expr:
            return "缺少参数 content，请提供要计算的数学表达式"
        return SafeCalculator().calculate(expr)
    if tool_name == "weather":
        city = arguments.get("content", "").strip()
        if not city:
            return "缺少城市名称，用户未提供城市时请先询问，不要猜测"
        return f"{city}：晴，26℃"
    return f"未知工具：{tool_name}"


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
            result_text = dispatch(fn["name"], arguments)
            messages.append(
                {"role": "tool", "content": result_text, "tool_call_id": tool_call["id"]}
            )

    print(f"[超限] 达到 {MAX_STEPS} 步仍未结束，强制停止。")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Agent 基础：工具调用循环")
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
