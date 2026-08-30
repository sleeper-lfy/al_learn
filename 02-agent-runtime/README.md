# 02-agent-runtime · 自学笔记

> 2026-08-27 ｜ 实现 Agent Runtime 跑通 ✅

## 目标

本章把“调模型”升级成“让模型干活”：

- Agent 不是一次 LLM 调用，而是一个**循环**（决策 → 行动 → 观察 → 再决策）；
- 用 Ollama 原生 function calling 让模型选择工具；
- 工具的分发与安全执行。

## 组织

两个文件，正好对应 Agent 架构里最本质的分离——**工具是可插拔组件，
Agent 只负责分发**：

```text
02-agent-runtime/
├── safe_calculator.py           # 工具实现：AST 白名单安全计算器
└── calculator_agent_switch.py   # Agent 循环：tools schema、tool_calls、tool 消息回填
```

## 核心概念

### 1. Agent = 循环，不是一次调用

01 章的调用是一次性的“问→答”。Agent 是把它包进一个循环，直到模型认为任务完成：

```python
for step in range(1, MAX_STEPS + 1):
    message = call_llm(messages)["message"]
    messages.append(message)                # assistant 消息（含 tool_calls）回填

    if not message.get("tool_calls"):       # 模型不再调用工具 = 终止条件
        print(message["content"])
        return

    for tool_call in message["tool_calls"]: # 可能一次请求多个工具
        result = dispatch(tool_call["function"]["name"], arguments)
        messages.append({"role": "tool", "content": result,
                         "tool_call_id": tool_call["id"]})
```

这就是 ReAct 骨架：模型在“思考用什么工具”，程序在“执行”，
执行结果以 `tool` 消息回到上下文，模型据此继续。

### 2. tools 数组 = 把“有什么工具”告诉模型

```python
TOOLS = [{
    "type": "function",
    "function": {
        "name": "calculator",
        "description": "计算数学表达式",
        "parameters": {
            "type": "object",
            "required": ["content"],
            "properties": {
                "content": {"type": "string",
                            "description": "完整可计算的数学表达式"}
            },
        },
    },
}]
```

`name` / `description` / `parameters` 三个字段决定模型能不能正确选工具——
description 写得越清楚，模型选错的概率越低。这本质上是“给模型看的接口文档”。

### 3. tool 消息的 tool_call_id 关联

工具结果必须带 `tool_call_id` 回填，模型才能把结果和“哪一次调用”对应上。
丢了 id，多工具并行时上下文就会错乱。

### 4. 终止条件：模型说了算，但要有保险丝

两个终止条件缺一不可：

- **正常终止**：模型不再返回 `tool_calls`，直接给最终回答；
- **保险丝**：`MAX_STEPS = 8`，模型陷入无限调用工具时强制停止。

### 5. 错误也是观察

工具参数缺失时不抛异常，而是返回错误文本：

```python
if not expr:
    return "缺少参数 content，请提供要计算的数学表达式"
```

错误文本作为 `tool` 消息回到模型，模型会据此向用户询问缺失信息——
这是 Agent 的纠错闭环，不是 crash。

### 6. 安全：AST 白名单，而不是 eval

计算器不用 `eval()`，而是把表达式解析成 AST，只允许白名单内的运算符节点：

```python
ALLOWED_OPS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ...
}
```

白名单之外的任何节点（`Call`、`Attribute`、`Name`……）一律拒绝。
这是 Agent 工具实现的底线：**工具是模型的执行器，必须先假设模型可能被骗去执行恶意输入**。

## 实测轨迹

三个场景都是真实运行（Qwen3-1.7B + Ollama 0.32.15）：

**场景 1：数字计算**

```text
[第 1 步] 模型请求 1 个工具调用
  -> calculator({'content': '123+456'})
[第 2 步] 模型直接回答：
123+456等于579。
```

**场景 2：有城市查询天气**

```text
[第 1 步] 模型请求 1 个工具调用
  -> weather({'content': '上海'})
[第 2 步] 模型直接回答：
今天上海的天气是晴天，气温26℃。
```

**场景 3：没给城市**

```text
[第 1 步] 模型直接回答：
您能告诉我您所在的城市吗？这样我才能为您查询天气哦。
```

没给城市时模型没有调用 weather、没有编造城市，而是按 system 规则询问——
说明“参数缺失先询问”的规则在 Qwen3-1.7B 上有效。

**安全边界验证（直接测 SafeCalculator）**：

| 表达式 | 结果 |
| --- | --- |
| `2**3` | `8` |
| `-5 + 3` | `-2` |
| `10 / 0` | `计算错误：division by zero` |
| `__import__('os').system('echo hi')` | `计算错误：不支持的表达式节点: Call` |
| `(1).__class__` | `计算错误：不支持的表达式节点: Attribute` |
| `1; print('x')` | `计算错误：invalid syntax` |

危险表达式全部被 AST 白名单挡住，这是 `eval()` 做不到的。

## 踩坑记录

- **`tool_call.function.arguments` 的类型不稳定**：这个 Ollama 版本返回的是
  dict，而部分版本/OpenAI 兼容端点返回 JSON 字符串。原代码直接
  `arguments['content']` 能跑正是因为返回 dict；我用 `json.loads` 反而炸了。
  正确写法是兼容两者：
  ```python
  raw = fn["arguments"]
  arguments = raw if isinstance(raw, dict) else json.loads(raw)
  ```
- **assistant 消息必须整体回填**：带 `tool_calls` 的 assistant 消息要原样
  append 回 `messages`，只回填 `content` 会丢掉调用记录，模型下一轮就“失忆”；
- **工具参数缺失别抛异常**：抛异常会中断整个 Agent 循环；返回错误文本，
  让模型自己纠错（实测缺城市场景，模型下一步就会询问用户）；
- **原生 function calling vs 文本 JSON 约定**：02-llm-agent 里那种
  “让模型输出 `{"action": ..., "input": ...}`”的写法更通用（任何模型都能用），
  但解析脆、action 文本会污染对话上下文；原生 `tool_calls` 结构化更强、
  有 id 关联，但依赖模型能力。两种都要会。

## 疑问 / 待探索

- [ ] 一次返回多个 `tool_calls` 时，模型是否真的会并行使用多个工具？本 demo
      支持循环处理，但没有专门构造“一次要调两个工具”的问题验证；
- [ ] Qwen3 的 `thinking` 推理内容和工具选择质量有什么关系？要不要在
      system prompt 里让模型“先想再调”？
- [ ] `qwen3.5-agent` 和通用 `Qwen3-1.7B` 在 function calling 上的表现差异；
- [ ] 模型陷入“同一个工具反复调用”的死循环时，`MAX_STEPS` 之外还能怎么兜底
      （比如连续同参调用直接判 no-op）？
- [ ] 工具返回内容很大时怎么办？截断/摘要策略；
- [ ] Ollama 的 OpenAI 兼容端点 `/v1/chat/completions` 的 `tools` 格式差异。

## 下一步

`02-llm-agent`：同一个计算器 Agent 的另一种写法（JSON action 约定），
和本章的原生 function calling 对照着看，能彻底搞懂两种范式。
