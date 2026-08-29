# 03-tool-calling · 自学笔记

> 2026-08-27 ｜ 工具工程化：真实数据库工具 跑通 ✅

## 目标

02-agent-runtime 里的 weather 工具返回固定值（“天气晴”），那是假的。
本章把工具升级成**真实 SQLite 查询**，核心问题变成：
**一个 Agent 能用的工具，到底要设计到什么程度？**

## 组织

```text
03-tool-calling/
├── safe_calculator.py   # 实现层：纯计算工具（AST 白名单）
├── query_database.py    # 实现层：纯数据工具（SQLite，统一返回 JSON）
├── tools.py             # 注册层：工具 schema + 参数校验 + 执行
├── agent.py             # 运行层：LLM 调用 + 循环 + CLI（只依赖 tools）
└── agent_data.db        # SQLite 模拟数据（用户/订单表）
```

依赖方向是单向的：

```text
agent.py ──> tools.py ──> safe_calculator.py
                    └──> query_database.py
```

第一次写的时候把七种职责（提示词、schema、计算器、分发、LLM 调用、循环、CLI）
全塞进了一个文件，重构后按“实现 → 注册 → 运行”三层拆开：

| 文件 | 职责 | 不知道的事 |
| --- | --- | --- |
| `safe_calculator.py` | 表达式安全求值 | LLM、Agent 是什么 |
| `query_database.py` | 用户/订单查询 | LLM、Agent 是什么 |
| `tools.py` | schema 声明、参数校验、调用实现 | 循环怎么跑、模型怎么选工具 |
| `agent.py` | 循环、消息回填、终止控制 | calculator 怎么写、SQL 怎么写 |

Agent 循环沿用 02-agent-runtime 的原生 function calling 骨架，
本章的增量全在工具层。**新增工具只改 tools.py，agent.py 一行不用动。**

## 核心概念

### 1. 工具 = 面向模型的函数（三层设计）

一个工具在三处下功夫：

| 层 | 做什么 | 本 demo 的例子 |
| --- | --- | --- |
| schema 层 | 告诉模型参数名、类型、必填、语义 | `select_order` 的 `status`/`min_amount`/`product` |
| 校验层 | 缺参/非法值 → 错误文本，不抛异常 | “至少提供一个条件”“无效的订单状态” |
| 执行层 | 业务查询 → 结构化 JSON | `data` + `detail`（字段含义说明） |

`detail` 字段是个容易被忽略的设计：模型看到结果还要知道**每个字段是什么意思**，
否则查出来的 `user_id: 1` 它不知道怎么用。

### 2. 为什么不让模型写 SQL

`query_database.py` 把查询封装成高层业务函数（`get_user` / `get_order`），
模型只填参数，不接触 SQL：

- **安全**：所有 SQL 走参数化占位符（`?`），模型给的参数永远不会变成注入；
- **可控**：只能查预设的查询，不能 `DROP TABLE`；
- **省 token**：模型不需要理解表结构，description 就能说清用途。

底层 `query_to_json` 统一负责“执行 → JSON 序列化”，查询错误也返回 JSON
而不是抛异常——工具层对外永远是“文本进、文本出”。

### 3. 多步工具协作（实测）

问“张三买了什么？”模型自动拆成两步：

```text
[第 1 步] select_user({'user_name': '张三'})      -> 返回 id=1
[第 2 步] select_order({'user_id': 1})             -> 返回张三的 2 笔订单
[第 3 步] 模型整理成最终回答
```

这是 Agent 相比单次调用的核心价值：**中间结果作为观察回填，
模型自己决定下一步要查什么**。

### 4. 工具描述 = 接口文档（实测前后对照）

第一次跑“查询所有VIP用户”：

```text
-> select_user({'user_role': 'VIP'})
模型回答：目前暂时没有找到VIP用户的信息。
```

工具 description 没写角色枚举，模型自作主张填了 `VIP`，而数据库里存的是
`VIP用户`，精确匹配查不到。修复：把枚举写进 description

```python
"description": "按用户名或角色查询用户（角色取值：管理员、普通用户、VIP用户）",
```

重跑：

```text
-> select_user({'user_role': 'VIP用户'})
已找到1个VIP用户：王五
```

结论：**枚举值、单位、格式这些“接口约定”必须写进工具描述**，
和“参数缺失先询问”是同一级别的规则。

### 5. 精确匹配 vs 模糊匹配

本 demo 全部用 `=` 精确匹配，参数语义差一点就查不到（上面 VIP 的案例）。
这是设计决策：精确匹配结果可控；模糊搜索（`LIKE` / embedding）是另一套
工程，留给 RAG 章节。

### 6. 规则、schema、数据三者要一致

旧模拟数据里有 `待发货`，但规则只认“已完成/已取消/进行中”。
重构时在 `_init_demo_data` 里加了一条幂等迁移：

```python
cursor.execute(
    "UPDATE orders SET status = ? WHERE status NOT IN (?, ?, ?)",
    ("进行中",) + ORDER_STATUS,
)
```

教训：prompt 规则、工具 schema、数据库真实数据不一致时，
要显式修复，不能假装不存在——模型迟早会查出来给你看。

## 实测轨迹（节选）

```text
$ python agent.py "127*3 等于多少？"
[第 1 步] calculator({'content': '127*3'})
[第 2 步] 127乘以3等于381。

$ python agent.py "查询金额大于5000的已完成订单"
[第 1 步] select_order({'status': '已完成', 'min_amount': 5000})
[第 2 步] 订单101 MacBook Pro 12999.0 已完成

$ python agent.py "查询订单"
[第 1 步] 模型直接回答：您需要提供更具体的查询条件……
```

数据工具自测也通过：角色查询、用户名查订单、状态枚举迁移后
只剩 `已完成/进行中/已取消` 三种。

## 踩坑记录

- **`arguments['arguments']` 是原代码最隐蔽的 bug**：计算器工具里把
  `content` 错写成 `arguments`，`KeyError` 被 `except` 吞成
  “计算错误”字符串回填给模型——**bug 变成了模型观察到的“事实”**，
  模型还会一本正经地复述这个错误。这类错误最难排查，因为链路“看起来正常”；
- **schema 类型与真实数据不一致**：原代码 `product` 字段类型是 `float`，
  但它是产品名称。模型填数字、工具查不到，两头都不对；
- **无用导入**：`from fastapi import params`、`from rich.json import JSON`、
  `from exceptiongroup import catch` 三个都没用，属于历史残留；
- **`str(dict)` 冒充 JSON**：原代码把结果用 `str({...})` 包装，模型收到的是
  Python 字面量（单引号）不是 JSON，解析行为不一致。统一 `json.dumps(ensure_ascii=False)`；
- **SQL 必须参数化**：参数来自模型，字符串拼接 = 注入入口。

## 疑问 / 待探索

- [ ] 工具数量多起来后，模型怎么从几十个工具里选对？描述太长会不会反而干扰？
- [ ] 工具返回结果太大怎么办？截断、分页还是摘要？
- [ ] `check_same_thread=False` 在多线程 Agent 并发下的代价和风险；
- [ ] 声明式工具注册表（把 schema + 实现绑定在一起，免手写 if/elif 分发）
      什么时候值得引入；
- [ ] 一次请求多个 `tool_calls` 的并行执行与结果归并；
- [ ] 什么时候该用 `LIKE` 模糊匹配，什么时候必须精确匹配。

## 下一步

`04-rag`：工具的“数据源”从关系型数据库升级为知识库——
embedding 相似度检索，让 Agent 能回答“数据库里没有”的问题。
