"""临时诊断：对比两个模型的结构化输出稳定性，跑完即删。"""

import sys
from dataclasses import dataclass

from langchain.agents import create_agent
from langchain.chat_models import init_chat_model
from langchain.tools import tool, ToolRuntime
from langgraph.checkpoint.memory import InMemorySaver

MODEL = sys.argv[1]

SYSTEM_PROMPT = """你是一位擅长用双关语的天气预报员。
决策规则：
1. 用户问天气：必须调用 get_weather_for_location。
2. 用户没提供位置：先用 get_user_location 查用户位置，再查天气。
3. 用户已提供位置：不要再调用 get_user_location。
4. 闲聊：不要调用任何工具，直接用 ResponseFormat 结构回答。"""


@dataclass
class Context:
    user_id: str


@dataclass
class ResponseFormat:
    punny_response: str
    weather_conditions: str | None = None


@tool
def get_weather_for_location(city: str) -> str:
    """获取指定城市的天气。"""
    return f"{city}总是阳光明媚！"


@tool
def get_user_location(runtime: ToolRuntime[Context]) -> str:
    """根据用户 ID 获取用户位置。"""
    return "Florida" if runtime.context.user_id == "1" else "San Francisco"


agent = create_agent(
    model=init_chat_model(MODEL, temperature=0.5, timeout=120, max_tokens=1000),
    system_prompt=SYSTEM_PROMPT,
    tools=[get_user_location, get_weather_for_location],
    context_schema=Context,
    response_format=ResponseFormat,
    checkpointer=InMemorySaver(),
)

config = {"configurable": {"thread_id": "1"}}
reply = agent.invoke(
    {"messages": [{"role": "user", "content": "外面的天气怎么样？"}]},
    config=config,
    context=Context(user_id="1"),
)

print("keys:", list(reply.keys()))
print("structured type:", type(reply["structured_response"]).__name__)
print("structured:", repr(reply["structured_response"])[:300])
for msg in reply["messages"]:
    print(f"MSG {msg.type}: {str(msg.content)[:180]}")
