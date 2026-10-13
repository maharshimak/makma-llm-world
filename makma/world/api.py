import asyncio
from fastapi import APIRouter,Header,WebSocket,WebSocketDisconnect
from ..schemas import Schema
from .contracts import WorldControlV1,WorldEventV1,BridgeHeartbeatV1,ConversationInputV1


class Embodiment(Schema):
    enabled:bool


def world_routes(world):
    router=APIRouter(prefix="/world",tags=["world-v1"])

    @router.get("/snapshot")
    def snapshot():return world.snapshot()

    @router.get("/citizens/{aid}")
    def citizen(aid:str):return world.public_agent(aid)

    @router.post("/clock")
    async def clock(body:WorldControlV1):return await world.control(body.paused,body.speed)

    @router.post("/bridge/heartbeat")
    async def heartbeat(body:BridgeHeartbeatV1):return await world.heartbeat(body.client_id,body.player_position)

    @router.post("/bridge/events")
    async def event(body:WorldEventV1,x_makma_bridge:str=Header()):return await world.acknowledge(x_makma_bridge,body)

    @router.post("/embodiment")
    def embodiment(body:Embodiment):
        world.store.set_setting("embodied_research",body.enabled)
        return {"enabled":body.enabled}

    @router.post("/conversation")
    async def conversation(body:ConversationInputV1):return await world.converse(body.agent_id,body.text)

    @router.get("/conversations/{cid}")
    def conversation_record(cid:str):return world.store.get("conversations",cid)

    @router.post("/snapshot/save")
    def save_snapshot():
        from ..schemas import uid
        snapshot=world.snapshot();snapshot["id"]=uid("snapshot")
        world.store.put("world_snapshots",snapshot)
        return {"id":snapshot["id"],"tick":snapshot["tick"]}

    @router.websocket("/stream")
    async def stream(socket:WebSocket):
        origin=socket.headers.get("origin")
        if origin and origin not in {"http://127.0.0.1:3010","http://localhost:3010"}:
            await socket.close(code=1008);return
        await socket.accept()
        try:
            while True:
                await socket.send_json({"type":"snapshot","version":1,"state":world.snapshot()})
                await asyncio.sleep(.5)
        except (WebSocketDisconnect,RuntimeError):pass
    return router
