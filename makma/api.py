"""Local operator API. Bind to loopback; never expose this unauthenticated console."""
import asyncio
import json
from contextlib import asynccontextmanager
from dataclasses import asdict
from typing import Literal
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse, PlainTextResponse
from starlette.middleware.trustedhost import TrustedHostMiddleware
from pydantic import Field
from .config import Settings
from .schemas import Agent, Role, Schema, ProjectCreate, MessageCreate, MemoryWrite
from .store import Store
from .providers import make_provider, ModelRouter
from .kernel import Kernel, seed
from .research import Research
from .scheduler import Scheduler
from .sandbox import DockerSandbox
from .knowledge import Literature
from .world.simulation import World
from .world.api import world_routes


class AgentCreate(Schema):
    name: str=Field(min_length=1,max_length=80)
    role: Role


class TaskCreate(Schema):
    task: str=Field(min_length=3,max_length=3000)


class AccessSettings(Schema):
    external_research: bool


def create_app(settings=None,provider=None,sandbox=None):
    config=settings or Settings()
    store=Store(config.data_dir/"makma.sqlite3")
    seed(store)
    model=provider or make_provider(config)
    router=ModelRouter(model,config.model,config.concurrency)
    lab=sandbox or DockerSandbox(config.sandbox_image,config.sandbox_timeout)
    kernel=Kernel(store,router,config)
    research=Research(store,router,lab,config)
    scheduler=Scheduler(store,kernel,research,config)
    world=World(store,router,config)
    scheduler.world=world

    @asynccontextmanager
    async def lifespan(app):
        await scheduler.start()
        await world.start()
        yield
        await scheduler.close()
        await world.close()
        if hasattr(model,"close"):
            await model.close()

    app=FastAPI(title="Mak'ma Agent Operating System",version="0.1.0",lifespan=lifespan)
    app.state.store=store
    app.state.scheduler=scheduler
    app.state.research=research
    app.state.world=world
    app.include_router(world_routes(world))
    app.add_middleware(TrustedHostMiddleware,allowed_hosts=["127.0.0.1","localhost","testserver"])

    @app.middleware("http")
    async def local_boundary(request,call_next):
        origin=request.headers.get("origin")
        if origin and origin not in {"http://127.0.0.1:3010","http://localhost:3010","http://127.0.0.1:8765","http://localhost:8765"}:
            return JSONResponse({"detail":"Untrusted origin"},status_code=403)
        if request.method not in {"GET","HEAD","OPTIONS"} and request.headers.get("x-makma-client")!="local-console":
            return JSONResponse({"detail":"X-Makma-Client: local-console header required"},status_code=403)
        try:
            declared_length=int(request.headers.get("content-length","0"))
        except ValueError:
            return JSONResponse({"detail":"Invalid Content-Length"},status_code=400)
        if declared_length<0:
            return JSONResponse({"detail":"Invalid Content-Length"},status_code=400)
        if declared_length>32000:
            return JSONResponse({"detail":"Request too large"},status_code=413)
        # Count actual bytes, including chunked bodies without Content-Length.
        chunks=[]
        received=0
        async for chunk in request.stream():
            received+=len(chunk)
            if received>32000:
                return JSONResponse({"detail":"Request too large"},status_code=413)
            chunks.append(chunk)
        request._body=b"".join(chunks)
        response=await call_next(request)
        response.headers["X-Content-Type-Options"]="nosniff"
        response.headers["Cache-Control"]="no-store"
        return response

    @app.exception_handler(KeyError)
    async def missing(request,exc):
        return JSONResponse({"detail":"Record not found"},status_code=404)

    @app.exception_handler(ValueError)
    async def invalid(request,exc):
        return JSONResponse({"detail":str(exc)},status_code=409)

    @app.exception_handler(PermissionError)
    async def denied(request,exc):
        return JSONResponse({"detail":str(exc)},status_code=403)

    @app.get("/health")
    async def health():
        model_health,sandbox_health=await asyncio.gather(model.health(),lab.health())
        return {"database":True,"memory":True,"scheduler":scheduler.loop_task is not None and not scheduler.loop_task.done(),"model":model_health,"sandbox":sandbox_health,"external_research":store.setting("external_research",config.external_research),"paused":store.setting("paused",True)}

    @app.get("/metrics")
    def metrics():
        agents=store.agents()
        traces=store.records("traces")
        experiments=store.records("experiments")
        return {"agents":len(agents),"active_agents":sum(a.state=="thinking" for a in agents),"projects":len(store.records("projects")),"hypotheses":len(store.records("hypotheses")),"experiments":len(experiments),"completed_experiments":sum(e["status"]=="completed" for e in experiments),"discoveries":len(store.records("discoveries")),"papers":len(store.records("papers")),"skills":len(store.records("skills")),"failures":len(store.records("failures")),"tokens":sum(t.get("tokens",0) for t in traces),"inference_seconds":sum(t.get("seconds",0) for t in traces),"paused":store.setting("paused",True),"cognition_reserved_tokens":store.setting("cognition_reserved_tokens",0),"cognition_budget":config.token_budget,"compute_utilization":None,"cost_per_discovery":None}

    @app.get("/agents")
    def agents():
        return [a.model_dump() for a in store.agents()]

    @app.post("/agents")
    def create_agent(body:AgentCreate):
        role_template=next((a for a in store.agents() if a.role==body.role),None)
        a=Agent(name=body.name,role=body.role,permissions=role_template.permissions if role_template else ["message","knowledge.query","reflect"])
        store.save_agent(a)
        store.event("AGENT_CREATED",a.id,f"{a.name} joined as {a.role}")
        return a

    @app.get("/agents/{aid}")
    def agent(aid:str):
        return store.agent(aid)

    @app.get("/agents/{aid}/memory")
    def memory(aid:str,q:str=""):
        return store.memories(aid,q,limit=100)

    @app.get("/agents/{aid}/beliefs")
    def beliefs(aid:str):
        return store.agent(aid).beliefs

    @app.get("/agents/{aid}/goals")
    def goals(aid:str):
        return store.agent(aid).goals

    @app.get("/agents/{aid}/messages")
    def messages(aid:str):
        return store.inbox(aid)

    @app.get("/agents/{aid}/traces")
    def traces(aid:str):
        store.agent(aid)
        return [t for t in store.records("traces") if t["agent_id"]==aid]

    @app.post("/agents/{aid}/message")
    def message(aid:str,body:TaskCreate):
        mid=store.send("human",aid,body.task)
        jid=store.enqueue(aid,"cognition",{"task":"Read the operator's message and act within your permissions."})
        return {"message_id":mid,"job_id":jid}

    @app.post("/agents/{aid}/task")
    def task(aid:str,body:TaskCreate):
        store.agent(aid)
        return {"job_id":store.enqueue(aid,"cognition",body.model_dump())}

    @app.post("/agents/{aid}/reflect")
    def reflect(aid:str):
        return {"memory_id":kernel.reflect(aid)}

    @app.post("/research/projects")
    def create_project(body:ProjectCreate):
        return research.create(body)

    @app.get("/research/projects")
    def projects():
        return store.records("projects")

    @app.get("/research/projects/{pid}")
    def project(pid:str):
        return store.get("projects",pid)

    @app.post("/research/projects/{pid}/start")
    def start_project(pid:str):
        return research.start(pid)

    @app.post("/research/projects/{pid}/pause")
    def pause_project(pid:str):
        p=store.get("projects",pid)
        p["status"]="paused"
        store.put("projects",p)
        store.event("PROJECT_PAUSED",pid,"Operator paused research")
        return p

    @app.get("/research/projects/{pid}/report",response_class=PlainTextResponse)
    def report(pid:str):
        p=store.get("projects",pid)
        return p.get("report") or research.report(p)

    @app.get("/hypotheses")
    def hypotheses():
        return store.records("hypotheses")

    @app.get("/experiments")
    def experiments():
        return store.records("experiments")

    @app.get("/experiments/{eid}")
    def experiment(eid:str):
        return store.get("experiments",eid)

    @app.get("/discoveries")
    def discoveries():
        return store.records("discoveries")

    @app.get("/knowledge/search")
    def knowledge(q:str=""):
        return Literature(store).query(q)

    @app.get("/knowledge/graph")
    def graph():
        return {"nodes":store.records("graph"),"edges":store.records("edges")}

    @app.get("/papers")
    def papers():
        return store.records("papers")

    @app.get("/skills")
    def skills():
        return store.records("skills")

    @app.get("/failures")
    def failures():
        return store.records("failures")

    @app.get("/models")
    def models():
        return [asdict(m) for m in router.registry]

    @app.get("/jobs")
    def jobs():
        return store.jobs()

    @app.post("/jobs/{jid}/retry")
    def retry(jid:str):
        job=next((j for j in store.jobs() if j["id"]==jid),None)
        if not job:
            raise KeyError(jid)
        if job["status"]!="blocked":
            raise ValueError("Only blocked jobs can be retried")
        if job["project_id"]:
            raise ValueError("Resume the research project to retry its current stage")
        store.finish_job(jid,"queued")
        return {"status":"queued"}

    @app.post("/world/pause")
    def pause():
        store.set_setting("paused",True)
        store.event("WORLD_PAUSED","world","Paused; in-flight operation may finish")
        return {"paused":True}

    @app.post("/world/resume")
    def resume():
        store.set_setting("paused",False)
        store.event("WORLD_RESUMED","world","Scheduler resumed")
        return {"paused":False}

    @app.post("/world/stop")
    async def stop():
        await scheduler.stop()
        await world.control(True,world.state()["speed"])
        with store.connect() as db:
            db.execute("UPDATE jobs SET status='blocked',error='Stopped by operator' WHERE status='queued'")
        for p in store.records("projects"):
            if p["status"]=="running":
                p["status"]="paused"
                store.put("projects",p)
        store.event("WORLD_STOPPED","world","Operator stopped all research and sandbox activity")
        return {"paused":True,"stopped":True}

    @app.post("/world/budget/reset")
    def budget_reset():
        store.set_setting("cognition_reserved_tokens",0)
        store.event("BUDGET_RESET","world","Operator renewed world cognition token allocation")
        return {"reserved_tokens":0}

    @app.post("/settings")
    def update_settings(body:AccessSettings):
        store.set_setting("external_research",body.external_research)
        store.event("RESEARCH_ACCESS_CHANGED","world",f"Crossref network access {'enabled' if body.external_research else 'disabled'} by operator")
        return body

    @app.get("/events")
    def events(after:int=0):
        return store.events(after)

    @app.get("/events/stream")
    async def stream(request:Request,after:int=0):
        async def generate():
            cursor=after
            while not await request.is_disconnected():
                events=sorted(store.events(cursor),key=lambda e:e["seq"])
                for event in events:
                    cursor=event["seq"]
                    yield f"id: {cursor}\ndata: {json.dumps(event)}\n\n"
                yield ": heartbeat\n\n"
                await asyncio.sleep(2)
        return StreamingResponse(generate(),media_type="text/event-stream",headers={"X-Accel-Buffering":"no"})

    return app
