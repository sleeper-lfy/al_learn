# 01-llm-basics · 自学笔记

> 2026-08-26 ｜ 状态：四个 demo 全部跑通 ✅

## 目标与组织

本章把“调模型”从一次请求扩展成对 LLM 应用开发基础概念的理解：
Token、Context Window、角色消息、Prompt、Temperature、Streaming、结构化输出。


```text
01-llm-basics/
├── call_llm.py         # Token、Context Window（/api/generate）
├── call_llm_prompt.py  # 角色消息、Prompt、Temperature（/api/chat）
├── call_llm_stream.py  # Streaming（流式输出）
└── call_llm_json.py    # Structured Output / JSON 输出
```

---

## 1. Token —— 先有度量，才能谈优化

`call_llm.py` 用最朴素的 `/api/generate` 发一次请求，然后打印响应元数据。
实测（Qwen3-1.7B，问 GIL）：

```text
输入(prompt) tokens : 19
输出(生成)  tokens : 542
生成速度           : 138.1 tok/s
```

要点：

- **Token 是模型的最小计量单位，不是字符。** 中文一个字可能占 1~2 个 token，
  所有“成本、延迟、上下文占用”的估算都以 token 为口径；
- 元数据字段 `prompt_eval_count` / `eval_count` / `eval_duration` 是唯一可靠的
  token 度量来源，比自己在外面数文本字符准得多；
- 138 tok/s 是本机的生成速度基线，后面做 Agent 时估算“一次工具调用要等多久”
  就用这个数量级。

顺带一个观察：prompt 里写了“用三句话介绍”，结果模型输出 542 tokens 的长文——
**约束写在普通 prompt 文本里并不可靠**，这正是下一节角色消息要解决的问题。

## 2. Context Window —— 模型的“工作记忆”有限

同一份 payload 里的 `options.num_ctx = 4096` 就是上下文窗口：
模型一次请求最多能看到这么多 token，超出部分会被截断。

要记住的关联：

- 多轮对话的历史、RAG 检索来的内容、工具返回结果，全都占窗口；
- Agent 的核心工程问题之一就是“窗口不够用了怎么办”：
  截断最旧消息、摘要历史、按相关性筛选上下文——后面章节逐个验证；
- `num_ctx` 不是越大越好：窗口越大显存占用越高，1.7B 这种小模型尤其明显。

## 3. 角色消息 —— chat 端点才有的概念

`/api/generate` 只有一段文本，没有角色；`/api/chat` 用 `messages` 数组表达：

```python
messages = [
    {"role": "system", "content": "你是 Python 专家。回答不超过 3 句话，用中文。"},
    {"role": "user", "content": "什么是装饰器？"},
]
```

- `system`：定义模型的行为、规则、背景、约束（“你是谁、怎么回答”）；
- `user`：用户的任务和输入；
- `assistant`：模型生成的回答。**多轮对话就是把 assistant 回答追加回
  `messages`，历史对话从此变成上下文的一部分。**

实测对照：同样要求“不超过 3 句话”，写在 system 里（本节 demo）基本遵守，
写在 generate 的 prompt 文本里（第 1 节，542 tokens）完全不遵守。
单次对比不算严谨结论，但方向上印证了“角色消息比裸文本更稳定”。

## 4. Prompt 结构

把本章的图转成代码视角，prompt 不是“一句话”，而是一组东西的组装：

```text
System Message                  User Message + 其他上下文
├─ 指令                         ├─ 问题/任务/要求
├─ 角色                         ├─ 历史对话
└─ 约束                         ├─ RAG 内容
                                └─ 工具结果
        └──────────┬───────────┘
                   ↓
             Context（上下文）
                   ↓
             Prompt（提示/指令）
                   ↓
             LLM 生成回答
                   ↓
             Assistant Message
```

工程含义：写 prompt 就是**明确拆解“约束 + 输入 + 上下文”三部分**，
而不是把要求全堆进一句话里。后面每一章（RAG、工具调用）都在往
“其他上下文”这一格里加东西。

## 5. Temperature —— 采样随机性的旋钮

`call_llm_prompt.py` 用同一个问题对比 `temperature=0` 和 `1.2`：

```text
=== temperature=0 ===
装饰器是Python中用于修改函数或类行为的高级语法，通过函数装饰器接收
目标函数作为参数，并返回新函数。……

=== temperature=1.2 ===
装饰器是 Python 中用于修改函数或类行为的高级语法，通过将函数作为参数
传递并返回新函数来实现。……
```

两点观察：

- 对“装饰器是什么”这类事实性问题，两次输出差异不大——温度影响的是
  概率采样的发散程度，**事实性问题本身分布很尖，温度改变不了答案**；
- 要看温度的真实影响，得对开放性问题多次采样看分布，单次对比说明力弱。

用途速记：抽取/代码/结构化任务用低温（0~0.3）保稳定；
创意写作用高温；Agent 默认低温 + 结构化输出，因为要保证流程可控。

## 6. Streaming —— 首 token 延迟的解法

`call_llm_stream.py` 把 `stream=True`，Ollama 按 NDJSON 逐行返回 chunk：

```python
chunk = json.loads(line)
piece = chunk["message"]["content"]   # 本次增量
if chunk.get("done"):
    eval_count = chunk.get("eval_count")  # 结束帧带真实 token 数
```

实测（问递归和迭代的区别）：

```text
[完成] 网络片段 265 个，模型实际生成 586 tokens，耗时 9.7s，约 60.2 tok/s
```

三个值得记住的点：

- **网络片段数 ≠ token 数**：265 个片段、586 个 token，Ollama 按自己的节奏
  切块返回。要精确数字只能信结束帧的 `eval_count`；
- 流式解决的是**首 token 延迟**：用户不需要等整个回答生成完才能看到第一个字，
  Agent 的“边想边说”就依赖这个机制（呼应 00 章笔记的疑问）；
- 本章两次测速（138 vs 60 tok/s）差异大，因为输出长度、markdown 表格、
  机器负载都影响吞吐——测速要说明场景，不能当常量。

## 7. Structured Output / JSON —— 约束 + 校验

`call_llm_json.py` 是本章最“工程”的一个：结构化输出必须两步都做。

**第一步：约束。** `format` 传 JSON Schema，模型按结构生成：

```python
payload = {
    "messages": [...],
    "format": {
        "type": "object",
        "properties": {
            "project_name": {"type": "string"},
            "platforms": {"type": "array", "items": {"type": "string"}},
            ...
        },
        "required": ["project_name", "platforms", ...],
    },
}
```

**第二步：校验。** `json.loads` 解析 + 必需字段检查，失败要能报错/重试。

实测输出（把一段报销系统需求抽成 JSON）：

```json
{
  "project_name": "公司报销审批系统",
  "platforms": ["Web端", "移动端"],
  "key_features": [
    "支持多级审批流程配置",
    "实时状态追踪与通知",
    "手机端离线操作",
    "权限分级管理",
    "数据加密传输与存储"
  ],
  "estimated_months": 3
}
```

一个值得注意的观察：**schema 只约束结构，不约束内容语义**——需求里只提了
手机端，模型自己补了 Web端。字段类型、必填都对，但业务语义仍要人来判断。
这也是为什么“校验”阶段不能只查 JSON 合法性。

## 踩坑记录

- **网络片段数当 token 数**：流式里按 chunk 数统计会严重低估，必须用结束帧
  的 `eval_count`；
- **约束放错位置**：同样的话，放 prompt 文本 vs 放 system 角色，效果差很多
  （542 tokens vs 3 句话）。角色消息是更强的约束通道；
- **`messageformat2` 是不必要的依赖**：原 `call_llm_prompt.py` import 了它，
  但这里只是字符串模板，f-string 足够。减少一个依赖，概念也更聚焦；
- **JSON 偶尔不合法**：即使 `format` 给了 schema，解析失败的分支也必须写
  （校验层不是装饰，是必须品）；Ollama 0.5 之前的版本不支持 schema 格式，
  要用 `format: "json"` 兜底。

## 疑问 / 待探索

- [ ] `temperature` 和 `top_p` / `top_k` / `seed` 的关系？设了 seed 能否完全复现输出？
- [ ] `num_ctx` 上限由什么决定（模型本身 vs 显存）？1.7B 最大能开多少？
- [ ] `format` 的 JSON Schema 在底层是怎么变成 grammar 约束的？
- [ ] `/api/chat` 的 `tool` 角色消息长什么样？——03 章工具调用时验证
- [ ] Ollama 的 OpenAI 兼容端点（`/v1/chat/completions`）对
      `response_format` 的支持程度，接 LangChain 时可能直接用

## 下一步

`02-agent-runtime`：把“调用 LLM”从脚本变成可组合的组件。
