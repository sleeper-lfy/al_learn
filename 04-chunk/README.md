# RAG 文档切割与检索评估

> 本文用于 AI RAG 学习项目。
>
> 主要介绍 RAG 中的 **Document Splitting、Chunk、chunk_size、chunk_overlap、Metadata、Recall@K、MRR** 等核心概念，并结合当前项目进行说明。
>
> 当前阶段以“理解 RAG 工作原理和能够完成工程实现”为目标，不深入学术性的检索评估。

---

# 一、RAG 整体流程

RAG（Retrieval-Augmented Generation）的核心思想是：

> **先从知识库中检索相关知识，再把这些知识交给 LLM 生成答案。**

完整流程可以简单理解为：

```text
                 知识库构建
                     │
                     ▼
原始文档 → Document Parser
                     │
                     ▼
                Document
                     │
                     ▼
             Document Splitter
                     │
                     ▼
                  Chunks
                     │
                     ▼
                Embedding
                     │
                     ▼
                  Vectors
                     │
                     ▼
                Vector Store
```

用户查询时：

```text
用户问题
   │
   ▼
Embedding
   │
   ▼
Query Vector
   │
   ▼
Vector Store
   │
   ▼
Retriever
   │
   ▼
Top-K Chunks
   │
   ▼
Context
   │
   ▼
LLM
   │
   ▼
最终答案
```

因此可以看到：

> **文档切割负责把知识变成适合检索的基本单元，而 Retriever 负责从这些知识单元中找到相关内容。**

---

# 二、什么是 Document？

Document 可以理解为：

> **经过 Parser 解析后的一个文档对象。**

例如：

```text
中华人民共和国立法法.pdf
```

经过 PDF Parser 后，可以得到：

```python
{
    "content": "...",

    "metadata": {
        "source": "中华人民共和国立法法.pdf",
        "page": 4
    }
}
```

其中：

```text
content
```

保存文本内容。

```text
metadata
```

保存来源、页码等信息。

---

# 三、为什么不能直接把整个 Document 做 Embedding？

假设：

```text
中华人民共和国立法法.pdf
```

有 35 页。

如果直接：

```text
PDF
 ↓
完整文本
 ↓
Embedding
 ↓
一个 Vector
```

那么一个 Vector 里面包含：

```text
第一章
第二章
第三章
...
第十条
...
第一百二十条
```

大量不同主题。

用户问：

```text
全国人民代表大会有哪些立法权？
```

真正相关的可能只是其中很小的一部分。

因此需要：

```text
完整 Document
      ↓
Document Splitter
      ↓
多个 Chunk
```

---

# 四、什么是 Chunk？

Chunk 就是：

> **从原始 Document 中切出来的一小段文本。**

例如：

```text
Document
│
├── Chunk 0
├── Chunk 1
├── Chunk 2
├── Chunk 3
├── Chunk 4
└── ...
```

例如：

```python
{
    "content":
        "第十条 全国人民代表大会和全国人民代表大会常务委员会行使国家立法权……",

    "metadata": {
        "source": "中华人民共和国立法法.pdf",
        "page": 4,
        "chunk_index": 3
    }
}
```

其中：

```text
content
```

是 Chunk 的实际文本。

```text
metadata
```

记录 Chunk 的来源信息。

---

# 五、为什么 RAG 需要 Chunk？

Chunk 的主要作用是：

> **让知识库中的信息拥有更合理的检索粒度。**

如果 Chunk 太大：

```text
一个 Chunk
包含很多不同主题
```

那么检索粒度比较粗。

如果 Chunk 太小：

```text
一个完整知识
被拆成很多碎片
```

又可能导致上下文不完整。

因此 Chunking 的核心目标是：

```text
保证语义完整
        +
控制检索粒度
```

---

# 六、chunk_size

`chunk_size` 用来控制：

> **一个 Chunk 大概有多大。**

例如：

```python
chunk_size = 500
```

可以简单理解为：

```text
原始文本

 ↓

约 500 字符

Chunk 1

 ↓

约 500 字符

Chunk 2

 ↓

约 500 字符

Chunk 3
```

---

# 七、chunk_size 太小

例如：

```python
chunk_size = 50
```

一个法律条文可能被拆成：

```text
Chunk 1:
全国人民代表大会和全国人民代表大会常务委员会

Chunk 2:
行使国家立法权。全国人民代表大会制定和修改

Chunk 3:
刑事、民事、国家机构的和其他的基本法律。
```

完整语义被拆开。

可能造成：

```text
语义不完整
   ↓
Embedding 表达不完整
   ↓
检索效果下降
```

---

# 八、chunk_size 太大

例如：

```python
chunk_size = 5000
```

一个 Chunk 可能包含：

```text
第五条……
第六条……
第七条……
第八条……
第九条……
第十条……
……
第二十条……
```

一个 Chunk 里面包含大量不同主题。

这样：

```text
检索粒度变粗
```

同时送给 LLM 的 Context 也会变大。

---

# 九、chunk_overlap

`chunk_overlap` 表示：

> **相邻 Chunk 之间重复保留多少内容。**

例如：

```python
chunk_size = 500
chunk_overlap = 50
```

可以理解为：

```text
Chunk 1
0 ───────────── 500

Chunk 2
        450 ───────────── 950

Chunk 3
                  900 ───────────── 1400
```

相邻 Chunk 之间存在：

```text
50
```

左右的重叠区域。

---

# 十、为什么需要 overlap？

假设原始文本：

```text
A B C D E F G H I J
```

如果完全不重叠：

```text
Chunk 1:
A B C D E

Chunk 2:
F G H I J
```

如果一个完整语义刚好位于：

```text
E → F
```

这个语义就可能被切断。

加入 overlap 后：

```text
Chunk 1:
A B C D E F

Chunk 2:
E F G H I J
```

这样可以减少：

> **重要语义恰好被切断的问题。**

---

# 十一、Metadata

Chunk 不应该只有：

```python
{
    "content": "..."
}
```

通常还需要：

```python
{
    "content": "...",

    "metadata": {
        "source": "中华人民共和国立法法.pdf",
        "page": 4,
        "chunk_index": 3
    }
}
```

Metadata 可以用于：

* 找到原始文档
* 找到页码
* 定位 Chunk
* 调试
* 展示引用来源
* 后续过滤检索结果

例如 Retriever 找到：

```text
Chunk 3
```

我们可以进一步知道：

```text
来源：
中华人民共和国立法法.pdf

页码：
4

Chunk：
3
```

---

# 十二、Chunk 与 Embedding

Chunk 完成后，需要进行 Embedding。

例如：

```text
Chunk 0
Chunk 1
Chunk 2
Chunk 3
```

经过 Embedding：

```text
Vector 0
Vector 1
Vector 2
Vector 3
```

它们需要保持对应关系：

```text
Chunk 0 ←→ Vector 0
Chunk 1 ←→ Vector 1
Chunk 2 ←→ Vector 2
Chunk 3 ←→ Vector 3
```

因此：

> **一个 Chunk 通常对应一个 Embedding Vector。**

---

# 十三、Chunk 与 Vector Store

Embedding 后：

```text
Chunks
   ↓
Embedding
   ↓
Vectors
   ↓
FAISS
```

例如：

```text
Chunk 0 → Vector 0
Chunk 1 → Vector 1
Chunk 2 → Vector 2
Chunk 3 → Vector 3
```

FAISS 保存的是向量索引。

当查询：

```text
全国人民代表大会有哪些立法权？
```

时：

```text
Query
 ↓
Query Embedding
 ↓
FAISS
 ↓
找到最相似的 Vector
 ↓
根据 Vector 找回对应 Chunk
```

---

# 十四、当前项目实际情况

我们的《中华人民共和国立法法》测试数据：

```text
PDF
 ↓
Document Parser
 ↓
Document
 ↓
Document Splitter
 ↓
58 个 Chunk
 ↓
Embedding
 ↓
58 个 Vector
 ↓
FAISS
```

运行结果：

```text
Chunk 数量: 58
FAISS Vector 数量: 58
```

说明：

```text
58 个 Chunk
      ↓
58 个 Embedding Vector
      ↓
58 个 FAISS Index
```

整个数据链路已经跑通。

---

# 十五、Retriever

Retriever 的任务非常简单：

> **根据用户的问题，从 Vector Store 中找到最相关的 Chunk。**

例如：

```text
Question:

全国人民代表大会有哪些立法权？
```

Retriever 返回：

```text
Top 1 → Chunk 27
Top 2 → Chunk 47
Top 3 → Chunk 22
Top 4 → Chunk 3
Top 5 → Chunk 52
```

其中：

```text
Chunk 3
```

才是真正包含相关内容的 Chunk。

---

# 十六、为什么需要评估 Retriever？

仅仅看到：

```python
results = retriever.retrieve(query)
```

成功返回结果，并不能说明 Retriever 好。

我们需要知道：

```text
有没有找到正确 Chunk？

正确 Chunk 排在第几？

Top-K 是否足够？

修改 Chunking 后有没有变好？
```

所以需要：

> **Retrieval Evaluation**

---

# 十七、Ground Truth

Evaluation 需要先知道：

> **什么是正确答案？**

例如：

```text
Question:

全国人民代表大会有哪些立法权？
```

我们人工确认：

```text
Relevant Chunk:
Chunk 3
```

于是：

```python
{
    "question":
        "全国人民代表大会有哪些立法权？",

    "relevant_chunk_ids": [
        3
    ]
}
```

这里：

```text
relevant_chunk_ids
```

就是 Ground Truth 的一部分。

---

# 十八、为什么之前的关键词 Recall 不够准确？

最开始可以使用：

```python
expected_keywords = [
    "全国人民代表大会",
    "制定",
    "修改",
    "基本法律"
]
```

然后判断：

```python
keyword in content
```

例如：

```text
Matched:
[
    "全国人民代表大会",
    "制定",
    "修改",
    "基本法律"
]

Recall:
1.0
```

这种方法可以用于非常简单的测试。

但是它不能真正判断：

> **Retriever 找到的 Chunk 是否是正确的 Chunk。**

因为：

```text
关键词匹配
```

和：

```text
语义相关
```

并不是完全相同的事情。

因此，我们进一步使用：

```text
Recall@K
MRR
```

来评估 Retriever。

---

# 十九、Recall@K

Recall@K 可以简单理解为：

> **正确 Chunk 有没有出现在前 K 个结果里面。**

例如：

```text
正确 Chunk：

Chunk 3
```

Retriever：

```text
Top 1 → Chunk 27
Top 2 → Chunk 47
Top 3 → Chunk 22
Top 4 → Chunk 3
Top 5 → Chunk 52
```

那么：

```text
Recall@1 = 0

Recall@3 = 0

Recall@5 = 1
```

因为：

```text
Top 1
没有找到

Top 3
没有找到

Top 5
找到了
```

---

# 二十、如何理解 K？

K 可以理解为：

> **我们允许 Retriever 返回多少个候选结果。**

例如：

```text
Recall@1
```

表示：

> 看第一名。

```text
Recall@3
```

表示：

> 看前三名。

```text
Recall@5
```

表示：

> 看前五名。

所以：

```text
Recall@K
```

实际上是在问：

> **正确内容有没有进入前 K 个候选结果？**

---

# 二十一、为什么 Recall@K 对 RAG 很重要？

因为 RAG 通常不是只检索一个 Chunk：

```text
Query
 ↓
Retriever
 ↓
Top-K
 ↓
Context
 ↓
LLM
```

例如：

```text
Top 5
 ↓
Context
 ↓
LLM
```

只要正确 Chunk 进入 Top 5：

```text
Recall@5 = 1
```

那么 LLM 就有机会看到正确知识。

所以：

> **Retriever 的第一目标之一，就是不要把真正相关的知识漏掉。**

---

# 二十二、多个 Relevant Chunk

现实中一个问题可能对应多个 Chunk。

例如：

```text
Question:

立法应当遵循哪些原则？
```

可能认为：

```text
Chunk 2
Chunk 22
```

都具有相关性。

那么：

```python
{
    "relevant_chunk_ids": [
        2,
        22
    ]
}
```

假设 Retriever：

```text
Top 1 → Chunk 27
Top 2 → Chunk 22
Top 3 → Chunk 8
Top 4 → Chunk 2
Top 5 → Chunk 51
```

那么：

```text
Recall@1 = 0 / 2 = 0

Recall@3 = 1 / 2 = 0.5

Recall@5 = 2 / 2 = 1.0
```

因此 Recall@K 还可以衡量：

> **多个相关 Chunk 被召回了多少。**

---

# 二十三、MRR

Recall@K 有一个不足：

它只关心：

```text
有没有找到？
```

但是不关心：

```text
排第几？
```

例如：

```text
情况 A：

Top 1 → 正确
```

和：

```text
情况 B：

Top 5 → 正确
```

它们的：

```text
Recall@5
```

都可能是：

```text
1.0
```

但显然：

```text
Top 1
```

比：

```text
Top 5
```

更好。

因此可以使用：

> **MRR（Mean Reciprocal Rank）**

---

# 二十四、Reciprocal Rank

先理解单个问题的 Reciprocal Rank。

公式：

```text
RR = 1 / 正确结果的排名
```

例如：

```text
正确结果 Top 1

RR = 1 / 1
   = 1.0
```

```text
正确结果 Top 2

RR = 1 / 2
   = 0.5
```

```text
正确结果 Top 3

RR = 1 / 3
   ≈ 0.333
```

```text
正确结果 Top 5

RR = 1 / 5
   = 0.2
```

如果没有找到：

```text
RR = 0
```

---

# 二十五、MRR 的直觉

MRR 可以简单理解为：

> **正确答案平均排得有多靠前。**

MRR 越高：

```text
正确结果通常排得越靠前
```

MRR 越低：

```text
正确结果通常排得越靠后
```

对于单个问题：

```text
MRR = RR
```

对于多个问题：

```text
MRR = 所有问题 RR 的平均值
```

---

# 二十六、结合当前实验

你的测试：

```text
Question:

全国人民代表大会有哪些立法权？
```

Retriever：

```text
Top 1 → Chunk 27
Top 2 → Chunk 47
Top 3 → Chunk 22
Top 4 → Chunk 3  ← 正确
Top 5 → Chunk 52
```

正确 Chunk 排名：

```text
4
```

因此：

```text
MRR = 1 / 4
    = 0.25
```

同时：

```text
Recall@1 = 0
Recall@3 = 0
Recall@5 = 1
```

这说明：

> Retriever 能够在 Top-5 找到正确 Chunk，但没有把它排到 Top-3 以内。

---

# 二十七、Recall@K 与 MRR 的区别

| 指标       | 关注的问题       |
| -------- | ----------- |
| Recall@1 | 第一名有没有正确结果？ |
| Recall@3 | 前三名有没有正确结果？ |
| Recall@5 | 前五名有没有正确结果？ |
| MRR      | 第一个正确结果排第几？ |

可以这样记：

```text
Recall@K
    ↓
有没有找到？

MRR
    ↓
排得靠不靠前？
```

---

# 二十八、为什么两个指标最好一起看？

例如方案 A：

```text
Recall@5 = 1.0
MRR = 0.25
```

说明：

```text
能找到
但是排得比较靠后
```

方案 B：

```text
Recall@5 = 1.0
MRR = 0.80
```

说明：

```text
也能找到
而且通常排得很靠前
```

所以方案 B 的 Retriever 排序质量更好。

---

# 二十九、Evaluation 的工程意义

以后我们修改：

```text
Chunk Size
Chunk Overlap
Embedding Model
Retriever
Top-K
```

都可以重新跑 Evaluation。

例如：

```text
方案 A

Recall@5 = 0.72
MRR = 0.41
```

修改 Chunking 后：

```text
方案 B

Recall@5 = 0.91
MRR = 0.67
```

那么我们就有数据说明：

```text
方案 B
```

在当前测试集上的检索效果更好。

而不是仅凭感觉判断。

---

# 三十、当前阶段不需要学习的指标

RAG Evaluation 后面还有很多指标：

```text
Precision
F1
MAP
nDCG
Hit Rate
LLM-as-a-Judge
Semantic Evaluation
```

这些目前不需要全部学习。

当前阶段掌握：

```text
Recall@K
MRR
```

已经足够理解 Retriever Evaluation 的基本思想。

---

# 三十一、不同文档可能需要不同的 Chunking

固定字符切割：

```text
chunk_size
chunk_overlap
```

非常适合当前学习项目。

但真实项目中，不同文档可能需要不同策略。

例如：

### TXT

可以按照：

```text
字符
段落
Token
```

进行切割。

### Markdown

可以按照：

```text
标题
章节
段落
```

进行切割。

### HTML

可以考虑：

```text
DOM
标题
正文区域
```

### 小说

可以按照：

```text
章节
段落
```

### 法律文档

可以进一步按照：

```text
章节
条
款
```

进行切割。

因此：

> **Chunking 没有一个适用于所有文档的固定方案。**

---

# 三十二、为什么当前使用简单 Chunking？

我们的目标是：

> **先理解 RAG 的完整工作流程。**

所以当前使用：

```python
chunk_size = 500
chunk_overlap = 50
```

已经足够。

当前不需要马上实现：

```text
语义切割
法律条文解析
Markdown AST
Token-aware Splitter
复杂 Recursive Splitter
```

这些属于后续优化内容。

---

# 三十三、当前项目应该掌握到什么程度？

目前只需要真正理解：

```text
Document
   ↓
Chunk
   ↓
Embedding
   ↓
Vector
   ↓
Vector Store
   ↓
Retriever
   ↓
Top-K
```

以及：

```text
chunk_size
chunk_overlap
metadata
Recall@K
MRR
```

---

# 三十四、完整知识链路

把整个知识串起来：

```text
                【知识库构建】

PDF
 │
 ▼
Document Parser
 │
 ▼
Document
 │
 ▼
Document Splitter
 │
 ├── chunk_size
 ├── chunk_overlap
 └── metadata
 │
 ▼
Chunks
 │
 ▼
Embedding
 │
 ▼
Vectors
 │
 ▼
FAISS
```

用户查询：

```text
                【检索阶段】

User Question
 │
 ▼
Embedding
 │
 ▼
Query Vector
 │
 ▼
FAISS
 │
 ▼
Retriever
 │
 ▼
Top-K Chunks
```

评估：

```text
Top-K
 │
 ▼
Ground Truth
 │
 ├── Recall@K
 │
 └── MRR
```

最终 RAG：

```text
User Question
      │
      ▼
   Retriever
      │
      ▼
 Relevant Chunks
      │
      ▼
    Context
      │
      ▼
      LLM
      │
      ▼
   Final Answer
```

---

# 三十五、核心知识总结

## 1. Chunk 是什么？

> 从 Document 中切出来的、用于独立检索的文本块。

---

## 2. chunk_size 是什么？

> 控制 Chunk 大小。

---

## 3. chunk_overlap 是什么？

> 控制相邻 Chunk 之间重复保留多少内容。

---

## 4. Metadata 是什么？

> 保存 Chunk 的来源和其他辅助信息。

---

## 5. Retriever 是什么？

> 根据用户 Query 找到最相关的 Chunk。

---

## 6. Recall@K 是什么？

> 判断正确 Chunk 是否进入前 K 个检索结果。

---

## 7. MRR 是什么？

> 衡量正确结果排得有多靠前。

---

# 三十六、一句话记忆

整个知识可以浓缩成：

```text
Document
   ↓
切成 Chunk
   ↓
Embedding
   ↓
Vector Store
   ↓
Retriever
   ↓
Top-K
```

然后用：

```text
Recall@K
    ↓
有没有找到？

MRR
    ↓
排得靠不靠前？
```

最终：

> **文档切割解决“知识应该以什么粒度进入向量库”，Retriever 解决“应该找哪些知识”，Recall@K 和 MRR 解决“我们找得怎么样”。**

---

# 三十七、当前学习进度

当前 RAG 基础链路已经完成：

```text
Document Parser       ✅
Document Cleaner      ✅
Document Splitter    ✅
Embedding             ✅
FAISS Vector Store   ✅
Retriever             ✅
基础 Evaluation       ✅
```

下一阶段：

```text
Retriever
    ↓
Context Builder
    ↓
Prompt
    ↓
LLM
    ↓
RAG Pipeline
```

也就是把目前已经完成的：

```text
Parser
Splitter
Embedding
FAISS
Retriever
```

真正连接起来，完成一个完整的 RAG 系统。

---

# 最终目标

最终我们希望实现：

```python
answer = rag.query(
    "全国人民代表大会有哪些立法权？"
)
```

系统内部：

```text
问题
 ↓
Retriever
 ↓
找到相关 Chunk
 ↓
Context
 ↓
Prompt
 ↓
LLM
 ↓
答案
```