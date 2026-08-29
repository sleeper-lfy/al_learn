"""hello-lang-graph.py：LangGraph Agent 最小示例。

一个文件演示 LangGraph 的四个核心能力：
1. 工具调用：模型自己决定调 get_user_location / get_weather_for_location；
2. 多步协作：用户没给位置 -> 先按 user_id 查位置 -> 再查天气；
3. 结构化输出：response_format 让模型按 ResponseFormat 结构返回；
4. 会话记忆：checkpointer + thread_id，同一会话能记住上一轮。

运行：
    python hello-lang-graph.py
"""

from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

MODEL = "ollama:modelscope.cn/Qwen/Qwen3-1.7B-GGUF"

SYSTEM_PROMPT = """你是一位擅长用双关语的天气预报员。
决策规则：
1. 用户问天气：必须调用 get_weather_for_location。
2. 用户没提供位置：先用 get_user_location 查用户位置，再查天气。
3. 用户已提供位置：不要再调用 get_user_location。
4. 闲聊：不要调用任何工具，直接用 ResponseFormat 结构回答
   （punny_response 填寒暄内容，weather_conditions 保持 None）。"""


@dataclass
class Context:
    """自定义运行时上下文：跨调用传给工具的附加信息（如 user_id）。"""

    user_id: str


@dataclass
class ResponseFormat:
    """结构化输出：模型必须按这个结构返回。"""

    punny_response: str  # 带双关语的回答（必需）
    weather_conditions: str | None = None  # 天气信息（如果有）


@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"


@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 获取用户位置。"""
    user_id = runtime.context.user_id
    return "Florida" if user_id == "1" else "San Francisco"


def build_agent():
    """组装 Agent：模型 + 提示词 + 工具 + 结构化输出 + 记忆。"""
    model = init_chat_model(MODEL, temperature=0.5, timeout=120, max_tokens=1000)
    return create_agent(
        model=model,
        system_prompt=SYSTEM_PROMPT,
        tools=[get_user_location, get_weather_for_location],
        context_schema=Context,
        response_format=ResponseFormat,
        checkpointer=InMemorySaver(),
    )


if __name__ == "__main__":
    agent = build_agent()
    config = {"configurable": {"thread_id": "1"}}

    # 第一轮：没给位置 -> 模型应自动两步走（先查位置，再查天气）
    reply = agent.invoke(
        {"messages": [{"role": "user", "content": "外面的天气怎么样？"}]},
        config=config,
        context=Context(user_id="1"),
    )
    print("== 第一轮（结构化响应）==")
    print(reply["structured_response"])

    # 第二轮：同一 thread_id，模型记得刚才聊过天气
    reply = agent.invoke(
        {"messages": [{"role": "user", "content": "谢谢！"}]},
        config=config,
        context=Context(user_id="1"),
    )
    print("== 第二轮（验证记忆）==")
    structured = reply["structured_response"]
    print(structured if structured is not None else reply["messages"][-1].content)
