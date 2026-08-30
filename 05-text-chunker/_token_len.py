import requests


def get_token_count(text, model_name="qwen3:1.7b"):
    """通过 Ollama API 获取输入文本的 token 数量"""
    try:
        response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": model_name,  # 使用正确的模型名称
                "prompt": text,
                "stream": False
            },
            timeout=100
        )

        if response.status_code == 200:
            result = response.json()
            # prompt_eval_count 表示输入的 token 数量
            token_count = result.get("prompt_eval_count", 0)

            # 打印详细信息（调试用）
            print(f"完整响应: {result}")
            print(f"生成内容: {result.get('response', '')[:50]}...")  # 只显示前50个字符

            return token_count
        else:
            print(f"API 调用失败: {response.status_code}")
            print(f"错误信息: {response.text}")
            return None
    except Exception as e:
        print(f"请求异常: {e}")
        return None


# 使用示例
text = """ 人工智能是一门研究如何让机器表现出智能行为的技术。 RAG 是一种检索增强生成技术，可以让大语言模型访问外部知识。 """
token_count = get_token_count(text, "qwen3:1.7b")

print(f"\n输入文本: {text}")
print(f"Token 数量: {token_count}")