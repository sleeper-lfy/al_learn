"""call_llm_stream.py：流式输出（Streaming）。

对应学习点：Streaming。

- stream=True 后，Ollama 按 NDJSON 逐行返回增量，每行是一个 chunk
- 关键字段：chunk["message"]["content"] 是本次增量，chunk["done"] 表示结束
- 流式的价值：首 token 延迟低，Agent 可以“边想边说”
"""

import json
import time

import requests

URL = "http://localhost:11434/api/chat"
MODEL = "modelscope.cn/Qwen/Qwen3-1.7B-GGUF"
TIMEOUT = 120

payload = {
    "model": MODEL,
    "messages": [
        {"role": "system", "content": "你是 Python 专家，回答要简洁。"},
        {"role": "user", "content": "递归和迭代的区别？"},
    ],
    "stream": True,
}

start = time.perf_counter()
pieces = 0

with requests.post(URL, json=payload, stream=True, timeout=TIMEOUT) as response:
    response.raise_for_status()
    for line in response.iter_lines(decode_unicode=True):
        if not line:
            continue
        chunk = json.loads(line)
        piece = chunk["message"]["content"]
        if piece:
            pieces += 1
            print(piece, end="", flush=True)
        if chunk.get("done"):
            eval_count = chunk.get("eval_count") or 0  # 结束帧里的真实 token 数
            elapsed = time.perf_counter() - start
            print(
                f"\n\n[完成] 网络片段 {pieces} 个，模型实际生成 {eval_count} tokens，"
                f"耗时 {elapsed:.1f}s，约 {eval_count / elapsed:.1f} tok/s"
            )

# 对比：stream=False 时，这些 chunk 会被服务端聚合成一个完整 response
