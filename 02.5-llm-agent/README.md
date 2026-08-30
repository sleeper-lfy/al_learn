# 02.5-llm-agent · 自学笔记

> 2026-08-27 ｜ 让 LLM 当 Agent（文本 JSON 约定范式）跑通 ✅

## 目标

02-agent-runtime 用了原生 function calling，这一章故意换一种**更朴素**的写法：
不用 `tools` 协议，而是用输出格式约束让模型直接吐
`{"action": ..., "input": ...}`，程序 switch 分发。

目的不是“再写一遍”，而是把两种范式放在一起对照，看清各自的取舍。

## 与 02-agent-runtime 的对照

| 维度 | 02.5 本章（文本约定） | 02-agent-runtime（原生 calling） |
| --- | --- | --- |
| 模型输出 | `{"action":"calculator","input":"123+456"}` | `message.tool_calls` 结构化对象 |
| 约束手段 | `format` JSON Schema | `tools` 数组声明 |
| 分发 | 解析 JSON → switch | 遍历 `tool_calls` → dispatch |
| 结果回填 | 无 id 关联，只能当文本 | `tool_call_id` 精确关联 |
| 上下文 | action 文本混在 messages 里 | 工具调用是独立结构化消息 |
| 模型要求 | 会输出 JSON 就行 | 必须支持原生 tool calling |
| 解析健壮性 | 弱（要自己兜底） | 强（协议自带结构） |

一句话：**文本约定赢在通用，原生 calling 赢在规范**。

## 核心实现

### 1. 用 format 把输出“焊死”成 JSON

```python
ACTION_SCHEMA = {
    "type": "object",
    "properties": {
        "action": {"type": "string"},
        "input": {"type": "string"},
    },
    "required": ["action", "input"],
}
```

`format` 在 Ollama 里通过 grammar 约束解码过程，理论上模型“只能”按结构输出。
但这只是**第一道防线**，不能当 100% 保证。

### 2. action 白名单

```python
ACTIONS = {"calculator"}

def dispatch(action, input_text):
    if action not in ACTIONS:
        return f"未知 action：{action}，我只能执行 {sorted(ACTIONS)}"
```

原代码只写了 `if action == 'calculator'`，模型若输出 system 里提到但没实现的
`search` / `weather` 就会静默失败。白名单校验把“模型乱选 action”变成
可见的错误文本——错误也是观察，这是上一章学到的原则的延续。

### 3. 解析层兜底

```python
try:
    decision = json.loads(content)
except json.JSONDecodeError:
    print(f"模型输出不是合法 JSON（需要重试或加强提示词）：\n{content}")
    return 1
```

`format` 约束也可能偶尔失效（弱模型、兼容端点），解析失败必须有明确的失败路径。

## 实测

真实运行（Qwen3-1.7B）：

```text
$ python calculator_agent_calculator.py "123+456等于多少？"
模型决策：action='calculator', input='123+456'
执行结果： 579
```

分发兜底单测：

```text
unknown action : 未知 action：weather，我只能执行 ['calculator']
missing input  : 缺少 input，请提供要计算的数学表达式
calc           : 9
dangerous      : 计算错误：不支持的表达式节点: Call
```

未知 action 和缺参都不再崩溃/静默，而是返回可读文本；
`__import__('os')` 依然被 AST 白名单挡掉。

## 踩坑记录

- **`format` 约束不是银弹**：grammar 保证结构，但模型在弱模型/跨端点上仍可能
  输出非法 JSON，解析层必须兜底，失败时把原文打出来方便诊断；
- **action 必须白名单校验**：system prompt 里提了哪些 action，模型就可能输出
  哪些，没实现的一律要拦截成可见错误，否则静默失败最难排查；
- **文本 action 会污染上下文**：`{"action":"calculator",...}` 这段 JSON 作为
  assistant 消息留在历史里，多轮后模型容易被自己的 JSON 带偏；
  原生 `tool_calls` 是独立结构，没有这个问题；
- **没有 tool_call_id**：一次请求多个 action 时，无法把“哪个结果对应哪次调用”
  精确关联，只能按顺序假设——这是文本约定在多工具场景下的硬伤。

## 疑问 / 待探索

- [ ] 文本约定 + 循环回填怎么写？把执行结果以 `user` 或 `assistant` 文本
      塞回 messages，模型下一轮再决策——和原生 `tool` 消息的体验差多少？
- [ ] Ollama 的 `format` 在底层是怎么把 JSON Schema 变成 grammar 的？
- [ ] 什么场景该坚定选文本约定？（模型不支持 tool calling、
      要兼容 OpenAI 等不同后端、快速原型）
- [ ] OpenAI 兼容端点 `/v1/chat/completions` 的 `response_format`
      与 Ollama `format` 的对应关系；
- [ ] 一次要执行多个 action 时，文本约定的解析/分发怎么做才不脆？

## 下一步

`03-tool-calling`：运行时骨架已经会了，下一章把工具从“固定返回值”升级成
真实数据库查询——重点是“怎么设计一个 Agent 能用的工具”。
