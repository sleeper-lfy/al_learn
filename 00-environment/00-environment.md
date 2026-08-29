# 00-environment · 自学笔记

> 2026-08-26 ｜ 环境链路跑通 ✅

## 目标

- [x] Ollama 服务可用（本机 `:11434`）
- [x] 模型可加载（`modelscope.cn/Qwen/Qwen3-1.7B-GGUF`）
- [x] 最小 HTTP 闭环：发 JSON、收 JSON、拿到 `response`

## 环境与实测数据

`ollama list` 当前模型：

```text
qwen3.5-agent:latest
modelscope.cn/Qwen/Qwen3-1.7B-GGUF:latest
modelscope.cn/nomic-ai/nomic-embed-text-v1.5-GGUF:latest   # embedding，RAG 备用
```

几个值得记录的观察（都是实际跑出来的数字）：

| 观察 | 数据 | 说明 |
| --- | --- | --- |
| 冷启动 | 首请求端到端 ~20s | 模型加载进显存占大头 |
| 热态短问答 | 端到端 6.8s，其中 eval 仅 0.8s | 89 token，~107 tok/s；剩余基本是加载/调度 |
| 响应元数据 | `context` / `thinking` / `load_duration` / `prompt_eval_count` / `eval_duration` / `done_reason` | 不止 `response` 一个字段 |

`thinking` 字段值得单独记一笔：Qwen3 系默认带推理，最终答案在 `response`，
推理过程在 `thinking`。后面做 Agent 时，“要不要把推理过程透出给用户”是个真实的产品决策。

## 代码（hello_llm.py）

保持单文件、单请求——这一步的定位是确认链路，不是写客户端。

```python
"""hello_llm.py：验证 Ollama 环境的最小示例。"""

import requests
import sys

# ========== 配置区：换模型、换提示词时改这里就行 ==========
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"  # 模型名（全名）
PROMPT = "天空为什么是蓝色的？"
TIMEOUT = 60  # 超时秒数，避免服务没响应时程序一直卡住

if __name__ == "__main__":
    # 1. 构造请求体：告诉 Ollama 用哪个模型、问什么问题、要不要流式
    payload = {
        "model": MODEL,
        "prompt": PROMPT,
        "stream": False,  # False = 等模型生成完一次性返回
    }

    # 2. 发送请求
    try:
        response = requests.post(OLLAMA_URL, json=payload, timeout=TIMEOUT)
    except requests.exceptions.ConnectionError:
        print("无法连接 Ollama，请先运行 `ollama serve` 或打开 Ollama 应用。")
        sys.exit(1)
    except requests.exceptions.Timeout:
        print(f"请求超时（超过 {TIMEOUT} 秒）。模型较大时首次加载慢，可调大 TIMEOUT。")
        sys.exit(1)

    # 3. 处理响应：200 说明成功，否则打印错误信息
    if response.status_code == 200:
        result = response.json()
        print(result["response"])
    else:
        print(f"请求失败，状态码：{response.status_code}")
        print(response.text)
        if response.status_code == 404:
            print("模型不存在：`ollama list` 查看已安装模型，`ollama pull <模型名>` 下载。")
```

## 技术要点

1. **`stream=False` 是“服务端流完再返回”，不是没有流。**
   底层仍是逐 token 生成，只是 API 聚合了。代价是拿不到首 token 延迟，
   Agent 场景要“边想边说”，必须 `stream=True` + NDJSON 逐行解析。

2. **错误语义要三分，重试策略完全不同。**
   `ConnectionError`（服务没起/端口不对）→ 可退避重试；
   `Timeout` → 和冷启动强耦合，先搞清楚是加载慢还是真卡死；
   HTTP 404 → 模型名不存在，**重试无意义**，直接给 `ollama list/pull` 提示。
   这次 404 分支是特意留的：错误信息值不值得写，取决于它能不能让调用方少查一次文档。

3. **timeout 要按预算设计，不是拍脑袋。**
   冷启动 20s 的现状下，`timeout=10` 会把正常首请求误杀。
   合理做法是区分“首次请求预算（含加载）”和“热态请求预算”，
   或先做一次预热请求。60s 这个值只是当前够用，不是答案。

4. **模型名匹配必须归一化。**
   `ollama list` 输出带 `:latest`，配置里通常写裸名，
   直接字符串比较会误判“未安装”。自检/工具代码要按
   `name if ":" in name else f"{name}:latest"` 处理。这是真坑。

5. **未来抽象点（现在不做，先记下）。**
   这个 demo 已经能看出客户端的形状：
   config（`keep_alive`、`options`、超时预算）、client（重试/退避/流式解析）、
   CLI（模型/提示词参数化）。等 02 章被真正复用时再抽，避免第一课就过度设计。

## 疑问 / 待探索

- [ ] `keep_alive` 默认多久？模型何时被卸载？`ollama ps` 能看到驻留状态吗？
- [ ] `/api/chat` vs `/api/generate`：chat 走对话模板 + system prompt，语义差异在哪？
- [ ] `options.num_ctx` 怎么配？上下文窗口和显存占用怎么权衡？
- [ ] 这个 GGUF 文件是什么量化等级（Q4_K_M / Q8）？对质量和速度的影响？
- [ ] Ollama 有没有 OpenAI 兼容端点（`/v1/chat/completions`）？
      后面接 LangChain 时可能只需要换 `base_url`。
- [ ] 同模型并发请求是排队还是并行？和 Agent 多工具并发相关。

## 下一步

`01-llm-basics`：同一个 `generate` 调用，进入提示词工程——
prompt 的结构、角色设定、few-shot 如何改变输出。
