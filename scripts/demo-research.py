"""Run one real local project. Never substitutes mock providers or host code."""
import asyncio
from makma.config import Settings
from makma.store import Store
from makma.kernel import seed
from makma.providers import make_provider,ModelRouter
from makma.sandbox import DockerSandbox
from makma.research import Research
from makma.schemas import ProjectCreate

async def main():
    settings=Settings();store=Store(settings.data_dir/"makma.sqlite3");seed(store)
    provider=make_provider(settings);sandbox=DockerSandbox(settings.sandbox_image)
    model_health=await provider.health();sandbox_health=await sandbox.health()
    print("Model:",model_health);print("Sandbox:",sandbox_health)
    if not model_health.get("available") or not sandbox_health.get("available"):
        await provider.close()
        raise RuntimeError("Start Ollama and Docker and build the sandbox before running this demo.")
    research=Research(store,ModelRouter(provider,settings.model),sandbox,settings)
    project=research.create(ProjectCreate(title="RAG retrieval experiment",question="Can inverse document frequency and length normalization improve retrieval over word overlap?",experiment_budget=1,token_budget=64000))
    project=research.start(project["id"])
    try:
        while (job:=store.claim_job(project["id"])):
            print("Running",job["kind"],flush=True)
            try:
                await research.step(job)
                store.finish_job(job["id"],"completed")
            except Exception as exc:
                store.finish_job(job["id"],"blocked",str(exc))
                p=store.get("projects",project["id"]);p.update(status="blocked",error=str(exc));store.put("projects",p)
                raise
        print("Report:",store.get("projects",project["id"]).get("report"))
    finally:
        await provider.close()

if __name__=="__main__":asyncio.run(main())
