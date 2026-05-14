from tasks.clq import clq


@clq.task
def execute_load_task(doc):
    from load.top import load_document
    load_document(doc)
    return 1
