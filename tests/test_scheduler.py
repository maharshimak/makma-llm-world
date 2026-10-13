import asyncio
from makma.scheduler import Scheduler
from makma.kernel import Kernel
from makma.providers import ModelRouter,MockProvider


class ResearchStub:
    class Lab:
        async def stop_all(self): pass
    sandbox=Lab()


async def test_paused_scheduler_does_not_call_model(store,settings):
    provider=MockProvider()
    scheduler=Scheduler(store,Kernel(store,ModelRouter(provider,"mock"),settings),ResearchStub(),settings)
    store.enqueue(store.agents()[0].id,"cognition",{"task":"test"})
    await scheduler.start()
    await asyncio.sleep(.05)
    assert not provider.calls
    assert store.jobs()[0]["status"]=="queued"
    await scheduler.close()


async def test_budget_prevents_inference(store,settings):
    provider=MockProvider()
    scheduler=Scheduler(store,Kernel(store,ModelRouter(provider,"mock"),settings),ResearchStub(),settings)
    store.set_setting("cognition_reserved_tokens",settings.token_budget)
    store.enqueue(store.agents()[0].id,"cognition",{"task":"test"})
    await scheduler.execute(store.claim_job())
    assert not provider.calls
    assert store.jobs()[0]["status"]=="blocked"


def test_crash_recovery_does_not_replay_side_effects(store):
    store.enqueue(store.agents()[0].id,"experiment",{})
    store.claim_job()
    store.recover()
    assert store.jobs()[0]["status"]=="blocked"

