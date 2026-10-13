"""Public provenance catalog, with opt-in requests to fixed literature APIs."""
import hashlib
import httpx
from .schemas import now, uid


class Literature:
    def __init__(self, store, enabled=False, transport=None):
        self.store=store
        self.enabled=enabled
        self.transport=transport

    async def search(self, query: str, agent_id: str, limit=5):
        if not self.enabled:
            raise PermissionError("External literature access is disabled. Enable it in the control center; search queries will be sent to Crossref.")
        async with httpx.AsyncClient(timeout=20,transport=self.transport,trust_env=False) as client:
            response=await client.get("https://api.crossref.org/works",params={"query.bibliographic":query[:500],"rows":min(limit,10),"select":"DOI,title,author,published,URL,type,is-referenced-by-count"},headers={"User-Agent":"Makma/0.1 (local research catalog)"})
            response.raise_for_status()
            items=response.json()["message"]["items"]
        papers=[]
        for item in items:
            if not item.get("DOI") or not item.get("title") or item.get("type") not in {"journal-article","proceedings-article","posted-content","book-chapter"}:
                continue
            paper={"id":"paper_"+hashlib.sha256(item["DOI"].encode()).hexdigest()[:16],"title":str(item["title"][0])[:1000],"doi":item["DOI"],"url":"https://doi.org/"+item["DOI"],"authors":[" ".join([a.get("given",""),a.get("family","")]).strip() for a in item.get("author",[])[:20]],"publication_date":item.get("published",{}).get("date-parts",[]),"retrieved_at":now(),"agent_id":agent_id,"source":"Crossref","evidence_type":"bibliographic_metadata","full_text_reviewed":False}
            self.store.put("papers",paper)
            self.store.put("graph",{"id":paper["id"],"kind":"Paper","label":paper["title"]})
            papers.append(paper)
        self.store.event("LITERATURE_RETRIEVED",agent_id,f"Indexed {len(papers)} DOI records from Crossref")
        return papers

    def query(self,text):
        terms=set(text.lower().split())
        items=self.store.records("papers")+self.store.records("publications")
        return sorted([i for i in items if any(t in str(i).lower() for t in terms)], key=lambda i:sum(t in str(i).lower() for t in terms),reverse=True)[:20]


def link(store, source, target, relation):
    rid=f"{source}:{relation}:{target}"
    store.put("edges",{"id":rid,"source":source,"target":target,"relation":relation})

