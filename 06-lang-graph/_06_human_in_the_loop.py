from typing import TypedDict

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.types import interrupt, Command


class State(TypedDict):
    action: str
    approved: bool


# =========================
# Node 1
# 准备操作
# =========================

def prepare(state: State):
    print("准备执行操作：", state["action"])

    return {}


# =========================
# Node 2
# 人工审核
# =========================

def human_review(state: State):
    result = interrupt({"message": "是否允许执行这个操作？", "action": state["action"]})

    return {"approved": result}


# =========================
# Node 3
# 执行操作
# =========================

def execute(state: State):
    if state["approved"]:
        print("✅ 执行操作：", state["action"])
    else:
        print("❌ 操作被拒绝")

    return {}


if __name__ == '__main__':
    # =========================
    # Graph
    # =========================

    builder = StateGraph(State)

    builder.add_node("prepare", prepare)
    builder.add_node("human_review", human_review)
    builder.add_node("execute", execute)

    builder.add_edge(START, "prepare")
    builder.add_edge("prepare", "human_review")
    builder.add_edge("human_review", "execute")
    builder.add_edge("execute", END)

    # =========================
    # Checkpoint
    # =========================

    checkpointer = InMemorySaver()

    graph = builder.compile(checkpointer=checkpointer)
    config = {"configurable": {"thread_id": "approval-001"}}

    result = graph.invoke({"action": "删除用户数据", "approved": False}, config=config)

    print(result)

    graph.invoke(Command(resume=True), config=config)
