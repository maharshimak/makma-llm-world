"""Durable research state machine with specialist handoffs and evidence gates."""
import json
from datetime import datetime, timezone
from pathlib import Path
from .schemas import Role, MemoryWrite, HypothesisDraft, Review, CodeDraft, now, uid
from .kernel import POLICY
from .knowledge import Literature, link
from .benchmark import Benchmark, validation_gate, digest
from .sandbox import validate_code

ROOT=Path(__file__).resolve().parent.parent
STAGES=["literature","hypothesis","critique","code","experiment","replication","report"]
ROLES={"literature":Role.scout,"hypothesis":Role.scientist,"critique":Role.critic,"code":Role.engineer,"experiment":Role.engineer,"replication":Role.replicator,"report":Role.statistician}


class Research:
    def __init__(self,store,router,sandbox,settings):
        self.store,self.router,self.sandbox,self.settings=store,router,sandbox,settings
        self.benchmark=Benchmark(sandbox,settings.data_dir/"artifacts")

    def create(self,request):
        project={"id":uid("project"),**request.model_dump(),"created_at":now(),"started_at":None,"status":"draft","stage":"literature","tokens":0,"reserved_tokens":0,"experiments_used":0,"hypothesis_ids":[],"experiment_ids":[],"citations":[],"team":{},"limitations":[],"generation":0,"max_generations":request.experiment_budget,"report":None}
        for stage,role in ROLES.items():
            candidates=[a for a in self.store.agents() if a.role==role]
            project["team"][stage]=candidates[0].id
        self.store.put("projects",project)
        self.store.put("graph",{"id":project["id"],"kind":"Project","label":project["title"]})
        self.store.event("PROJECT_CREATED",project["id"],project["title"])
        return project

    def start(self,pid):
        p=self.store.get("projects",pid)
        if p["status"] not in {"draft","paused","blocked"}:
            raise ValueError(f"Cannot start project in {p['status']} state")
        p["started_at"]=p["started_at"] or now()
        p["status"]="running"
        p.pop("error",None)
        self.store.put("projects",p)
        queued=[j for j in self.store.jobs() if j["project_id"]==pid and j["status"] in {"queued","running"}]
        if not queued:
            self.enqueue(p,p["stage"])
        return p

    def enqueue(self,p,stage):
        current=self.store.get("projects",p["id"])
        if current["status"] in {"paused","blocked"}:
            p["status"]=current["status"]
        p["stage"]=stage
        self.store.put("projects",p)
        self.store.enqueue(p["team"][stage],stage,{"project_id":p["id"]},p["id"],priority=2)

    def check_budget(self,p,stage):
        if p["status"]!="running":
            raise PermissionError("Project is not running")
        elapsed=(datetime.now(timezone.utc)-datetime.fromisoformat(p["started_at"])).total_seconds()
        if elapsed>=p["time_budget_seconds"]:
            raise PermissionError("Project time budget exhausted")
        if stage in {"hypothesis","critique","code"}:
            reservation=2*(self.settings.context_length+self.settings.max_output_tokens)
            if p["reserved_tokens"]+reservation>p["token_budget"]:
                raise PermissionError("Token reservation budget exhausted (includes possible repair)")
            p["reserved_tokens"]+=reservation
            self.store.put("projects",p)
        if stage=="experiment" and p["experiments_used"]>=p["experiment_budget"]:
            raise PermissionError("Experiment budget exhausted")

    async def structured(self,p,stage,schema,prompt):
        agent=self.store.agent(p["team"][stage])
        trace={"id":uid("trace"),"project_id":p["id"],"agent_id":agent.id,"stage":stage,"prompt_version":"research/1.0.0","created_at":now(),"tokens":0,"seconds":0,"status":"running","model":self.router.route("coding" if stage=="code" else "reasoning").name}
        def usage(completion):
            trace["tokens"]+=completion.tokens
            trace["seconds"]+=completion.seconds
            trace.setdefault("attempts",[]).append({"output":completion.text,"tokens":completion.tokens})
            p["tokens"]+=completion.tokens
            p["status"]=self.store.get("projects",p["id"])["status"]
            self.store.put("projects",p)
        messages=[{"role":"system","content":POLICY+f"\nRole: {agent.role}. Personality: {agent.personality.model_dump_json()}"},{"role":"user","content":prompt}]
        try:
            output=await self.router.structured(messages,schema,self.settings.max_output_tokens,usage)
            trace.update(status="completed",output=output.model_dump())
            self.store.remember(agent.id,MemoryWrite(kind="research",content=output.model_dump_json()[:3000],sources=[p["id"]],confidence=.5))
            return output
        except Exception as exc:
            trace.update(status="failed",error=str(exc))
            raise
        finally:
            self.store.put("traces",trace)

    async def step(self,job):
        p=self.store.get("projects",job["project_id"])
        stage=job["kind"]
        if stage!=p["stage"]:
            raise PermissionError("Stale project stage; operator must inspect queued work")
        self.check_budget(p,stage)
        agent_id=job["agent_id"]
        if stage=="literature":
            enabled=self.store.setting("external_research",self.settings.external_research)
            if enabled:
                papers=await Literature(self.store,True).search(p["question"],agent_id)
                p["citations"]=[r["id"] for r in papers]
                for paper in papers:
                    link(self.store,p["id"],paper["id"],"CITES")
                if not papers:
                    p["limitations"].append("Literature search returned no quality-filtered records")
            else:
                p["limitations"].append("External literature disabled; prior art and novelty unassessed")
            self.handoff(p,stage,"hypothesis","Literature metadata available in project: "+json.dumps(p["citations"]))
        elif stage=="hypothesis":
            failures=[f for f in self.store.records("failures") if f.get("project_id")==p["id"]]
            papers=[self.store.get("papers",i) for i in p["citations"]]
            draft=await self.structured(p,stage,HypothesisDraft,"Question: "+p["question"]+"\nPropose one standard-library Python lexical retrieval improvement over word-overlap ranking. No embeddings are installed. Do not claim novelty. Our smoke corpus tests plumbing, not scientific validity. Describe a testable mechanism. Previous failures: "+json.dumps(failures)[-2000:]+"\nUntrusted literature metadata: "+json.dumps(papers)[:3000])
            h={"id":uid("hyp"),**draft.model_dump(),"creator":agent_id,"project_id":p["id"],"status":"REVIEWING","novelty":None,"generation":p["generation"],"created_at":now(),"parent_id":p["hypothesis_ids"][-1] if p["hypothesis_ids"] else None,"experiment_ids":[]}
            self.store.put("hypotheses",h)
            self.store.put("graph",{"id":h["id"],"kind":"Hypothesis","label":h["title"]})
            link(self.store,p["id"],h["id"],"PROPOSES")
            if h["parent_id"]:
                link(self.store,h["id"],h["parent_id"],"DERIVED_FROM")
            p["hypothesis_ids"].append(h["id"])
            self.store.event("HYPOTHESIS_CREATED",h["id"],h["title"])
            self.handoff(p,stage,"critique",json.dumps(h))
        elif stage=="critique":
            h=self.current_hypothesis(p)
            review=await self.structured(p,stage,Review,"Critically assess this unverified hypothesis. Identify leakage, weak baseline, prior art, confounders. Approve only if executable as an exploratory retrieval test; approval is not scientific validation. Hypothesis: "+json.dumps(h))
            h["review"]={**review.model_dump(),"reviewer":agent_id}
            h["status"]="APPROVED" if review.approved else "REJECTED"
            self.store.put("hypotheses",h)
            self.store.event("HYPOTHESIS_REVIEWED",h["id"],f"{h['status']}: {review.criticisms[0][:200]}")
            if review.approved:
                self.handoff(p,stage,"code",json.dumps(review.model_dump()))
            else:
                self.failure(p,h,"Critical review rejected the hypothesis",review.model_dump())
                self.next_generation_or_report(p)
        elif stage=="code":
            h=self.current_hypothesis(p)
            skills=self.store.records("skills")[:3]
            draft=await self.structured(p,stage,CodeDraft,"Implement this hypothesis as Python. Define retrieve(documents, queries, k): documents is a list of {id: str, text: str}; queries is a list of strings. Return a list of lists of at most k unique document IDs, one per query. Allowed imports: math,re,collections,heapq,itertools,functools,statistics,random,string. No files, network, print, exec, eval, dunder access. No hardcoded rankings. Return code in JSON. Hypothesis: "+json.dumps(h)+"\nPreviously execution-tested skills (not proven improvements): "+json.dumps([{k:s[k] for k in ("id","description","code")} for s in skills])[:1800])
            validate_code(draft.code)
            h["code"]=draft.code
            h["code_explanation"]=draft.explanation
            h["status"]="EXPERIMENTING"
            self.store.put("hypotheses",h)
            self.handoff(p,stage,"experiment","Candidate implementation passed static policy checks")
        elif stage in {"experiment","replication"}:
            h=self.current_hypothesis(p)
            if "experiment.run" not in self.store.agent(agent_id).permissions:
                raise PermissionError("Agent lacks experiment.run")
            # Each base experiment reserves a batch of 3 isolated seeds under one budget unit.
            seeds=[0] if stage=="experiment" else [1,2]
            dataset=json.loads((ROOT/"benchmarks/retrieval-smoke.json").read_text())
            for seed in seeds:
                if self.store.setting("paused",True) or self.store.get("projects",p["id"])["status"]!="running":
                    raise PermissionError("Human pause or stop requested")
                eid=uid("exp")
                exp={"id":eid,"project_id":p["id"],"hypothesis_id":h["id"],"agent_id":agent_id,"seed":seed,"status":"running","created_at":now(),"dataset_id":dataset["id"],"resource_limits":{"cpu":1,"memory_mb":256,"timeout_seconds":self.settings.sandbox_timeout},"code":h["code"],"code_hash":digest(h["code"]),"model":self.settings.model,"prompt_version":"research/1.0.0"}
                self.store.put("experiments",exp)
                self.store.event("EXPERIMENT_STARTED",eid,f"Seed {seed} in isolated container")
                try:
                    result=await self.benchmark.compare(eid,h["code"],dataset,seed)
                    exp.update(status="completed",result=result)
                except BaseException as exc:
                    exp.update(status="failed",error=type(exc).__name__+": "+str(exc))
                    self.store.put("experiments",exp)
                    self.failure(p,h,"Experiment execution failed",{"experiment_id":eid,"error":exp["error"]})
                    raise
                self.store.put("experiments",exp)
                h["experiment_ids"].append(eid)
                p["experiment_ids"].append(eid)
                self.store.put("hypotheses",h)
                self.store.put("projects",p)
                self.store.put("graph",{"id":eid,"kind":"Experiment","label":f"Seed {seed}"})
                link(self.store,eid,h["id"],"EVALUATES" if seed==0 else "REPLICATES")
                self.store.event("EXPERIMENT_FINISHED",eid,f"Measured NDCG {result['metrics']['baseline']['ndcg']:.3f} → {result['metrics']['candidate']['ndcg']:.3f}")
                self.store.remember(agent_id,MemoryWrite(kind="research",content="Observed experiment: "+json.dumps(result["metrics"])[:2700],sources=[eid],confidence=.9))
            if stage=="experiment":
                p["experiments_used"]+=1
                h["status"]="REPLICATION"
                self.store.put("hypotheses",h)
                self.handoff(p,stage,"replication","Independent reruns requested; result IDs: "+json.dumps(h["experiment_ids"]))
            else:
                results=[self.store.get("experiments",i)["result"] for i in h["experiment_ids"]]
                h["validation"]=validation_gate(results)
                h["status"]="REJECTED" if any(r["statistics"]["mean_difference"]<=0 for r in results) else "REPLICATION"
                h["replication_count"]=len(results)
                h["replication_success_rate"]=sum(r["statistics"]["mean_difference"]>0 for r in results)/len(results)
                self.store.put("hypotheses",h)
                if h["status"]=="REJECTED":
                    self.failure(p,h,"Candidate did not consistently improve retrieval",h["validation"])
                else:
                    self.learn_skill(h,agent_id)
                self.next_generation_or_report(p)
        elif stage=="report":
            p["status"]="completed"
            p["report"]=self.report(p)
            self.store.put("projects",p)
            target=self.settings.data_dir/"artifacts"/p["id"]
            target.mkdir(parents=True,exist_ok=True)
            (target/"report.md").write_text(p["report"],encoding="utf-8")
            self.store.event("PROJECT_COMPLETED",p["id"],"Research report generated; findings remain exploratory")

    def current_hypothesis(self,p):
        return self.store.get("hypotheses",p["hypothesis_ids"][-1])

    def handoff(self,p,current,next_stage,content):
        self.store.send(p["team"][current],p["team"][next_stage],content[:3000],"task_assignment")
        self.enqueue(p,next_stage)

    def failure(self,p,h,reason,evidence):
        self.store.put("failures",{"id":uid("failure"),"project_id":p["id"],"hypothesis_id":h["id"],"reason":reason,"evidence":evidence,"created_at":now()})
        self.store.remember(h["creator"],MemoryWrite(kind="failure",content=reason+": "+json.dumps(evidence)[:2500],sources=[h["id"]],importance=.9,confidence=.9))

    def next_generation_or_report(self,p):
        p["generation"]+=1
        reservation=6*(self.settings.context_length+self.settings.max_output_tokens)
        can_continue=p["generation"]<p["max_generations"] and p["reserved_tokens"]+reservation<=p["token_budget"] and p["experiments_used"]<p["experiment_budget"]
        self.enqueue(p,"hypothesis" if can_continue else "report")

    def learn_skill(self,h,agent_id):
        sid="skill_"+digest(h["code"])[:16]
        existing=next((s for s in self.store.records("skills") if s["id"]==sid),None)
        skill={"id":sid,"name":h["title"],"description":h["mechanism"],"creator":agent_id,"version":1,"inputs":"documents, queries, k","outputs":"ranked document IDs","code":h["code"],"tests":h["experiment_ids"],"reliability_score":1.,"usage_count":3+(existing["usage_count"] if existing else 0),"failure_count":0,"dependencies":"Python standard library","status":"execution-tested; retrieval benefit is exploratory"}
        self.store.put("skills",skill)
        agent=self.store.agent(agent_id)
        if sid not in agent.skills:
            agent.skills.append(sid)
        agent.reputation["successful_replications"]=agent.reputation.get("successful_replications",0)+3
        self.store.save_agent(agent)
        self.store.event("SKILL_CREATED",sid,h["title"])

    def report(self,p):
        lines=[f"# {p['title']}","",p["question"],"","## Methods","Standard-library retrieval candidates compared with a documented word-overlap baseline. Labels are kept outside candidate containers. Three seeds vary corpus order; these are not independent datasets.","","## Observed results"]
        for eid in p["experiment_ids"]:
            e=self.store.get("experiments",eid)
            if e.get("result"):
                r=e["result"]
                lines.extend([f"- {eid} / seed {e['seed']}: NDCG@3 {r['metrics']['baseline']['ndcg']:.4f} → {r['metrics']['candidate']['ndcg']:.4f}; paired 95% interval {r['statistics']['ci95']}."])
        if not p["experiment_ids"]:
            lines.append("NOT YET MEASURED. No successful experiments.")
        lines.extend(["","## Hypotheses and criticism"])
        for hid in p["hypothesis_ids"]:
            h=self.store.get("hypotheses",hid)
            lines.extend([f"### {h['title']} — {h['status']}",h["prediction"],"Criticism: "+"; ".join(h.get("review",{}).get("criticisms",[]))])
        lines.extend(["","## Limitations","Exploratory smoke fixture with 20 locally authored relevance labels. No novelty established. No answer generation, faithfulness, real tokenizer usage, GPU telemetry, or compute-cost measurements. Container wall time is not query latency. Repeated seeds share queries; statistical intervals use query pairs. No validated discovery is claimed.",*p["limitations"],"","## Sources"])
        for paper_id in p["citations"]:
            paper=self.store.get("papers",paper_id)
            lines.append(f"- [{paper['title']}]({paper['url']}) — metadata retrieved from Crossref; full text not reviewed.")
        lines.extend(["","## Future work","Evaluate on preregistered external corpora with independent held-out queries, stronger baselines, answer evaluation and calibrated cost measurements. Human prior-art and methodology review is required."])
        return "\n".join(lines)
