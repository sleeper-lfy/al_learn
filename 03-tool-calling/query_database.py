"""query_database.py：Agent 数据工具（SQLite）。

设计原则（Agent 工具视角）：
- 工具是“面向模型”的函数：业务查询封装成高层函数，模型不需要知道 SQL；
- 所有 SQL 使用参数化占位符，参数来自模型，必须杜绝注入；
- 统一返回 JSON 字符串（ensure_ascii=False），模型可以直接读；
- 结果附带 detail 说明字段含义，降低模型理解成本。
"""

import json
import logging
import sqlite3

logger = logging.getLogger(__name__)

ORDER_STATUS = ("已完成", "已取消", "进行中")
DB_PATH = "db/agent_data.db"  # 从 03-tool-calling 目录运行时相对当前目录


class AgentDataTool:
    """为 Agent 设计的 SQLite 数据工具，内置一套模拟订单数据。"""

    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._init_demo_data()

    def _init_demo_data(self) -> None:
        """建表 + 空表时灌入模拟数据 + 兼容历史脏数据。"""
        cursor = self.conn.cursor()
        cursor.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY,
                name TEXT,
                role TEXT,
                signup_date TEXT
            );
            CREATE TABLE IF NOT EXISTS orders (
                id INTEGER PRIMARY KEY,
                user_id INTEGER,
                product TEXT,
                amount REAL,
                status TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            """
        )

        if cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0] == 0:
            cursor.executemany(
                "INSERT INTO users VALUES (?, ?, ?, ?)",
                [
                    (1, "张三", "管理员", "2023-01-15"),
                    (2, "李四", "普通用户", "2023-02-20"),
                    (3, "王五", "VIP用户", "2023-03-10"),
                ],
            )
            cursor.executemany(
                "INSERT INTO orders VALUES (?, ?, ?, ?, ?)",
                [
                    (101, 1, "MacBook Pro", 12999.0, "已完成"),
                    (102, 2, "iPhone 15", 7999.0, "进行中"),
                    (103, 3, "AirPods", 1899.0, "已完成"),
                    (104, 1, "iPad Air", 4799.0, "已取消"),
                ],
            )

        # 兼容旧版本模拟数据：把枚举外的状态统一成“进行中”，保持规则与数据一致
        cursor.execute(
            "UPDATE orders SET status = ? WHERE status NOT IN (?, ?, ?)",
            ("进行中",) + ORDER_STATUS,
        )
        self.conn.commit()

    def query_to_json(self, sql: str, params: tuple | None = None) -> str:
        """执行参数化 SQL，返回 JSON 字符串；出错也返回 JSON，不抛异常。"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(sql, params or ())
            rows = [dict(row) for row in cursor.fetchall()]
            return json.dumps(rows, ensure_ascii=False)
        except sqlite3.Error as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    def get_user(self, user_name: str | None = None, user_role: str | None = None) -> str:
        """按用户名/角色查用户，两个条件可组合，都为空时返回全表。"""
        sql = "SELECT id, name, role, signup_date FROM users WHERE 1=1"
        params: list = []
        if user_name:
            sql += " AND name = ?"
            params.append(user_name)
        if user_role:
            sql += " AND role = ?"
            params.append(user_role)
        data = self.query_to_json(sql, tuple(params))
        detail = "id：用户编号，name：用户名称，role：用户角色，signup_date：注册时间"
        return json.dumps({"data": json.loads(data), "detail": detail}, ensure_ascii=False)

    def get_order(
        self,
        status: str | None = None,
        min_amount: float | None = None,
        max_amount: float | None = None,
        product: str | None = None,
        user_id: int | None = None,
    ) -> str:
        """按状态/金额区间/商品/用户ID查订单，条件可任意组合。"""
        sql = "SELECT id, user_id, product, amount, status FROM orders WHERE 1=1"
        params: list = []
        if status:
            sql += " AND status = ?"
            params.append(status)
        if min_amount is not None:
            sql += " AND amount >= ?"
            params.append(min_amount)
        if max_amount is not None:
            sql += " AND amount <= ?"
            params.append(max_amount)
        if product:
            sql += " AND product = ?"
            params.append(product)
        if user_id is not None:
            sql += " AND user_id = ?"
            params.append(user_id)
        data = self.query_to_json(sql, tuple(params))
        detail = "id：订单号，user_id：下单用户编号，product：商品名称，amount：金额，status：状态"
        return json.dumps({"data": json.loads(data), "detail": detail}, ensure_ascii=False)

    def get_user_orders(self, user_name: str) -> str:
        """按用户名查订单（业务级封装示例：一次 JOIN 完成）。"""
        sql = """
            SELECT u.name, o.product, o.amount, o.status
            FROM orders o JOIN users u ON o.user_id = u.id
            WHERE u.name = ?
        """
        return self.query_to_json(sql, (user_name,))

    def close(self) -> None:
        self.conn.close()


if __name__ == "__main__":
    tool = AgentDataTool()
    print(">>> 查询 VIP 用户：")
    print(tool.get_user(user_role="VIP用户"))
    print("\n>>> 查询张三的订单：")
    print(tool.get_user_orders("张三"))
    tool.close()
