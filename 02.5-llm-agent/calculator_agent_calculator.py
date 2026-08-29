"""calculator_agent_calculator.py：让 LLM 当 Agent（文本 JSON 约定范式）。

与 02-agent-runtime 对照学习：
- 这里不用原生 tool_calls，而是用 format 强制模型输出
  {"action": "...", "input": "..."}，程序用 switch 分发执行；
- 优点：任何模型都能用（只要会输出 JSON）；
- 缺点：解析脆、action 文本会混进对话上下文、没有 tool_call_id 关联。

完整的安全计算器实现见 02-agent-runtime/safe_calculator.py，
这里只保留核心的 AST 白名单逻辑，保持本目录自包含。
"""

import argparse
import ast
import json
import operator
import sys

import requests

OLLAMA_URL = "http://localhost:11434/api/chat"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 120

# 模型能选择的“行动”白名单，防止模型输出未知 action 时程序崩溃或静默失败
ACTIONS = {"calculator"}

# 用 JSON Schema 约束模型输出：action + input 两个字段
ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string"},
        "input": {"type": "string"},
    },
    "required": ["action", "input"],
}

SYSTEM_PROMPT = """你是一个 Agent。根据用户需求选择 Action，只能输出以下 action：
- calculator：数学计算，input 必须是完整可计算的表达式（如 "123+456"），严禁夹带文字。
参数缺失时不要编造，向用户询问。"""

ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,  # 负号
    ast.UAdd: operator.pos,  # 正号
}


def safe_calc(expression: str) -> str:
    """AST 白名单求值：拒绝 Call/Attribute 等任意代码执行节点。"""
    try:
        tree = ast.parse(expression, mode="eval")
        return str(_eval_node(tree.body))
    except (ValueError, SyntaxError, ZeroDivisionError) as exc:
        return f"计算错误：{exc}"


def _eval_node(node):
    if isinstance(node, ast.Constant):
        if not isinstance(node.value, (int, float)):
            raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
        return node.value
    if isinstance(node, ast.BinOp):
        left = _eval_node(node.left)
        right = _eval_node(node.right)
        op = ALLOWED_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        return op(left, right)
    if isinstance(node, ast.UnaryOp):
        op = ALLOWED_OPS.get(type(node.op))
        if op is None:
            raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
        return op(_eval_node(node.operand))
    raise ValueError(f"不支持的表达式节点: {type(node).__name__}")


def dispatch(action, input_text):
    """文本约定的分发器：白名单校验 + 缺参兜底 + 执行。"""
    if action not in ACTIONS:
        return f"未知 action：{action}，我只能执行 {sorted(ACTIONS)}"
    if action == "calculator":
        if not input_text or not input_text.strip():
            return "缺少 input，请提供要计算的数学表达式"
        return safe_calc(input_text)
    return "未实现"


def main(argv=None):
    parser = argparse.ArgumentParser(description="让 LLM 当 Agent（文本 JSON 约定）")
    parser.add_argument("question", help="问 Agent 的问题")
    args = parser.parse_args(argv)

    payload = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": args.question},
        ],
        "stream": False,
        "format": ACTION_SCHEMA,
    }

    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
        response.raise_for_status()
        content = response.json()["message"]["content"]
    except requests.RequestException as exc:
        print(f"请求失败：{exc}")
        return 1

    # 解析层：format 约束也可能偶尔失效，必须兜底
    try:
        decision = json.loads(content)
    except json.JSONDecodeError as exc:
        print(f"模型输出不是合法 JSON（需要重试或加强提示词）：\n{content}")
        return 1

    action = decision.get("action", "")
    input_text = decision.get("input", "")
    print(f"模型决策：action={action!r}, input={input_text!r}")
    print("执行结果：", dispatch(action, input_text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
