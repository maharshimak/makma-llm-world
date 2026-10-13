import {api} from './api';
type Tool={name:string;description:string;inputSchema:object;annotations:{readOnlyHint:boolean};execute:(input:unknown)=>Promise<unknown>};
export function registerTools(refresh:()=>Promise<void>) {
 const context=(document as Document & {modelContext?:{registerTool:(tool:Tool,options:{signal:AbortSignal})=>void|Promise<void>}}).modelContext;
 if(!context)return ()=>{};
 const controller=new AbortController();
 const tools:Tool[]=[{name:'read_civilization_metrics',description:'Read live counts and the paused state of this local civilization.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:true},execute:async input=>{if(!input||typeof input!=='object'||Object.keys(input).length)throw new Error('Expected an empty object');return api('/metrics')}},{name:'pause_civilization',description:'Pause scheduling. An in-flight operation may finish. Same action as the Pause control.',inputSchema:{type:'object',properties:{},additionalProperties:false},annotations:{readOnlyHint:false},execute:async input=>{if(!input||typeof input!=='object'||Object.keys(input).length)throw new Error('Expected an empty object');const result=await api('/world/pause',{});await refresh();return result}}];
 for(const tool of tools) {try {Promise.resolve(context.registerTool(tool,{signal:controller.signal})).catch(()=>{});}catch{/* Optional browser capability; UI remains available. */}}
 return ()=>controller.abort();
}
