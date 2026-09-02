from typing import TypedDict
from langgraph.graph import StateGraph, START, END


class State(TypedDict):
    name: str
    message: str


def add_greeting(state: State):
    return {
        "message": "你好"
    }


def make_greeting(state: State):
    return {
        "message": f"{state['message']}，{state['name']}"
    }


if __name__ == '__main__':
    builder = StateGraph(State)
    #添加可以执行节点
    builder.add_node("add_greeting", add_greeting)
    builder.add_node("make_greeting", make_greeting)
    #控制节点运行顺序
    builder.add_edge(START, "add_greeting")
    builder.add_edge("add_greeting", "make_greeting")
    builder.add_edge("make_greeting", END)

    graph = builder.compile()

    result = graph.invoke({
        "name": "张三",
        "message": ""
    })

    print(result)