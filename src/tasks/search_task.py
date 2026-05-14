from tasks.clq import clq
from web.event_publisher import set_session_id, publish_event


@clq.task
def execute_query_task(query, session_id=None):
    from search.agent import kgq_ask
    set_session_id(session_id)
    res = kgq_ask(query)
    publish_event("report_update", dict(report=res))
    publish_event("done", {})
    return res
