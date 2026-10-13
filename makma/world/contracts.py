from typing import Literal
from pydantic import Field
from ..schemas import Schema,uid


class Vector3(Schema):
    x:float=Field(default=0,ge=-50000,le=50000,allow_inf_nan=False)
    y:float=Field(default=0,ge=-50000,le=50000,allow_inf_nan=False)
    z:float=Field(default=90,ge=-1000,le=10000,allow_inf_nan=False)


class WorldActionV1(Schema):
    version:Literal[1]=1
    id:str=Field(default_factory=lambda:uid("action"))
    agent_id:str
    action:Literal["go_to","use_object","talk_to","idle"]
    target:str
    position:Vector3
    activity:str
    status:Literal["pending","completed","failed"]="pending"
    created_tick:int
    attempts:int=0


class WorldEventV1(Schema):
    version:Literal[1]=1
    action_id:str
    agent_id:str
    event:Literal["action_completed","action_failed"]
    position:Vector3
    reason:str=Field(default="",max_length=500)


class WorldControlV1(Schema):
    version:Literal[1]=1
    paused:bool
    speed:Literal[1,5,10,20,100]=1


class ConversationInputV1(Schema):
    version:Literal[1]=1
    agent_id:str
    text:str=Field(min_length=1,max_length=1200)


class ConversationReplyV1(Schema):
    reply:str=Field(min_length=1,max_length=1500)
    confidence:float=Field(ge=0,le=1)


class BridgeHeartbeatV1(Schema):
    version:Literal[1]=1
    client_id:str=Field(min_length=1,max_length=80)
    player_position:Vector3|None=None
