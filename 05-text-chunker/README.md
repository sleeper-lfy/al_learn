# RAG 文档处理

> RAG（Retrieval-Augmented Generation，检索增强生成）的第一步不是 Embedding，而是把原始文档加工成适合检索的知识块。

## 一、整体流程

```text
原始文档
   │
   ▼
Document Parser
   │
   ▼
Document
   │
   ▼
Document Cleaner
   │
   ▼
Clean Document
   │
   ▼
Document Merger
   │
   ▼
Full Document
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
```

---

## 二、为什么需要文档处理？

LLM 不能直接把一个几十 MB 的 PDF 当成一个知识单元进行高质量检索。

例如：

```text
中华人民共和国立法法.pdf
```

可能包含大量：

* 章节
* 条文
* 段落
* 页码
* 页眉
* 页脚
* 格式信息

因此需要：

```text
PDF
 ↓
解析
 ↓
清洗
 ↓
结构化
 ↓
切片
 ↓
Embedding
```

---

## 三、核心概念

### Document

表示一个可以被 RAG 系统处理的文档对象。

```python
Document(
    content="第一条……",
    metadata={
        "source": "立法法.pdf",
        "page": 1
    }
)
```

其中：

```text
content
    文档正文

metadata
    文档的附加信息
```

---

### Chunk

Chunk 是经过切分后的知识块。

```text
Document
    ↓
Chunk 1
Chunk 2
Chunk 3
...
```

Chunk 是最终进行 Embedding 和向量检索的基本单位。

---

## 四、为什么 Chunking 很重要？

如果切片不合理：

```text
一个完整语义
        ↓
被拆成两个 Chunk
```

那么：

```text
Embedding
 ↓
向量表示
 ↓
检索
```

都可能受到影响。

所以 Chunking 的核心目标不是：

> 把文本平均切成 N 段。

而是：

> 尽可能保持语义完整，同时控制 Chunk 大小。

---

## 五、不同文档应该使用不同策略

| 文档类型     | 推荐结构                          |
| -------- | ----------------------------- |
| 小说       | 章节 → 段落 → 句子                  |
| 法律       | 编 → 章 → 节 → 条 → 款             |
| 技术文档     | Header → Section → Paragraph  |
| Markdown | Header → Section              |
| 代码       | Class → Function → Code Block |
| FAQ      | Question → Answer             |

因此：

```text
Chunking ≠ 固定 500 字切一次
```

而是一个数据工程问题。

---

## 六、本项目

本项目使用：

```text
《中华人民共和国立法法》
```

作为 RAG 文档处理实验数据。

最终目标：

```text
立法法.pdf
 ↓
PDF Parser
 ↓
Cleaner
 ↓
Merger
 ↓
Legal Text Splitter
 ↓
Article Chunks
 ↓
Embedding
 ↓
Vector Database
```

最终得到：

```python
Document(
    content="第一百条……",
    metadata={
        "document_id": "doc_001",
        "source": "中华人民共和国立法法.pdf",
        "article": "第一百条",
        "start_page": 20,
        "end_page": 21
    }
)
```

这就是后续进入 Embedding 的基本数据。
