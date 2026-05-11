from tasks.clq import clq


@clq.task
def execute_query_task(query):
    from search.agent import kgq_ask
    res = kgq_ask(query)
    return res
