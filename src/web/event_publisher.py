import contextvars
import json
from typing import Optional, List, Iterable
from loguru import logger
import redis

_redis_client = None
_session_id_ctx: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "session_id", default=None
)


def get_redis_client() -> redis.Redis:
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.Redis(
            host="localhost", port=6379, db=0, decode_responses=True
        )
    return _redis_client


def get_session_id() -> Optional[str]:
    return _session_id_ctx.get()


def set_session_id(session_id: str):
    _session_id_ctx.set(session_id)


def publish_event(event_type: str, payload: dict):
    sid = get_session_id()
    if sid is None: return
    client = get_redis_client()
    message = {
        "session_id": sid,
        "type": event_type,
        "payload": payload,
    }
    client.publish("agent_events", json.dumps(message, ensure_ascii=False))

def publish_selection_event(selected_uids: Iterable[str]):
    # logger.info(f"[usage] {selected_uids}")
    publish_event("selection_update", {"uids": list(set(selected_uids))})
