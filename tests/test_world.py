import copy
import pytest
from makma.world.simulation import World,distance
from makma.world.contracts import WorldEventV1,Vector3
from makma.providers import MockProvider,ModelRouter


@pytest.fixture
def world(store,settings):return World(store,ModelRouter(MockProvider(),"mock"),settings)


def test_world_identities_and_state_survive_restart(world,store,settings):
    before=world.state()
    assert len(before["citizens"])==21
    assert len({c["id"] for c in before["citizens"]})==21
    assert World(store,None,settings).state()==before


async def test_clock_pause_and_speed(world):
    old=world.state()["sim_minutes"]
    await world.advance(1)
    assert world.state()["sim_minutes"]==old
    await world.control(False,20)
    await world.advance(1)
    assert world.state()["sim_minutes"]==pytest.approx(old+20/60)


async def test_player_position_is_owned_by_active_bridge(world):
    near=Vector3(**world.state()["citizens"][0]["position"])
    await world.heartbeat("engine-a",near)
    with pytest.raises(PermissionError):
        await world.heartbeat("engine-b",Vector3(x=20000))
    assert world.state()["player"]["position"]==near.model_dump()
    await world.control(False,1)
    await world.advance(1)
    assert world.state()["citizens"][0]["lod"]==3


def test_object_reservation_exclusive(world):
    s=world.state();a,b=s["citizens"][:2]
    first=world.reserve(s,a,"ai_lab");second=world.reserve(s,b,"ai_lab")
    assert first["id"]!=second["id"]
    assert world.reserve(s,a,"ai_lab")["id"]==first["id"]


async def test_action_ack_requires_lease_identity_and_proximity(world):
    await world.control(False,1)
    await world.advance(1)
    s=world.state();a=s["actions"][0]
    await world.heartbeat("engine-a")
    good=WorldEventV1(action_id=a["id"],agent_id=a["agent_id"],event="action_completed",position=Vector3(**a["position"]))
    with pytest.raises(PermissionError):await world.acknowledge("wrong",good)
    with pytest.raises(PermissionError):await world.heartbeat("engine-b")
    bad=good.model_copy(update={"position":Vector3(x=30000,y=30000)})
    with pytest.raises(ValueError):await world.acknowledge("engine-a",bad)
    assert (await world.acknowledge("engine-a",good))["status"]=="accepted"
    assert (await world.acknowledge("engine-a",good))["status"]=="duplicate"


async def test_connected_engine_owns_low_level_movement(world):
    await world.control(False,1);await world.advance(1)
    await world.heartbeat("engine")
    before=world.state()["citizens"][0]["position"]
    await world.advance(2)
    assert world.state()["citizens"][0]["position"]==before


async def test_thirty_minutes_produces_real_routine_interactions(world,store):
    await world.control(False,100)
    for _ in range(9):await world.advance(2)
    s=world.state()
    assert s["sim_minutes"]==pytest.approx(450)
    assert any(c["location"]!="apartments" for c in s["citizens"])
    assert any(e["type"]=="SOCIAL_ENCOUNTER" for e in store.events(limit=1000))
    assert any(store.memories(c["id"]) for c in s["citizens"])


def test_economy_conserves_simulation_currency(world):
    s=world.state();c=s["citizens"][0]
    total=lambda:sum(c["money"] for c in s["citizens"])+sum(b["money"] for b in s["businesses"])+s["treasury"]
    before=total();world.eat(s,c);assert total()==before
    s["sim_minutes"]=1500;world.pay_day(s,c);assert total()==before
    balance=c["money"];world.pay_day(s,c);assert c["money"]==balance


async def test_player_dialogue_cannot_see_other_agents_memory(world,store,settings):
    from makma.schemas import MemoryWrite
    a,b=world.state()["citizens"][:2]
    store.remember(a["id"],MemoryWrite(content="A_SECRET"))
    store.remember(b["id"],MemoryWrite(content="B_SECRET"))
    provider=MockProvider([{"reply":"I am preparing for the day.","confidence":.8}])
    world.router=ModelRouter(provider,"mock")
    await world.converse(a["id"],"What are you doing?")
    import json
    prompt=json.dumps(provider.calls)
    assert "A_SECRET" in prompt and "B_SECRET" not in prompt
