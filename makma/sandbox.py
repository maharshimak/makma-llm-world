"""Generated code runs only inside a constrained Docker container.

No bind mounts: input/code go through stdin. No host interpreter fallback exists.
"""
import ast
import asyncio
import json
import shutil
import time
from .schemas import uid


class SandboxUnavailable(RuntimeError):
    pass


class SandboxFailure(RuntimeError):
    pass


ALLOWED_IMPORTS={"math","re","collections","heapq","itertools","functools","statistics","random","string"}


def validate_code(code: str):
    if len(code.encode())>16000:
        raise PermissionError("Code exceeds 16 KB policy")
    tree=ast.parse(code)
    if not any(isinstance(n,ast.FunctionDef) and n.name=="retrieve" for n in tree.body):
        raise PermissionError("Candidate must define retrieve(documents, queries, k)")
    for node in ast.walk(tree):
        if isinstance(node,(ast.Import,ast.ImportFrom)):
            modules=[a.name.split('.')[0] for a in node.names] if isinstance(node,ast.Import) else [(node.module or '').split('.')[0]]
            if isinstance(node,ast.ImportFrom) and node.level:
                raise PermissionError("Relative imports denied")
            if any(m not in ALLOWED_IMPORTS for m in modules):
                raise PermissionError("Import outside standard-library allowlist")
        if isinstance(node,ast.Name) and (node.id.startswith("__") or node.id in {"open","exec","eval","compile","globals","locals","getattr","setattr","vars","input","breakpoint","help"}):
            raise PermissionError(f"Forbidden operation: {node.id}")
        if isinstance(node,ast.Attribute) and node.attr.startswith("_"):
            raise PermissionError("Private/dunder attribute access denied")
    # Static validation is defense in depth, never the isolation boundary.


class DockerSandbox:
    def __init__(self,image="makma-sandbox:0.1",timeout=45):
        self.image=image
        self.timeout=timeout
        self.active=set()

    async def _command(self,*args,timeout=10):
        proc=await asyncio.create_subprocess_exec("docker",*args,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
        try:
            out,err=await asyncio.wait_for(proc.communicate(),timeout)
        except asyncio.TimeoutError:
            proc.kill()
            await proc.wait()
            raise SandboxUnavailable("Docker command timed out")
        if proc.returncode:
            raise SandboxUnavailable(err.decode(errors="replace")[:1000])
        return out.decode()

    async def health(self):
        if not shutil.which("docker"):
            return {"available":False,"detail":"Docker CLI is not installed","image":self.image}
        try:
            version=(await self._command("info","--format","{{.ServerVersion}}" )).strip()
            image_id=(await self._command("image","inspect",self.image,"--format","{{.Id}}" )).strip()
            return {"available":True,"version":version,"image":self.image,"image_id":image_id,"detail":"Ready; network disabled"}
        except (OSError,SandboxUnavailable) as exc:
            return {"available":False,"image":self.image,"detail":str(exc)[:1000]}

    def command(self,name):
        return ["docker","run","--rm","--pull=never","--name",name,"--label","makma.experiment=true","-i","--network=none","--read-only","--cap-drop=ALL","--security-opt=no-new-privileges","--user=65534:65534","--cpus=1","--memory=256m","--memory-swap=256m","--pids-limit=32","--ulimit","nofile=64:64","--log-driver=none","--tmpfs","/tmp:rw,noexec,nosuid,size=16m",self.image]

    async def run(self,code,documents,queries,k=3,seed=0):
        validate_code(code)
        health=await self.health()
        if not health["available"]:
            raise SandboxUnavailable(health["detail"])
        name=uid("makma")
        data=json.dumps({"code":code,"documents":documents,"queries":queries,"k":k,"seed":seed}).encode()
        if len(data)>2_000_000:
            raise SandboxFailure("Input exceeds 2 MB")
        self.active.add(name)
        start=time.perf_counter()
        proc=None
        async def read_bounded(stream):
            result=bytearray()
            while chunk:=await stream.read(8192):
                result.extend(chunk)
                if len(result)>256000:
                    raise SandboxFailure("Sandbox output exceeds 256 KB")
            return bytes(result)
        try:
            proc=await asyncio.create_subprocess_exec(*self.command(name),stdin=asyncio.subprocess.PIPE,stdout=asyncio.subprocess.PIPE,stderr=asyncio.subprocess.PIPE)
            async def execute():
                proc.stdin.write(data)
                await proc.stdin.drain()
                proc.stdin.close()
                out,err=await asyncio.gather(read_bounded(proc.stdout),read_bounded(proc.stderr))
                await proc.wait()
                return out,err
            out,err=await asyncio.wait_for(execute(),self.timeout)
            if proc.returncode:
                raise SandboxFailure(err.decode(errors="replace")[:3000])
            result=json.loads(out)
            rankings=result["rankings"]
            known={d["id"] for d in documents}
            if not isinstance(rankings,list) or len(rankings)!=len(queries):
                raise SandboxFailure("Candidate did not return one ranking per query")
            for ranking in rankings:
                if not isinstance(ranking,list) or len(ranking)>k or any(not isinstance(i,str) or i not in known for i in ranking) or len(set(ranking))!=len(ranking):
                    raise SandboxFailure("Rankings must contain unique, known document IDs")
            return {"rankings":rankings,"wall_seconds":time.perf_counter()-start,"image_id":health["image_id"],"seed":seed,"stderr":err.decode(errors="replace")[:3000]}
        except asyncio.TimeoutError as exc:
            raise SandboxFailure(f"Sandbox exceeded {self.timeout}s") from exc
        except (ValueError,KeyError,TypeError) as exc:
            raise SandboxFailure("Invalid sandbox response") from exc
        finally:
            try:
                await self._command("rm","-f",name)
            except (OSError,SandboxUnavailable):
                pass
            if proc and proc.returncode is None:
                proc.kill()
                await proc.wait()
            self.active.discard(name)

    async def stop_all(self):
        for name in list(self.active):
            try:
                await self._command("rm","-f",name)
            except (OSError,SandboxUnavailable):
                pass

