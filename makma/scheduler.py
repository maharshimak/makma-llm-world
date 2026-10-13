import asyncio
from .schemas import MemoryWrite


class Scheduler:
    def __init__(self,store,kernel,research,settings):
        self.store,self.kernel,self.research,self.settings=store,kernel,research,settings
        self.tasks=set()
        self.loop_task=None
        self.stopping=False
        self.world=None

    async def start(self):
        self.store.recover()
        self.loop_task=asyncio.create_task(self.loop())

    async def loop(self):
        while not self.stopping:
            if not self.store.setting("paused",True) and len(self.tasks)<self.settings.concurrency:
                job=self.store.claim_job()
                if job:
                    if job["project_id"] and self.world and not self.world.ready_for_research(job["agent_id"]):
                        self.store.finish_job(job["id"],"queued")
                        await asyncio.sleep(self.settings.scheduler_interval)
                        continue
                    task=asyncio.create_task(self.execute(job))
                    self.tasks.add(task)
                    task.add_done_callback(self.tasks.discard)
            await asyncio.sleep(self.settings.scheduler_interval)

    async def execute(self,job):
        agent=self.store.agent(job["agent_id"])
        agent.state="thinking"
        agent.schedule={"lod":3,"wake_reason":job["kind"]}
        self.store.save_agent(agent)
        try:
            if job["kind"]=="cognition":
                used=self.store.setting("cognition_reserved_tokens",0)
                reserve=2*(self.settings.context_length+self.settings.max_output_tokens)
                if used+reserve>self.settings.token_budget:
                    raise PermissionError("World cognition budget exhausted; operator must reset budget")
                self.store.set_setting("cognition_reserved_tokens",used+reserve)
                await self.kernel.think(agent.id,job["payload"]["task"])
            else:
                await self.research.step(job)
            self.store.finish_job(job["id"],"completed")
        except asyncio.CancelledError:
            self.store.finish_job(job["id"],"blocked","Stopped by operator or shutdown")
            if job["project_id"]:
                p=self.store.get("projects",job["project_id"])
                p.update(status="blocked",error="Interrupted; inspect artifacts before resuming")
                self.store.put("projects",p)
        except Exception as exc:
            error=f"{type(exc).__name__}: {exc}"[:3000]
            self.store.finish_job(job["id"],"blocked",error)
            self.store.event("JOB_BLOCKED",job["id"],error[:400])
            self.store.remember(agent.id,MemoryWrite(kind="failure",content=error,importance=.8,confidence=1))
            if job["project_id"]:
                p=self.store.get("projects",job["project_id"])
                p.update(status="blocked",error=error)
                self.store.put("projects",p)
        finally:
            agent=self.store.agent(agent.id)
            agent.state="idle"
            agent.schedule={"lod":0,"wake_reason":None}
            self.store.save_agent(agent)

    async def stop(self):
        self.store.set_setting("paused",True)
        for task in list(self.tasks):
            task.cancel()
        await asyncio.gather(*list(self.tasks),return_exceptions=True)
        await self.research.sandbox.stop_all()

    async def close(self):
        self.stopping=True
        if self.loop_task:
            self.loop_task.cancel()
            await asyncio.gather(self.loop_task,return_exceptions=True)
        await self.stop()
