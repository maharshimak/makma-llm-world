import json
import pytest
from makma.providers import MockProvider,ModelRouter
from makma.kernel import Kernel
from makma.schemas import Role


async def test_forbidden_action_batch_cannot_write_memory(store,settings):
    a=next(a for a in store.agents() if a.role==Role.statistician)
    output={"thought_summary":"Try tool","current_goal":"search","confidence":1,"memory_write":[{"content":"should not be written"}],"proposed_actions":[{"action":"research.search","content":"test"}]}
    kernel=Kernel(store,ModelRouter(MockProvider([output]),"mock"),settings)
    with pytest.raises(PermissionError):
        await kernel.think(a.id,"try search")
    assert store.memories(a.id)==[]
    assert store.records("traces")[0]["status"]=="failed"


async def test_claim_does_not_become_experimental_evidence(store,settings):
    a=store.agents()[0]
    output={"thought_summary":"Hypothesis only","current_goal":"test","confidence":.9,"belief_updates":[{"claim":"latency improves 40%","belief_type":"claim","confidence":.9,"last_verified":"2026-01-01","sources":["fake:paper"]}]}
    await Kernel(store,ModelRouter(MockProvider([output]),"mock"),settings).think(a.id,"test")
    assert store.agent(a.id).beliefs[0].last_verified is None
    assert not store.records("experiments")
    assert not store.records("discoveries")

