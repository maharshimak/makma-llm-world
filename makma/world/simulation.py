"""Needs/schedules drive physical intentions; measured research drives lab use.

World state is operator-authoritative. The trusted local engine acknowledges
movement, not cognition. Disconnected clients never cause invented activity.
"""
import asyncio
import copy
import json
import math
import time
from ..schemas import Agent,Role,MemoryWrite,now,uid
from ..kernel import POLICY
from .contracts import WorldActionV1,WorldEventV1,Vector3,ConversationReplyV1

LOCATIONS=[
    ("university","Mak'ma University",-3300,2600,900,700),
    ("ai_lab","AI Research Laboratory",0,2600,900,700),
    ("systems_lab","Systems Laboratory",3300,2600,900,700),
    ("library","Library",-3300,-2200,800,600),
    ("cafe","Café",0,-2200,700,500),
    ("restaurant","Restaurant",3300,-2200,800,600),
    ("apartments","Apartments",-6500,2500,900,700),
    ("market","Supermarket",-6500,-2200,750,600),
    ("office","Small office",6500,2500,800,600),
    ("clinic","Clinic",6500,-2200,750,600),
    ("park","Campus park",3300,5200,1000,650),
    ("plaza","Public plaza",0,0,800,650),
    ("transit","Transit stop",-3300,0,400,200),
    ("security","Community safety office",6500,5200,650,450),
]


def distance(a,b):
    return math.dist([a["x"],a["y"]],[b["x"],b["y"]])


class World:
    def __init__(self,store,router,settings):
        self.store,self.router,self.settings=store,router,settings
        self.lock=asyncio.Lock()
        self.client_id=None
        self.client_seen=0.
        self.task=None
        self.closed=False
        self.seed()

    def seed(self):
        if self.store.records("world"):
            return
        locations=[{"id":i,"name":name,"position":{"x":x,"y":y,"z":90},"half_width":w,"half_depth":h,"door":{"x":x,"y":y-h,"z":90},"interior":i not in {"park","plaza","transit"}} for i,name,x,y,w,h in LOCATIONS]
        profiles=[("AI researcher","ai_lab",Role.scientist)]*4+[("Research engineer","systems_lab",Role.engineer)]*3+[("Professor","university",Role.professor)]*2+[("Student","university",Role.student)]*2+[("Statistician","ai_lab",Role.statistician),("Critic / reviewer","ai_lab",Role.critic),("Librarian","library",Role.librarian),("Café worker","cafe",Role.cafe_worker),("Shopkeeper","market",Role.shopkeeper),("Journalist","office",Role.journalist),("Entrepreneur","office",Role.entrepreneur),("Doctor","clinic",Role.doctor),("Police officer","security",Role.police),("Citizen","park",Role.citizen)]
        taken=set()
        citizens=[]
        extra_names=["Mira","Theo","Sara","Leo","Jun","Nora","Ravi","Elena","Omar","Lena","Zoe","Kai"]
        for index,(profession,work,role) in enumerate(profiles):
            agent=next((a for a in self.store.agents() if a.role==role and a.id not in taken),None)
            if agent is None:
                agent=Agent(name=extra_names[index%len(extra_names)]+f" {index+1:02}",role=role,permissions=["message","knowledge.query","reflect"],specialization=[profession])
                self.store.save_agent(agent)
            taken.add(agent.id)
            position={"x":-6500+(index%5-2)*100,"y":2450+(index//5-2)*100,"z":90}
            citizens.append({"id":agent.id,"name":agent.name,"profession":profession,"home":"apartments","workplace":work,"age":22+index,"position":position,"location":"apartments","activity":"rest","intention":"Prepare for the day","energy":.75,"hunger":.25,"stress":.1,"mood":"rested","focus":.8,"money":10000,"inventory":{"food":2},"salary":1200,"rent":300,"lod":1,"action_id":None,"plan":[],"current_goal":None,"research_job":None,"last_social_minute":-1000,"last_salary_day":0,"last_rent_day":0,"activity_since":420.,"path_failures":0})
        objects=[]
        for location in locations:
            for index in range(8 if location["id"] in {"ai_lab","systems_lab","apartments","university"} else 3):
                objects.append({"id":f"{location['id']}_object_{index}","location":location["id"],"kind":"bed" if location["id"]=="apartments" else "table" if location["id"] in {"cafe","restaurant"} else "workstation","position":{"x":location["position"]["x"]+(index%4-1.5)*240,"y":location["position"]["y"]+(index//4)*240,"z":90},"reserved_by":None})
        self.store.put("world",{"id":"campus","version":1,"tick":0,"sim_minutes":420.,"paused":True,"speed":1,"citizens":citizens,"locations":locations,"objects":objects,"actions":[],"businesses":[{"id":"cafe","money":50000,"inventory":500},{"id":"market","money":50000,"inventory":500}],"treasury":1000000,"mode":"headless","player":{"position":{"x":0,"y":0,"z":90}},"saved_at":now()})
        self.store.event("WORLD_CREATED","campus",f"Campus populated with {len(citizens)} persistent citizens")

    def state(self):
        return self.store.get("world","campus")

    def save(self,s):
        s["saved_at"]=now()
        self.store.put("world",s)

    def snapshot(self):
        s=self.state()
        s["bridge_connected"]=time.monotonic()-self.client_seen<8
        return s

    def public_agent(self,aid):
        c=next((c for c in self.state()["citizens"] if c["id"]==aid),None)
        if c is None:raise KeyError(aid)
        return {k:c[k] for k in ["id","name","profession","location","activity","intention","mood"]}

    async def start(self):
        self.task=asyncio.create_task(self.loop())

    async def loop(self):
        last=time.monotonic()
        while not self.closed:
            await asyncio.sleep(.5)
            current=time.monotonic()
            try:
                await self.advance(min(current-last,2))
            except Exception as exc:
                self.store.event("WORLD_ERROR","campus",f"World paused: {type(exc).__name__}: {exc}")
                s=self.state();s["paused"]=True;self.save(s)
            last=current

    async def close(self):
        self.closed=True
        if self.task:
            self.task.cancel()
            await asyncio.gather(self.task,return_exceptions=True)

    async def control(self,paused,speed):
        async with self.lock:
            s=self.state();s.update(paused=paused,speed=speed);self.save(s)
            self.store.event("WORLD_CLOCK_CHANGED","campus",f"Clock {'paused' if paused else 'running'} at {speed}x")
            return {"paused":paused,"speed":speed}

    async def heartbeat(self,client_id,player_position=None):
        async with self.lock:
            if self.client_id and self.client_id!=client_id and time.monotonic()-self.client_seen<8:
                raise PermissionError("Another engine owns the active world bridge lease")
            self.client_id=client_id;self.client_seen=time.monotonic()
            if player_position is not None:
                s=self.state();s["player"]["position"]=player_position.model_dump();self.save(s)
            return {"version":1,"client_id":client_id,"lease_seconds":8,"tick":self.state()["tick"]}

    def reserve(self,s,c,location):
        existing=next((o for o in s["objects"] if o["reserved_by"]==c["id"]),None)
        if existing:return existing
        available=next((o for o in s["objects"] if o["location"]==location and o["reserved_by"] is None),None)
        if available:available["reserved_by"]=c["id"]
        return available

    def release(self,s,aid):
        for obj in s["objects"]:
            if obj["reserved_by"]==aid:obj["reserved_by"]=None

    def issue(self,s,c,kind,target,position,activity):
        action=WorldActionV1(agent_id=c["id"],action=kind,target=target,position=Vector3(**position),activity=activity,created_tick=s["tick"]).model_dump()
        s["actions"].append(action)
        c["action_id"]=action["id"]
        c["intention"]=activity
        c["activity"]="walk" if kind=="go_to" else activity
        self.store.event("WORLD_ACTION_ISSUED",c["id"],f"{c['name']}: {kind} → {target} ({activity})")

    def destination(self,s,c):
        hour=(s["sim_minutes"]%1440)/60
        if c["energy"]<.15 or hour>=22 or hour<7:return c["home"],"sleep"
        if c["hunger"]>.65:return "cafe","eat"
        if c["research_job"]:return c["workplace"],"research"
        if 9<=hour<17:return c["workplace"],"work"
        if 17<=hour<20:return "park","socialize"
        if 7<=hour<9:return "cafe","breakfast"
        return c["home"],"rest"

    def complete(self,s,c,action,position):
        if action["status"]!="pending":return
        action["status"]="completed";c["action_id"]=None;c["position"]=position;c["activity_since"]=s["sim_minutes"]
        if action["action"]=="go_to":
            c["location"]=action["target"];c["activity"]="idle"
            self.store.event("AGENT_ENTERED_LOCATION",c["id"],f"{c['name']} arrived at {action['target']}")
            self.store.remember(c["id"],MemoryWrite(content=f"Arrived at {action['target']} to {action['activity']}.",kind="episodic",confidence=1,importance=.2,sources=[action["id"]]))
        else:
            c["activity"]=action["activity"]
            self.store.event("OBJECT_USED",c["id"],f"{c['name']} began {action['activity']}")

    async def acknowledge(self,client_id,event:WorldEventV1):
        async with self.lock:
            if client_id!=self.client_id or time.monotonic()-self.client_seen>=8:
                raise PermissionError("World bridge lease expired; resynchronize first")
            s=self.state();c=next((c for c in s["citizens"] if c["id"]==event.agent_id),None)
            action=next((a for a in s["actions"] if a["id"]==event.action_id and a["agent_id"]==event.agent_id),None)
            if c is None or action is None:raise KeyError(event.action_id)
            if action["status"]!="pending":return {"status":"duplicate","tick":s["tick"]}
            if c["action_id"]!=action["id"]:raise ValueError("Stale world action")
            if event.event=="action_completed":
                if distance(event.position.model_dump(),action["position"])>150:raise ValueError("Completion reported too far from target")
                self.complete(s,c,action,event.position.model_dump())
            else:
                action["status"]="failed";c["action_id"]=None;c["path_failures"]+=1;c["activity"]="path_failed"
                self.release(s,c["id"])
                self.store.remember(c["id"],MemoryWrite(kind="failure",content="Navigation failed: "+event.reason,sources=[action["id"]],confidence=1))
                self.store.event("NAVIGATION_FAILED",c["id"],event.reason)
            self.save(s)
            return {"status":"accepted","tick":s["tick"]}

    def pay_day(self,s,c):
        day=int(s["sim_minutes"]//1440)
        if c["last_salary_day"]<day and s["treasury"]>=c["salary"]:
            c["money"]+=c["salary"];s["treasury"]-=c["salary"];c["last_salary_day"]=day
            self.store.event("SALARY_PAID",c["id"],f"{c['name']} received {c['salary']} simulation credits")
        if c["last_rent_day"]<day and c["money"]>=c["rent"]:
            c["money"]-=c["rent"];s["treasury"]+=c["rent"];c["last_rent_day"]=day

    def eat(self,s,c):
        business=next(b for b in s["businesses"] if b["id"]=="cafe")
        if c["money"]>=50 and business["inventory"]>0:
            c["money"]-=50;business["money"]+=50;business["inventory"]-=1;c["hunger"]=max(0,c["hunger"]-.45)
            self.store.event("ITEM_PURCHASED",c["id"],f"{c['name']} bought a meal for 50 simulation credits")

    def socialize(self,s,c):
        if s["sim_minutes"]-c["last_social_minute"]<30:return
        other=next((o for o in s["citizens"] if o["id"]!=c["id"] and o["location"]==c["location"] and not o["action_id"] and s["sim_minutes"]-o["last_social_minute"]>=30),None)
        if not other:return
        c["last_social_minute"]=other["last_social_minute"]=s["sim_minutes"]
        self.store.event("SOCIAL_ENCOUNTER",c["id"],f"{c['name']} met {other['name']} at {c['location']}")
        for first,second in [(c,other),(other,c)]:
            agent=self.store.agent(first["id"])
            agent.relationships[second["id"]]=min(1,agent.relationships.get(second["id"],0)+.02)
            self.store.save_agent(agent)
            self.store.remember(first["id"],MemoryWrite(kind="social",content=f"Met {second['name']} at {c['location']}.",sources=[second["id"]],confidence=1,importance=.3))
        # This records an encounter, not a fabricated conversation. Dialogue needs inference.
        self.store.send(c["id"],other["id"],f"We met at {c['location']}. My current activity is {c['activity']}.","message")

    async def advance(self,real_seconds):
        async with self.lock:
            s=self.state()
            if s["paused"]:return
            seconds=max(0,min(real_seconds,2))*s["speed"]
            dt=seconds/60
            s["sim_minutes"]+=dt;s["tick"]+=1
            connected=time.monotonic()-self.client_seen<8
            s["mode"]="engine" if connected else "headless"
            pending_jobs=self.store.jobs()
            for c in s["citizens"]:
                self.pay_day(s,c)
                c["hunger"]=min(1,c["hunger"]+dt*.0015)
                c["energy"]=max(0,min(1,c["energy"]+dt*(.006 if c["activity"]=="sleep" else -.0007)))
                c["mood"]="tired" if c["energy"]<.25 else "hungry" if c["hunger"]>.65 else "focused" if c["activity"] in {"research","work"} else "calm"
                c["lod"]=3 if connected and distance(c["position"],s["player"]["position"])<1500 else 1
                job=next((j for j in pending_jobs if j["agent_id"]==c["id"] and j["status"] in {"queued","running"} and j["project_id"]),None)
                c["research_job"]=job["id"] if job else None
                current=next((a for a in s["actions"] if a["id"]==c["action_id"]),None)
                if current and current["status"]=="pending":
                    if not connected:
                        dist=distance(c["position"],current["position"])
                        travel=140*seconds
                        if current["action"]!="go_to" or dist<=travel:
                            self.complete(s,c,current,copy.deepcopy(current["position"]))
                        else:
                            for axis in ["x","y"]:c["position"][axis]+=(current["position"][axis]-c["position"][axis])*travel/dist
                    continue
                target,activity=self.destination(s,c)
                if c["location"]!=target:
                    self.release(s,c["id"])
                    location=next(l for l in s["locations"] if l["id"]==target)
                    c["plan"]=[f"Go to {target}",activity]
                    self.issue(s,c,"go_to",target,location["position"],activity)
                elif activity in {"sleep","research","work","eat","breakfast"} and c["activity"]!=activity:
                    obj=self.reserve(s,c,target)
                    if obj:self.issue(s,c,"use_object",obj["id"],obj["position"],activity)
                    else:c["activity"]="waiting_for_object"
                else:
                    if c["activity"] in {"eat","breakfast"} and s["sim_minutes"]-c["activity_since"]>=10:
                        self.eat(s,c);c["activity"]="rest";self.release(s,c["id"])
                    if activity in {"socialize","rest"}:c["activity"]=activity
                    if c["activity"] in {"rest","socialize","work","breakfast","eat"}:self.socialize(s,c)
            # Keep bounded ack history; immutable global events preserve older transitions.
            s["actions"]=[a for a in s["actions"] if a["status"]=="pending"]+[a for a in s["actions"] if a["status"]!="pending"][-200:]
            self.save(s)

    def ready_for_research(self,agent_id):
        s=self.state()
        if not self.store.setting("embodied_research",False):return True
        citizen=next((c for c in s["citizens"] if c["id"]==agent_id),None)
        return citizen is not None and citizen["location"]==citizen["workplace"] and citizen["activity"]=="research" and not s["paused"]

    async def converse(self,agent_id,text):
        # Player context is restricted to one agent's experiences, never world snapshot.
        c=next((c for c in self.state()["citizens"] if c["id"]==agent_id),None)
        if c is None:raise KeyError(agent_id)
        used=self.store.setting("world_dialogue_reserved",0)
        reserve=2*(self.settings.context_length+self.settings.max_output_tokens)
        if used+reserve>self.settings.token_budget:raise PermissionError("World dialogue budget exhausted")
        self.store.set_setting("world_dialogue_reserved",used+reserve)
        agent=self.store.agent(agent_id)
        context={"name":agent.name,"profession":c["profession"],"current_location":c["location"],"activity":c["activity"],"goals":agent.goals[-5:],"memories":self.store.memories(agent_id,text,limit=4),"question":text}
        reply=await self.router.structured([{"role":"system","content":POLICY+" Answer a nearby player's question using only your actual private state. Say when you do not know. Do not claim to be conscious."},{"role":"user","content":json.dumps(context)}],ConversationReplyV1,512)
        self.store.remember(agent_id,MemoryWrite(kind="social",content=f"Player asked: {text}\nI replied: {reply.reply}",importance=.6,confidence=1))
        cid=uid("conversation")
        self.store.put("conversations",{"id":cid,"agent_id":agent_id,"input":text,"reply":reply.reply,"created_at":now()})
        self.store.event("CONVERSATION_FINISHED",agent_id,f"{agent.name} spoke with the player")
        return {"version":1,"id":cid,"agent_id":agent_id,**reply.model_dump()}
