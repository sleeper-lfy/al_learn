"""safe_calculator.py：安全的数学表达式计算工具。

不用 eval()，而是把表达式解析成 AST，只允许白名单内的运算符节点，
从根本上杜绝任意代码执行——这是 Agent 工具实现里的安全底线。
"""

import ast
import operator


class SafeCalculator:
    """用 AST 白名单方式计算数学表达式，禁止执行任意 Python 代码。"""

    ALLOWED_OPS = {
        ast.Add: operator.add,
        ast.Sub: operator.sub,
        ast.Mult: operator.mul,
        ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv,
        ast.Mod: operator.mod,
        ast.Pow: operator.pow,
        ast.USub: operator.neg,  # 负号
        ast.UAdd: operator.pos,  # 正号
    }

    def calculate(self, expression: str) -> str:
        """计算表达式；出错时返回错误文本（错误对模型也是有用的观察）。"""
        try:
            tree = ast.parse(expression, mode="eval")
            value = self._eval_node(tree.body)
            return str(value)
        except (ValueError, SyntaxError, ZeroDivisionError) as exc:
            return f"计算错误：{exc}"

    def _eval_node(self, node):
        """递归求值 AST 节点，只认白名单里的运算类型。"""
        if isinstance(node, ast.Constant):
            if not isinstance(node.value, (int, float)):
                raise ValueError(f"不支持的常量类型: {type(node.value).__name__}")
            return node.value
        if isinstance(node, ast.BinOp):
            left = self._eval_node(node.left)
            right = self._eval_node(node.right)
            op_func = self.ALLOWED_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
            return op_func(left, right)
        if isinstance(node, ast.UnaryOp):
            operand = self._eval_node(node.operand)
            op_func = self.ALLOWED_OPS.get(type(node.op))
            if op_func is None:
                raise ValueError(f"不支持的运算符: {type(node.op).__name__}")
            return op_func(operand)
        raise ValueError(f"不支持的表达式节点: {type(node).__name__}")
