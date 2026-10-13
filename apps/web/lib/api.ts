export interface Agent { id:string; name:string; role:string; state:string; permissions:string[]; goals:string[]; skills:string[]; beliefs:Record<string,unknown>[]; personality:Record<string,number>; reputation:Record<string,number>; relationships:Record<string,number> }
export interface Memory { id:string; kind:string; content:string; confidence:number; sources:string[] }
export interface Event { seq:number; type:string; summary:string; created_at:string }
export interface Health { database:boolean; memory:boolean; scheduler:boolean; paused:boolean; external_research:boolean; model:{available:boolean; model:string; detail?:string}; sandbox:{available:boolean; detail?:string} }
export interface Metrics { agents:number; active_agents:number; projects:number; hypotheses:number; experiments:number; completed_experiments:number; discoveries:number; papers:number; skills:number; failures:number; tokens:number; inference_seconds:number; paused:boolean }
export interface Project { id:string; title:string; question:string; status:string; stage:string; tokens:number; reserved_tokens:number; token_budget:number; experiment_ids:string[]; hypothesis_ids:string[]; experiments_used:number; experiment_budget:number; error?:string; report?:string; limitations:string[] }
export interface Hypothesis { id:string; title:string; status:string; mechanism:string; prediction:string; review?:{criticisms:string[]; controls:string[]}; validation?:{reasons:string[]}; code?:string; replication_count?:number; project_id:string }
export interface Experiment { id:string; hypothesis_id:string; status:string; seed:number; code:string; error?:string; result?:{ metrics:Record<string,{recall:number;precision:number;mrr:number;ndcg:number;batch_wall_seconds:number;retrieved_word_count:number}>; statistics:{mean_difference:number;ci95:number[]}; image_id:string; dataset_hash:string; measurement_scope:string } }
export interface Paper { id:string; title:string; url:string; authors:string[]; source:string }
export interface Skill { id:string; name:string; description:string; code:string; usage_count:number; status:string }
export interface Job { id:string; kind:string; agent_id:string; project_id:string|null; status:string; error:string|null }
export interface Graph {nodes:{id:string;kind:string;label:string}[];edges:{id:string;source:string;target:string;relation:string}[]}
export async function api<T>(path:string,body?:unknown):Promise<T> {
 const response=await fetch('/api'+path,{method:body===undefined?'GET':'POST',headers:body===undefined?{}:{'Content-Type':'application/json','X-Makma-Client':'local-console'},body:body===undefined?undefined:JSON.stringify(body)});
 if(!response.ok) { const err=await response.json().catch(()=>({detail:'Local API unavailable'})) as {detail:unknown}; throw new Error(typeof err.detail==='string'?err.detail:JSON.stringify(err.detail)); }
 return response.json();
}
