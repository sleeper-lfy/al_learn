def legal_analysis(state):
    print("法律分析")

    state["legal_result"] = "发现 3 个潜在法律风险"

    return state


def spelling_check(state):
    print("错别字检查")

    state["spelling_result"] = "发现 5 个错别字"

    return state


from concurrent.futures import ThreadPoolExecutor


# 等效于
# builder.add_edge("query", "vector_search")
# builder.add_edge("query", "bm25_search")
# query 执行完成后，vector_search 和 bm25_search就会进入同一批次的并行执行。
def workflow(state):
    with ThreadPoolExecutor(max_workers=2) as executor:
        future1 = executor.submit(legal_analysis, state.copy())
        future2 = executor.submit(spelling_check, state.copy())
        legal_state = future1.result()
        spelling_state = future2.result()

    state["legal_result"] = legal_state["legal_result"]
    state["spelling_result"] = spelling_state["spelling_result"]

    return state