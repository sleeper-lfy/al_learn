# AI Agent 学习路线与实践项目

> 从 LLM 基础，到手动实现 Agent，再到 LangChain / LlamaIndex，最终完成企业级 Agent 项目。

这是我的 **AI Agent 系统学习与实践项目**。

项目的核心目标不是单纯学习某一个框架，而是理解：

> **LLM 是如何工作的 → Tool Calling 是什么 → Agent 如何运行 → RAG 如何实现 → 框架如何封装这些能力 → 如何构建真正可用的 Agent 系统。**

整个项目采用：

**理论学习 → 手动实现 → 框架实现 → 项目实践 → 总结复盘**

的方式进行。

---

# 一、学习目标

最终希望具备以下能力：

- 理解 LLM 基础原理
- 理解 Token / Embedding / Transformer 等核心概念
- 掌握 Prompt Engineering
- 理解 System / User / Assistant
- 理解 Temperature、Sampling 等生成参数
- 理解 Tool Calling
- 能够设计 Tool Schema
- 能够处理 Tool 调用失败
- 能够手动实现基础 Agent
- 理解 Agent 的执行循环
- 掌握 RAG 基本原理
- 能够独立实现 RAG Demo
- 掌握 LangChain
- 掌握 LlamaIndex
- 理解 Agent Framework 的核心抽象
- 掌握 Memory / State / Workflow
- 掌握企业知识库设计
- 理解 Agent 的安全与权限控制
- 理解 Agent Evaluation
- 了解 Fine-tuning
- 最终完成一个完整的企业级 Agent 项目

---

# 二、总体学习路线

```text
                    AI Agent 学习路线

                         │
                         ▼
                ┌─────────────────┐
                │   LLM 基础       │
                │ Token / Prompt  │
                │ Embedding       │
                │ Transformer     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  LLM API 调用    │
                │ System/User     │
                │ Assistant       │
                │ Temperature     │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Prompt工程       │
                │ Role / Context  │
                │ Output Format   │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   Tool Calling   │
                │ Tool Schema      │
                │ 参数校验         │
                │ 异常处理         │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │  手动实现 Agent   │
                │ Think → Tool     │
                │ Observation     │
                │ → Final Answer  │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │      RAG         │
                │ 文档解析         │
                │ Chunking        │
                │ Embedding       │
                │ Vector DB       │
                │ Retrieval       │
                └────────┬────────┘
                         │
                         ▼
              ┌──────────────────────┐
              │ LangChain / LlamaIndex│
              │ Framework Learning   │
              └──────────┬───────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ Agent Workflow   │
                │ Memory / State   │
                │ Multi-Agent      │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │ 企业级 Agent     │
                │ 权限 / 安全      │
                │ Evaluation      │
                │ Observability   │
                └────────┬────────┘
                         │
                         ▼
                ┌─────────────────┐
                │   综合项目       │
                │ 企业知识库 Agent │
                └─────────────────┘
```

---

# 三、阶段一：LLM 基础

## 学习目标

理解大模型到底是什么，以及一次请求是如何进入模型并产生回答的。

## 核心知识

- LLM
- Token
- Context Window
- Transformer
- Attention
- Embedding
- Position Encoding
- Logits
- Softmax
- Sampling
- Temperature
- Top-K
- Top-P

## 重点理解

需要能够回答：

### Token 是什么？

理解：

```text
文本
 ↓
Tokenizer
 ↓
Token IDs
 ↓
Embedding
 ↓
Transformer
 ↓
Logits
 ↓
Sampling
 ↓
Token
 ↓
文本
```

### Temperature 是什么？

理解 Temperature 并不是简单地：

> “越高越随机”

而是：

> **影响模型对候选 Token 的概率分布进行采样时的分布形状。**

---

# 四、阶段二：LLM API

## 学习目标

能够脱离框架，直接调用大模型 API。

当前主要使用：

- Python
- requests
- Ollama
- Qwen

## 实践

实现：

```text
用户输入
   ↓
Python
   ↓
HTTP Request
   ↓
Ollama
   ↓
LLM
   ↓
Response
   ↓
Python
   ↓
输出
```

## 已完成

- [x] Ollama API 调用
- [x] Chat API
- [x] System Message
- [x] User Message
- [x] Assistant Response

---

# 五、阶段三：Prompt Engineering

## 学习目标

理解 Prompt 不只是“告诉模型一句话”。

需要掌握 Prompt 的结构化设计。

## 学习内容

```text
Role
 ↓
Task
 ↓
Context
 ↓
Rules
 ↓
Tools
 ↓
Output Format
 ↓
Examples
```

## 学习方法

通过实际实验比较：

```text
Prompt A
VS
Prompt B
VS
Prompt C
```

观察：

- 准确率
- 稳定性
- 是否遵循规则
- 输出格式
- 幻觉情况

## 实践项目

实现：

```text
影视检索 Agent Prompt
```

让 LLM 根据用户需求选择不同 Tool。

---

# 六、阶段四：Tool Calling

这是进入 Agent 开发非常重要的一步。

## 核心概念

```text
LLM
 │
 ├── 普通回答
 │
 └── Tool Call
       │
       ▼
     Tool
       │
       ▼
   Tool Result
       │
       ▼
      LLM
       │
       ▼
   Final Answer
```

## 学习内容

- Function Calling
- Tool Schema
- JSON Schema
- Tool 参数
- 参数校验
- Tool 返回值
- Tool Exception
- Tool 超时
- Tool 权限

## 重点理解

### 为什么需要 Tool Schema？

因为 LLM 需要知道：

```text
Tool叫什么
Tool做什么
需要什么参数
参数是什么类型
哪些参数必须存在
```

例如：

```json
{
  "name": "search_movie",
  "description": "搜索电影",
  "parameters": {
    "query": "string"
  }
}
```

---

# 七、阶段五：手动实现 Agent

## 学习目标

不使用 LangChain，自己实现 Agent。

这是整个学习过程中非常重要的一阶段。

## Agent 核心循环

```text
User
 ↓
LLM
 ↓
判断是否需要 Tool
 ↓
Tool Call
 ↓
Tool 执行
 ↓
Observation
 ↓
LLM
 ↓
判断是否继续
 ↓
Final Answer
```

## 自己实现

```python
while True:

    response = llm(messages, tools)

    if response.has_tool_call():

        tool_result = execute_tool(
            response.tool_call
        )

        messages.append(tool_result)

    else:

        return response
```

## 学习重点

理解：

> **Agent 本质上并不是一个神秘的新模型，而是 LLM + Tools + 状态 + 执行循环。**

---

# 八、阶段六：Agent 安全

Agent 一旦可以调用真实 Tool，就不能让 LLM 完全自由执行。

## 学习内容

### SQL Agent

重点理解：

```text
LLM
 ↓
SQL
 ↓
权限控制
 ↓
SQL Validation
 ↓
Database
```

而不是：

```text
LLM
 ↓
随便生成 SQL
 ↓
直接执行
```

## 需要学习

- SQL Injection
- Tool Permission
- 参数校验
- SQL 白名单
- Read / Write 权限
- Tool Timeout
- Tool Retry
- Error Handling
- Sandbox

---

# 九、阶段七：RAG

## 学习目标

能够独立实现一个完整 RAG 系统。

## RAG Pipeline

```text
Documents
    │
    ▼
Document Loader
    │
    ▼
Text Splitter
    │
    ▼
Chunk
    │
    ▼
Embedding
    │
    ▼
Vector Database
    │
    ▼
Retriever
    │
    ▼
Relevant Documents
    │
    ▼
Prompt
    │
    ▼
LLM
    │
    ▼
Answer
```

## 学习内容

### 文档处理

- PDF
- Markdown
- TXT
- Word
- HTML

### Chunking

重点研究：

- Fixed Size Chunk
- Recursive Chunk
- Semantic Chunk
- Overlap
- Chunk Size

### Embedding

理解：

```text
文本
 ↓
Embedding Model
 ↓
Vector
```

### Vector Database

学习：

- FAISS
- Chroma
- Milvus
- Elasticsearch

---

# 十、RAG 实践项目

## 项目：个人知识库

实现：

```text
documents/
    ├── book.txt
    ├── article.md
    └── notes.md
```

然后：

```text
文档
 ↓
切片
 ↓
Embedding
 ↓
Vector DB
 ↓
Query
 ↓
Retrieval
 ↓
LLM
```

## 已完成

- [x] RAG Demo
- [x] 文档读取
- [x] 文档切片
- [x] Embedding
- [x] 检索
- [x] LLM 回答

## 下一步

- [ ] Chunking 对比实验
- [ ] Retrieval 参数实验
- [ ] Reranker
- [ ] Hybrid Search
- [ ] Metadata Filter
- [ ] Query Rewrite
- [ ] Multi Query
- [ ] RAG Evaluation

---

# 十一、阶段八：LangChain

在理解底层实现之后开始学习框架。

## 学习原则

不是：

```text
看到 API
 ↓
背 API
```

而是：

```text
自己实现
 ↓
理解原理
 ↓
LangChain API
 ↓
寻找对应关系
```

## 学习内容

- Model
- Prompt
- Output Parser
- Runnable
- Tool
- Agent
- Retriever
- Document
- VectorStore
- Memory
- LangGraph

重点研究：

> LangChain 到底帮我们封装了什么？

---

# 十二、阶段九：LlamaIndex

重点学习它在：

> **数据 → Index → Retrieval → RAG**

方面的设计。

## 学习内容

- Document
- Node
- Index
- VectorStore
- Retriever
- Query Engine
- Agent
- Workflow

重点进行：

```text
手写 RAG
   ↓
LangChain RAG
   ↓
LlamaIndex RAG
```

三者对比。

---

# 十三、阶段十：Agent Workflow

当 Agent 变复杂之后，单纯的：

```text
LLM
 ↓
Tool
 ↓
LLM
```

已经不够。

开始学习：

- State
- Workflow
- Graph
- Node
- Edge
- Conditional Edge
- Human-in-the-loop

例如：

```text
              ┌──────────────┐
              │    User      │
              └──────┬───────┘
                     ▼
              ┌──────────────┐
              │ Intent Judge │
              └──────┬───────┘
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Search       RAG       SQL
          │          │          │
          └──────────┼──────────┘
                     ▼
              ┌──────────────┐
              │  Final LLM   │
              └──────────────┘
```

---

# 十四、阶段十一：Memory

学习 Agent 如何保存上下文。

## 分类

### Short-term Memory

```text
当前对话
```

### Long-term Memory

```text
用户历史信息
```

### Conversation State

```text
Agent 当前执行状态
```

重点理解：

> Memory 不等于简单地把所有聊天记录塞进 Prompt。

---

# 十五、阶段十二：Multi-Agent

学习多个 Agent 协作。

例如：

```text
                Manager Agent
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
 Research Agent   RAG Agent     SQL Agent
       │             │             │
       └─────────────┼─────────────┘
                     ▼
                Final Agent
```

重点研究：

- Agent Communication
- Task Delegation
- Role Design
- State Sharing
- Agent Routing
- Failure Handling

---

# 十六、阶段十三：Agent Evaluation

一个 Agent 能运行不代表它做得好。

开始学习如何评估 Agent。

## RAG Evaluation

例如：

```text
Retrieval Recall
Retrieval Precision
Context Relevance
Answer Relevance
Faithfulness
```

## Agent Evaluation

例如：

```text
Tool Selection Accuracy
Tool Argument Accuracy
Task Success Rate
Latency
Token Cost
Failure Rate
```

最终建立：

```text
Question Dataset
       ↓
Agent
       ↓
Result
       ↓
Evaluator
       ↓
Score
```

---

# 十七、阶段十四：Fine-tuning

Fine-tuning 放在 Agent 基础能力之后学习。

## 学习内容

- Pre-training
- SFT
- LoRA
- QLoRA
- Dataset
- Instruction Tuning
- RLHF
- DPO

重点理解：

> **什么时候应该 Prompt？什么时候应该 RAG？什么时候应该 Fine-tuning？**

这是实际项目中非常重要的能力。

---

# 十八、阶段十五：企业级 Agent

最终进入真正的工程实践。

## 需要考虑

### 架构

```text
                Frontend
                   │
                   ▼
              API Gateway
                   │
                   ▼
              Agent Service
                   │
       ┌───────────┼───────────┐
       ▼           ▼           ▼
      LLM         RAG         Tools
       │           │           │
       │           ▼           ▼
       │       Vector DB    Database/API
       │
       ▼
   Observability
       │
       ▼
   Evaluation
```

## 工程能力

- API
- FastAPI
- Docker
- Redis
- PostgreSQL
- Vector Database
- Logging
- Monitoring
- Authentication
- Authorization
- Rate Limiting
- Caching
- Retry
- Timeout
- Async
- Streaming

---

# 十九、最终综合项目

## 企业知识库 Agent

最终目标：

> 构建一个真正具备企业场景的 Agent 系统。

例如：

```text
用户
 │
 ▼
Agent
 │
 ├── 知识库 Tool
 │       └── RAG
 │
 ├── SQL Tool
 │       └── Database
 │
 ├── Search Tool
 │       └── Web Search
 │
 └── API Tool
         └── External API
```

Agent 能够：

- 查询企业知识库
- 查询数据库
- 搜索互联网
- 调用业务 API
- 根据任务选择 Tool
- 处理 Tool 错误
- 保留对话状态
- 进行权限控制
- 输出结构化结果

---

# 二十、项目目录

建议最终形成：

```text
AI-Agent-Learning/
│
├── 01-LLM-Basic/
│   ├── token/
│   ├── embedding/
│   ├── transformer/
│   └── sampling/
│
├── 02-LLM-API/
│   ├── ollama/
│   └── qwen/
│
├── 03-Prompt/
│   ├── basic/
│   ├── structured/
│   └── experiments/
│
├── 04-Tool-Calling/
│   ├── basic/
│   ├── schema/
│   └── error-handling/
│
├── 05-Agent/
│   ├── manual-agent/
│   ├── react-agent/
│   └── agent-security/
│
├── 06-RAG/
│   ├── document-loader/
│   ├── chunking/
│   ├── embedding/
│   ├── vector-db/
│   ├── retrieval/
│   └── rag-demo/
│
├── 07-LangChain/
│   ├── model/
│   ├── prompt/
│   ├── tools/
│   ├── rag/
│   └── agent/
│
├── 08-LlamaIndex/
│   ├── document/
│   ├── index/
│   ├── retrieval/
│   └── rag/
│
├── 09-Agent-Workflow/
│   ├── state/
│   ├── workflow/
│   └── langgraph/
│
├── 10-Memory/
│
├── 11-Multi-Agent/
│
├── 12-Evaluation/
│
├── 13-Fine-Tuning/
│
└── 14-Final-Project/
    └── enterprise-agent/
```

---

# 二十一、每个阶段的学习方法

每个知识点遵循：

```text
① 理论
   ↓
② 自己解释
   ↓
③ 最小 Demo
   ↓
④ 手写实现
   ↓
⑤ 框架实现
   ↓
⑥ 对比源码
   ↓
⑦ 总结
```

例如学习 Tool Calling：

```text
了解 Function Calling
        ↓
自己设计 Tool Schema
        ↓
自己实现 Tool
        ↓
自己实现 Agent Loop
        ↓
使用 LangChain Tool
        ↓
阅读框架源码
        ↓
总结框架到底封装了什么
```

---

# 二十二、学习笔记标准

每学习一个知识点，都尽量回答以下问题：

## What

> 它是什么？

## Why

> 为什么需要它？

## How

> 它是怎么工作的？

## Example

> 最小代码怎么实现？

## Problem

> 它解决了什么问题？

## Limitation

> 它有什么缺点？

## Framework

> LangChain / LlamaIndex 是怎么实现的？

## Interview

> 如果面试官问我，我怎么回答？

---

# 二十三、面试能力目标

最终能够回答：

### LLM

- Token 是什么？
- Embedding 是什么？
- Transformer 是什么？
- Attention 是什么？
- Temperature 是什么？

### Prompt

- System / User / Assistant 有什么区别？
- Prompt 如何设计？
- 如何降低幻觉？

### Tool Calling

- Tool Schema 为什么重要？
- Tool 调用失败怎么办？
- 为什么不能允许 LLM 随意执行 SQL？

### Agent

- Agent 和普通 LLM 有什么区别？
- Agent Loop 是什么？
- ReAct 是什么？
- Agent 如何选择 Tool？

### RAG

- RAG 是什么？
- Chunk 为什么重要？
- Chunk Size 怎么选择？
- RAG 检索不到怎么办？
- 为什么需要 Reranker？
- Hybrid Search 是什么？

### Framework

- LangChain 解决什么问题？
- LlamaIndex 解决什么问题？
- LangGraph 为什么需要 State？

### 企业级

- 如何保证 Agent 安全？
- 如何控制 Tool 权限？
- 如何评估 Agent？
- 如何降低 Token 成本？
- 如何提高 Agent 稳定性？

---

# 二十四、当前学习进度

截至目前：

- [x] LLM API
- [x] System / User / Assistant
- [x] Prompt 基础
- [x] Temperature 基础理解
- [x] Tool Calling
- [x] Tool Schema
- [x] Tool Error Handling
- [x] 手动 Agent 基础
- [x] RAG Demo
- [ ] RAG 深入优化
- [ ] LangChain
- [ ] LlamaIndex
- [ ] LangGraph
- [ ] Memory
- [ ] Multi-Agent
- [ ] Evaluation
- [ ] Fine-tuning
- [ ] 企业级 Agent
- [ ] 综合项目

---

# 二十五、核心原则

这个项目最重要的原则：

> **不要把学习框架当成学习 Agent。**

应该按照：

```text
原理
 ↓
手写
 ↓
框架
 ↓
源码
 ↓
工程
```

进行学习。

尤其是：

```text
手写 Agent
        ↓
LangChain Agent
        ↓
LangGraph
```

以及：

```text
手写 RAG
        ↓
LangChain RAG
        ↓
LlamaIndex RAG
```

通过这种方式理解：

> **框架到底帮我们解决了什么问题。**

---

# 二十六、最终目标

完成这个项目后，希望能够独立完成：

```text
需求分析
   ↓
Agent 架构设计
   ↓
Tool 设计
   ↓
Prompt 设计
   ↓
RAG 设计
   ↓
Workflow 设计
   ↓
Memory 设计
   ↓
安全控制
   ↓
Evaluation
   ↓
部署
```

最终达到：

> **能够从 0 到 1 设计、实现和解释一个完整的 AI Agent 系统。**

而不是只会调用：

```python
Agent(...)
```

---

# 学习路线总结

```text
LLM
 ↓
Prompt
 ↓
Tool Calling
 ↓
手写 Agent
 ↓
RAG
 ↓
LangChain
 ↓
LlamaIndex
 ↓
LangGraph / Workflow
 ↓
Memory
 ↓
Multi-Agent
 ↓
Evaluation
 ↓
Fine-tuning
 ↓
企业级 Agent
 ↓
综合项目
```

**最终目标：理解原理 + 能写代码 + 能用框架 + 能做项目 + 能通过面试。**