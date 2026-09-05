from typing import Annotated
from typing_extensions import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.store.memory import InMemoryStore


# =========================
# 1. Thread 的 State
# =========================

class State(TypedDict):
    messages: Annotated[list, add_messages]


# =========================
# 2. Memory
# =========================

memory = InMemoryStore()


# =========================
# 3. 模拟 Chatbot
# =========================

def chatbot(state: State):
    messages = state["messages"]

    last_message = messages[-1]

    user_text = last_message.content

    # 模拟 AI
    if "我叫" in user_text:
        name = user_text.replace("我叫", "").strip()

        return {"messages": [{"role": "assistant", "content": f"你好，{name}！"}]}

    if "学习" in user_text:
        return {"messages": [{"role": "assistant", "content": "好的，我知道你正在学习这个东西了。"}]}

    if "我叫什么" in user_text:
        # 从 Memory 查询
        user_memory = memory.get(("user", "user-001"), "profile")

        if user_memory:
            name = user_memory.value.get("name")

            return {"messages": [{"role": "assistant", "content": f"你叫{name}。"}]}

        return {"messages": [{"role": "assistant", "content": "我还不知道你的名字。"}]}

    return {"messages": [{"role": "assistant", "content": "好的，我知道了。"}]}


if __name__ == '__main__':
    # =========================
    # 4. 创建 Graph
    # =========================

    builder = StateGraph(State)

    builder.add_node("chatbot", chatbot)

    builder.add_edge(START, "chatbot")
    builder.add_edge("chatbot", END)

    # =========================
    # 5. Checkpoint
    # =========================

    checkpointer = InMemorySaver()
    graph = builder.compile(checkpointer=checkpointer, )

    # =========================
    # 6. Thread 001
    # =========================

    thread_001 = {"configurable": {"thread_id": "thread-001"}}

    print("========== Thread 001 ==========")

    result = graph.invoke({"messages": [{"role": "user", "content": "我叫张三"}]}, config=thread_001)

    print(result["messages"])

    # =========================
    # 7. 把信息保存到 Memory
    # =========================

    memory.put(("user", "user-001"), "profile", {"name": "张三", "interest": "LangGraph"})

    # Thread 001 第二次对话

    result = graph.invoke({"messages": [{"role": "user", "content": "我正在学习 LangGraph"}]}, config=thread_001)

    print(result["messages"])

    # =========================
    # 8. 创建新的 Thread
    # =========================

    thread_002 = {"configurable": {"thread_id": "thread-002"}}

    print("========== Thread 002 ==========")

    result = graph.invoke({"messages": [{"role": "user", "content": "我叫什么"}]}, config=thread_002)

    print(result["messages"])
