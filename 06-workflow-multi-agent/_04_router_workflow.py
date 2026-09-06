from json import tool

from pydantic import BaseModel, Field
from typing import Literal
from langchain_ollama import ChatOllama, OllamaEmbeddings
from typing_extensions import TypedDict
from langgraph.graph import StateGraph, START, END
from langchain_core.tools import tool

class State(TypedDict):
    question: str
    category: str
    answer: str


class Classification(BaseModel):
    category: Literal["law", "movie", "normal"] = Field(description="问题所属类别")

def classifier(state: State):
    question = state["question"]
    result = classifier_llm.invoke(question)
    return {"category": result.category}



def law_handler(state: State):
    """ 查询法律法规和法律条文。"""
    print(">>> Law Node")
    return {"answer": "进入法律知识库进行检索"}

def movie_handler(state: State):
    """查询电影相关信息。"""
    print(">>> movie Node")
    return {"answer": "进入电影知识库进行检索"}

def normal_handler(state: State):
    """日常对话"""
    print(">>> normal Node")
    return {"answer": "交给普通 LLM 处理"}

def route(state: State):
    return state["category"]

llm = ChatOllama(model="qwen3:1.7b", temperature=0)
classifier_llm = llm.with_structured_output(Classification)

builder = StateGraph(State)

builder.add_node("classifier", classifier)
builder.add_node("law_handler", law_handler)
builder.add_node("movie_handler", movie_handler)
builder.add_node("normal_handler", normal_handler)

builder.add_edge(START, "classifier")

builder.add_conditional_edges("classifier", route,
                              {"law": "law_handler", "movie": "movie_handler", "normal": "normal_handler"})

builder.add_edge("law_handler", END)
builder.add_edge("movie_handler", END)
builder.add_edge("normal_handler", END)

graph = builder.compile()

result = graph.invoke({
    "question": "我国立法应当遵循什么原则？",
    "category": "",
    "answer": ""
})

print(result)