from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    message: str


def node_a(state: State):
    print("执行 A")
    return {"message": state["message"] + " → A"}


def node_b(state: State):
    print("执行 B")
    return {"message": state["message"] + " → B"}


def node_c(state: State):
    print("执行 C")
    return {"message": state["message"] + " → C"}


builder = StateGraph(State)

builder.add_node("a", node_a)
builder.add_node("b", node_b)
builder.add_node("c", node_c)

builder.add_edge(START, "a")
builder.add_edge("a", "b")
builder.add_edge("b", "c")
builder.add_edge("b", "c")

graph = builder.compile()

result = graph.invoke({"message": "开始"})
print(result)