import asyncio
import datetime
import json
import uuid
from contextlib import asynccontextmanager

import socketio
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from redis.asyncio import Redis as AsyncRedis

from db.neo_base import n_setup, IDNode, cypher
from db.neo_doc import DDocument, DocumentProcStages, DBlock
from db.neo_kg import KNode, KEntity, KRelFact, KValFact
from load.top import DocumentFile
from tasks.load_task import execute_load_task
from tasks.search_task import execute_query_task

event_buffers = {}


async def redis_listener():
    r = AsyncRedis(host="localhost", port=6379, db=0, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("agent_events")
    try:
        async for message in pubsub.listen():
            if message["type"] != "message":
                continue

            data = json.loads(message["data"])
            session_id = data["session_id"]
            event_type = data["type"]
            payload = data["payload"]
            buffer = event_buffers.setdefault(session_id, [])
            buffer.append((event_type, payload))
            if len(buffer) > 100:
                buffer.pop(0)

            await sio.emit(event_type, payload, room=session_id)
    except asyncio.CancelledError:
        await pubsub.unsubscribe("agent_events")
        await r.close()
        raise


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(redis_listener())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass


app = FastAPI(title="rag", lifespan=lifespan)
sio = socketio.AsyncServer(cors_allowed_origins="*", async_mode="asgi")
socket_app = socketio.ASGIApp(sio, app)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

search_sessions = {}


class SearchRequest(BaseModel):
    query: str


class NodesRequest(BaseModel):
    uids: list[str]


@app.get("/api/documents")
async def get_documents():
    return [
        dict(
            uid=i.uid,
            name=i.name,
            state="queued" if len(i.stages) == 0 else (
                "processing" if len(i.stages) < len(DocumentProcStages) else "done"),
            percent=round(len(set(i.stages)) / len(DocumentProcStages) * 100),
            blocks_count=len(i.blocks),
        )
        for i in DDocument.select()
    ]


@app.post("/api/clear")
async def clear_db():
    n_setup()


@app.post("/api/documents/upload")
async def upload_document(file: UploadFile = File(...)):
    execute_load_task.delay(DocumentFile(
        name=file.filename,
        content=await file.read()
    ))
    return {"uid": 0, "status": "uploaded"}


def node_dto(i):
    par = {}
    pre = i.__dict__

    def __vf_dto(tgt: KNode):
        return {
            i.type_code: i.value
            for i in tgt.described_with.all()
            if isinstance(i, KValFact)
        }

    def _subj(x):
        x = [j.uid for j in x.subject.all()]
        return x[0] if x else None

    try:
        match i:
            case KEntity():
                par = dict(
                    name=i.repr,
                    characteristics=__vf_dto(i),
                )
            case KRelFact():
                par = dict(
                    name=i.type_code,
                    subject=_subj(i),
                    objects=[j.uid for j in i.objects.all()],
                    characteristics=__vf_dto(i),
                )
            case KValFact():
                par = dict(
                    name=i.type_code,
                    subject=_subj(i),
                    value=i.value
                )
    except:
        pass

    base = dict(
        uid=i.uid,
        node_class=type(i).__name__,
        name=pre.get("name") or pre.get("repr"),
        repr=pre.get("repr"),
        type_code=pre.get("type_code"),
    )
    base.update(par)
    return base


@app.get("/api/graph")
async def get_graph():
    n = IDNode.select() + KNode.select()
    n = [i for i in n if isinstance(i, KNode | DDocument | DBlock)]
    nodes = {i.uid: node_dto(i) for i in n}
    conns = cypher("""
        MATCH (a)-[x:K_SUBJ|K_OBJ]-(b)
        WHERE a.uid in $allowed and b.uid in $allowed
        RETURN DISTINCT a.uid, b.uid, type(x)
    """, params=dict(allowed=list(nodes.keys())))
    return dict(nodes=nodes, connections=conns)


@app.get("/api/nodes/{uid}")
async def get_node(uid: str):
    if not (node := IDNode.get(uid=uid)):
        node = KNode.get(uid=uid)
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    return node_dto(node)


@app.post("/api/search")
async def start_search(request: SearchRequest):
    session_id = str(uuid.uuid4())
    search_sessions[session_id] = {
        "query": request.query,
        "started_at": datetime.datetime.now(),
    }
    execute_query_task.delay(request.query, session_id)
    return {"session_id": session_id}


@sio.event
async def connect(sid, environ):
    print(f"Client connected: {sid}")


@sio.event
async def disconnect(sid):
    print(f"Client disconnected: {sid}")


@sio.on("join_search")
async def join_search(sid, data):
    session_id = data.get("session_id")
    if session_id:
        await sio.enter_room(sid, session_id)
        print(f"Client {sid} joined search session {session_id}")

        buffer = event_buffers.get(session_id, [])
        for event_type, payload in buffer:
            await sio.emit(event_type, payload, to=sid)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(socket_app, host="0.0.0.0", port=8000)
