import json
import pytest
from makma.research import Research
from makma.providers import MockProvider,ModelRouter
from makma.schemas import ProjectCreate
from makma.benchmark import Benchmark,BASELINE
from makma.sandbox import SandboxUnavailable

HYP={"title":"Length-normalized retrieval","mechanism":"Normalize lexical term overlap by document length to reduce verbosity bias.","prediction":"Short relevant documents will rank above longer noisy documents.","required_experiment":"Compare recall and NDCG on held-out queries","plausibility":.6}
REVIEW={"approved":True,"criticisms":["Small fixture cannot establish novelty"],"controls":["Keep labels outside candidate environment"]}


class Offline:
    async def health(self): return {"available":False,"detail":"offline"}
    async def run(self,*args,**kwargs): raise SandboxUnavailable("offline")


async def test_pipeline_uses_model_then_stops_at_unavailable_sandbox(store,settings):
    provider=MockProvider([HYP,REVIEW,{"explanation":"Test baseline-shaped candidate","code":BASELINE}])
    research=Research(store,ModelRouter(provider,"mock"),Offline(),settings)
    p=research.create(ProjectCreate(title="RAG experiment",question="Can retrieval quality improve?",token_budget=100000))
    research.start(p["id"])
    store.set_setting("paused",False)
    for expected in ["literature","hypothesis","critique","code"]:
        job=store.claim_job()
        assert job["kind"]==expected
        await research.step(job)
        store.finish_job(job["id"],"completed")
    job=store.claim_job()
    assert job["kind"]=="experiment"
    with pytest.raises(SandboxUnavailable):
        await research.step(job)
    assert len(provider.calls)==3
    assert store.records("experiments")[0]["status"]=="failed"
    assert not store.records("discoveries")
    assert store.records("failures")
    assert any(store.inbox(a.id) for a in store.agents())


def test_paused_project_does_not_claim_queued_job(store,settings):
    research=Research(store,None,Offline(),settings)
    p=research.create(ProjectCreate(title="Pause test",question="Can retrieval quality improve?"))
    research.start(p["id"])
    p=store.get("projects",p["id"])
    p["status"]="paused"
    store.put("projects",p)
    assert store.claim_job() is None


def test_handoff_preserves_operator_pause(store,settings):
    research=Research(store,None,Offline(),settings)
    p=research.create(ProjectCreate(title="Pause test",question="Can retrieval quality improve?"))
    p=research.start(p["id"])
    paused={**p,"status":"paused"}
    store.put("projects",paused)
    research.enqueue(p,"hypothesis")
    assert store.get("projects",p["id"])["status"]=="paused"


async def test_mock_rankings_cannot_supply_numeric_metrics(tmp_path):
    class RankingDouble:
        async def run(self,*args):
            return {"rankings":[["x"]],"wall_seconds":.2,"image_id":"TEST-IMAGE","ndcg":999}
    dataset={"id":"test","scope":"smoke","documents":[{"id":"x","text":"alpha"}],"queries":[{"text":"alpha","relevant":["x"]}]}
    result=await Benchmark(RankingDouble(),tmp_path).compare("exp_test",BASELINE,dataset)
    assert result["metrics"]["candidate"]["ndcg"]==1
    assert result["metrics"]["candidate"]["llm_tokens"] is None
    assert json.loads((tmp_path/"exp_test"/"result.json").read_text())["dataset_hash"]==result["dataset_hash"]

