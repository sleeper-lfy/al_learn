from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver


# 1. 定义 State
class State(TypedDict):
    count: int


# 2. 定义 Node
def increment(state: State, config):
    print("--- 1. 节点接收到的 config ---")
    print(f"Config Metadata: {config.get('metadata')}")
    return {"count": state["count"] + 1}


if __name__ == '__main__':
    # 3. 创建 Graph
    builder = StateGraph(State)

    builder.add_node("increment", increment)

    builder.add_edge(START, "increment")
    builder.add_edge("increment", END)

    # 4. 创建 Checkpointer
    # graph.invoke()
    # ↓
    # Graph
    # 执行
    # ↓
    # 多个步骤
    # ↓
    # State
    # 不断变化
    # ↓
    # 产生
    # Checkpoint
    checkpointer = InMemorySaver()

    graph = builder.compile(checkpointer=checkpointer)

    # 5. 指定 Thread
    config = {"configurable": {"thread_id": "user-001"}}

    # 6. 第一次执行
    result1 = graph.invoke({"count": 0}, config=config)


    print("第一次：", result1)

    result1 = graph.invoke({"count": 0}, config=config)

    state = graph.get_state(config)

    print("Checkpoint：", state.values)

    print("第二次：", result1)

    # 7. 查看当前 State
    state = graph.get_state(config)

    print("Checkpoint：", state.values)

    result1 = graph.invoke(None, config=config)

    for state in graph.get_state_history(config):
        print(state)
