from tasks.clq import clq


@clq.task
def load_document(doc):
    return 1
