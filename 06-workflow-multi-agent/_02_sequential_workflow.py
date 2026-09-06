def analyze(query):
    print("分析问题")
    return {"query": query, "keyword": "听证"}


def search(data):
    print("执行检索")
    data["results"] = ["行政处罚法相关条文"]
    return data


def rerank(data):
    print("执行重排序")
    data["results"] = data["results"]
    return data


def generate(data):
    print("生成答案")
    data["answer"] = "根据相关法律规定……"
    return data

def workflow(query):
    data = analyze(query)
    data = search(data)
    data = rerank(data)
    data = generate(data)

    return data
result = workflow(
    "行政处罚法中关于听证的规定是什么？"
)

print(result["answer"])