"""hello_llm.py：验证 Ollama 环境的最小示例。

运行前请确保：
1. Ollama 已启动：运行 `ollama serve`，或打开 Ollama 桌面应用；
2. 模型已下载：`ollama list` 可查看本机已安装的模型。
"""

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

    # 2. 发送请求。timeout 是必须的：没有它，Ollama 没响应时会一直等下去
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
