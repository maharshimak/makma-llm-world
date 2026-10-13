"""Trusted evaluator. Computes metrics from rankings; never trusts model numbers."""
import hashlib
import json
import math
import platform
import random
import statistics
from pathlib import Path
from .schemas import now

BASELINE='''import re
def retrieve(documents, queries, k):
    def words(text): return set(re.findall(r"\\w+", text.lower()))
    indexed = [(d["id"], words(d["text"])) for d in documents]
    return [[doc_id for doc_id, terms in sorted(indexed, key=lambda row: -len(words(query) & row[1]))[:k]] for query in queries]
'''


def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()


def retrieval_metrics(rankings,labels,k=3):
    if len(rankings)!=len(labels) or not labels:
        raise ValueError("Nonempty matched rankings and labels required")
    rows=[]
    for ranking,relevant in zip(rankings,labels):
        if not relevant:
            raise ValueError("Each query needs at least one relevant document")
        hits=[int(doc in relevant) for doc in ranking[:k]]
        dcg=sum(hit/math.log2(i+2) for i,hit in enumerate(hits))
        ideal=sum(1/math.log2(i+2) for i in range(min(k,len(relevant))))
        rows.append({"recall":sum(hits)/len(relevant),"precision":sum(hits)/k,"mrr":next((1/(i+1) for i,h in enumerate(hits) if h),0),"ndcg":dcg/ideal})
    return {**{m:statistics.mean(r[m] for r in rows) for m in rows[0]},"k":k,"per_query":rows}


def paired_bootstrap(baseline,candidate,seed=42,iterations=2000):
    if len(baseline)!=len(candidate) or not baseline:
        raise ValueError("Paired samples required")
    differences=[c-b for b,c in zip(baseline,candidate)]
    rng=random.Random(seed)
    means=sorted(statistics.mean(rng.choices(differences,k=len(differences))) for _ in range(iterations))
    sd=statistics.stdev(differences) if len(differences)>1 else 0
    return {"mean_difference":statistics.mean(differences),"ci95":[means[int(iterations*.025)],means[int(iterations*.975)]],"paired_effect_size":statistics.mean(differences)/sd if sd else None,"independent_queries":len(differences),"method":"paired query bootstrap; exploratory, no multiple-testing correction"}


class Benchmark:
    def __init__(self,sandbox,artifact_dir: Path):
        self.sandbox=sandbox
        self.artifact_dir=artifact_dir

    async def compare(self,experiment_id,code,dataset,seed=0):
        docs=list(dataset["documents"])
        random.Random(seed).shuffle(docs)
        queries=[q["text"] for q in dataset["queries"]]
        labels=[q["relevant"] for q in dataset["queries"]]
        # Alternating order reduces systematic container warm-up advantage.
        runs={}
        for label in (["baseline","candidate"] if seed%2==0 else ["candidate","baseline"]):
            runs[label]=await self.sandbox.run(BASELINE if label=="baseline" else code,docs,queries,3,seed)
        metrics={label:retrieval_metrics(run["rankings"],labels) for label,run in runs.items()}
        counts={d["id"]:len(d["text"].split()) for d in docs}
        for label,run in runs.items():
            metrics[label].update(batch_wall_seconds=run["wall_seconds"],batch_throughput=len(queries)/run["wall_seconds"],retrieved_word_count=sum(counts[i] for ranking in run["rankings"] for i in ranking),answer_accuracy=None,faithfulness=None,llm_tokens=None,ram_mb=None,vram_mb=None,cpu_seconds=None,estimated_compute_cost=None,latency_p50=None,latency_p95=None)
        stats=paired_bootstrap([r["ndcg"] for r in metrics["baseline"]["per_query"]],[r["ndcg"] for r in metrics["candidate"]["per_query"]])
        result={"id":experiment_id,"created_at":now(),"seed":seed,"dataset_id":dataset["id"],"dataset_hash":digest(dataset),"code_hash":digest(code),"baseline_hash":digest(BASELINE),"metrics":metrics,"statistics":stats,"rankings":{k:v["rankings"] for k,v in runs.items()},"image_id":runs["candidate"]["image_id"],"host":{"system":platform.system(),"machine":platform.machine(),"python":platform.python_version()},"measurement_scope":"Retrieval only. Wall time includes container startup. Word counts are not tokenizer counts.","benchmark_scope":dataset.get("scope","unclassified"),"reproduced":True}
        target=self.artifact_dir/experiment_id
        target.mkdir(parents=True,exist_ok=True)
        for filename,value in {"candidate.py":code,"baseline.py":BASELINE,"dataset.json":json.dumps(dataset,indent=2),"result.json":json.dumps(result,indent=2),"environment.json":json.dumps({"image_id":result["image_id"],"network":"none","cpu":1,"memory_mb":256,"seed":seed,"host":result["host"]},indent=2)}.items():
            (target/filename).write_text(value,encoding="utf-8")
        return result


def validation_gate(results,novelty_reviewed=False,min_queries=100):
    reasons=[]
    if len(results)<3:
        reasons.append("At least three successful replications required")
    if len({r["dataset_id"] for r in results})<2:
        reasons.append("At least two datasets required")
    if not results or any(r.get("benchmark_scope")!="research" for r in results):
        reasons.append("Smoke fixtures cannot establish a discovery")
    if any(r["statistics"]["independent_queries"]<min_queries or r["statistics"]["ci95"][0]<=0 for r in results):
        reasons.append("Insufficient independent samples or confidence interval overlaps zero")
    if any(r["metrics"]["candidate"]["recall"]<=r["metrics"]["baseline"]["recall"] for r in results):
        reasons.append("Recall improvement did not replicate")
    if not novelty_reviewed:
        reasons.append("Human novelty and methodology review required")
    # This first evaluator cannot validate the full latency/token/cost objective.
    reasons.append("Answer quality, token use and compute cost are not yet measured")
    return {"eligible":not reasons,"reasons":reasons}

