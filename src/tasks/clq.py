from celery import Celery

from utils.config import sys_cfg

clq = Celery("kgq")
clq.conf.update(
    result_backend_transport_options={
        'global_keyprefix': 'clq__'
    },
    broker_url=f'{sys_cfg.redis.conn}/0',
    result_backend=f'{sys_cfg.redis.conn}/0',
    task_serializer='pickle',
    result_serializer='pickle',
    accept_content=['json', 'application/x-python-serialize'],
    result_accept_content=['json', 'application/x-python-serialize'],
    include=[
        'tasks.search_task',
        'tasks.load_task',
    ]
)
