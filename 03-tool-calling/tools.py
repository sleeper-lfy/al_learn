"""tools.py：工具注册表。

一个工具 = 三件事：
1. schema：给模型的接口文档（TOOLS 列表）；
2. 校验：参数缺失/非法 -> 错误文本；
3. 执行：调用底层实现，返回字符串。

Agent 只依赖这里的两个入口：
- TOOLS：问“有哪些工具、参数长什么样”；
- execute_tool：执行工具，统一返回字符串（成功结果或错误文本，不抛异常）。

新增工具时只需要在 TOOLS 加一个 schema、在 execute_tool 加一个分支，
Agent 循环和底层实现都不需要改。
"""

from query_database import ORDER_STATUS, AgentDataTool
from safe_calculator import SafeCalculator

# 工具清单（给模型的接口文档）：name / description / parameters
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
            "name": "select_user",
            "description": "按用户名或角色查询用户（角色取值：管理员、普通用户、VIP用户）",
            "parameters": {
                "type": "object",
                "required": [],
                "properties": {
                    "user_name": {"type": "string", "description": "用户名称"},
                    "user_role": {"type": "string", "description": "用户角色"},
                },
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "select_order",
            "description": "按状态/金额区间/商品/用户ID查询订单，条件可组合",
            "parameters": {
                "type": "object",
                "required": [],
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "订单状态，只能是：已完成、已取消、进行中",
                    },
                    "min_amount": {
                        "type": "number",
                        "description": "最小金额（含），用户说“大于XX”时填",
                    },
                    "max_amount": {
                        "type": "number",
                        "description": "最大金额（含），用户说“小于XX”时填",
                    },
                    "product": {"type": "string", "description": "商品名称"},
                    "user_id": {"type": "integer", "description": "用户ID"},
                },
            },
        },
    },
]

_data_tool: AgentDataTool | None = None


def _get_data_tool() -> AgentDataTool:
    """惰性单例：SQLite 连接只建一次，多轮循环里复用。"""
    global _data_tool
    if _data_tool is None:
        _data_tool = AgentDataTool()
    return _data_tool


def execute_tool(name: str, arguments: dict) -> str:
    """执行工具：成功返回结果文本，参数问题返回错误文本，不抛异常。"""
    if name == "calculator":
        expr = arguments.get("content", "").strip()
        if not expr:
            return "缺少参数 content，请提供要计算的数学表达式"
        return SafeCalculator().calculate(expr)

    if name == "select_user":
        user_name = arguments.get("user_name", "").strip()
        user_role = arguments.get("user_role", "").strip()
        if not user_name and not user_role:
            return "缺少参数：user_name 或 user_role 至少提供一个"
        return _get_data_tool().get_user(user_name or None, user_role or None)

    if name == "select_order":
        status = arguments.get("status", "").strip()
        product = arguments.get("product", "").strip()
        min_amount = arguments.get("min_amount")
        max_amount = arguments.get("max_amount")
        user_id = arguments.get("user_id")
        has_condition = any(
            [status, product, min_amount is not None, max_amount is not None, user_id is not None]
        )
        if not has_condition:
            return "缺少参数：status / max_amount / min_amount / product / user_id 至少提供一个"
        if status and status not in ORDER_STATUS:
            return f"无效的订单状态：{status}，只能是 {'/'.join(ORDER_STATUS)}"
        return _get_data_tool().get_order(
            status=status or None,
            min_amount=min_amount,
            max_amount=max_amount,
            product=product or None,
            user_id=user_id,
        )

    return f"未知工具：{name}"
