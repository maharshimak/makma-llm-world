import json
from concurrent.futures import ThreadPoolExecutor
import pytest
from makma.schemas import MemoryWrite
from makma.store import Store
from makma.kernel import Kernel,seed


def test_seed_is_idempotent_and_persistent(store):
    ids=[a.id for a in store.agents()]
    seed(store)
    assert len(ids)==48
    assert ids==[a.id for a in Store(store.path).agents()]


@pytest.mark.parametrize("kind",["working","episodic","semantic","procedural","research","social","failure","skill"])
def test_private_memory_never_crosses_owner_boundary(store,kind):
    agents=store.agents()
    for a in agents:
        store.remember(a.id,MemoryWrite(kind=kind,content=f"SHARED_QUERY secret_{a.id}",importance=1,confidence=1))
    for a in agents:
        found=store.memories(a.id,"SHARED_QUERY",limit=100)
        assert len(found)==1
        assert found[0]["agent_id"]==a.id
        assert found[0]["content"]==f"SHARED_QUERY secret_{a.id}"


def test_sql_injection_and_unknown_owner_do_not_retrieve_private_memories(store):
    a=store.agents()[0]
    store.remember(a.id,MemoryWrite(content="SECRET"))
    with pytest.raises(KeyError):
        store.memories("' OR 1=1 --")


def test_context_only_contains_addressed_messages(store,settings):
    a,b=store.agents()[:2]
    store.send("human",a.id,"A_SECRET")
    store.send("human",b.id,"B_SECRET")
    context=json.dumps(Kernel(store,None,settings).context(a.id,"task"))
    assert "A_SECRET" in context and "B_SECRET" not in context
    assert all("A_SECRET" not in e["summary"] for e in store.events())


def test_read_receipts_require_correct_recipient(store):
    a,b=store.agents()[:2]
    mid=store.send(a.id,b.id,"hello")
    store.mark_read(a.id,[mid])
    assert len(store.inbox(b.id,True))==1


def test_reflection_retains_sources(store,settings):
    a=store.agents()[0]
    ids=[store.remember(a.id,MemoryWrite(content=f"Experiment {i} failed",kind="failure")) for i in range(3)]
    mid=Kernel(store,None,settings).reflect(a.id)
    rows=store.memories(a.id,limit=100)
    assert len(rows)==4
    assert set(next(m for m in rows if m["id"]==mid)["sources"])==set(ids)


def test_concurrent_job_claim_is_exactly_once(store):
    a=store.agents()[0]
    jid=store.enqueue(a.id,"cognition",{"task":"test"})
    with ThreadPoolExecutor(max_workers=8) as pool:
        claims=list(pool.map(lambda _:store.claim_job(),range(8)))
    assert [c["id"] for c in claims if c]==[jid]


def test_events_immutable(store):
    import sqlite3
    with pytest.raises(sqlite3.IntegrityError):
        with store.connect() as db:
            db.execute("DELETE FROM events")


def test_project_scoped_claim_does_not_consume_other_work(store):
    a,b=store.agents()[:2]
    store.put("projects",{"id":"target","status":"running"})
    unrelated=store.enqueue(a.id,"cognition",{"task":"unrelated"},priority=10)
    target=store.enqueue(b.id,"hypothesis",{},project_id="target")
    assert store.claim_job("target")["id"]==target
    assert store.claim_job("target") is None
    assert store.claim_job()["id"]==unrelated
