from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    age: int
    result: str


def check_age(state: State):
    return {}


def adult(state: State):
    return {"result": "成年人"}


def child(state: State):
    return {"result": "未成年人"}


def route(state: State):
    if state["age"] >= 18:
        return "adult"
    else:
        return "child"


if __name__ == '__main__':
    builder = StateGraph(State)
    builder.add_node("check_age", check_age)
    builder.add_node("adult", adult)
    builder.add_node("child", child)

    builder.add_edge(START, "check_age")
    # 让route返回的参数为下一个要执行的node
    builder.add_conditional_edges("check_age", route)

    builder.add_edge("adult", END)
    builder.add_edge("child", END)

    graph = builder.compile()

    result = graph.invoke({"age": 18, "result": ""})
    print(result)
    result = graph.invoke({"age": 16, "result": ""})
    print(result)