// Local production proxy; Vite's development proxy serves the same paths.
export const dynamic = 'force-dynamic';
async function proxy(request:Request,context:{params:Promise<{path:string[]}>}){
 const {path}=await context.params;
 if(path.some(part=>part==='.'||part==='..'||part.includes('/')))return new Response('Invalid path',{status:400});
 const incoming=new URL(request.url);
 const target='http://127.0.0.1:8765/'+path.map(encodeURIComponent).join('/')+incoming.search;
 const headers=new Headers();
 for(const name of ['content-type','x-makma-client','x-makma-bridge','origin']){const value=request.headers.get(name);if(value)headers.set(name,value);}
 try{
  const upstream=await fetch(target,{method:request.method,headers,body:request.method==='GET'?undefined:await request.text(),signal:request.signal});
  return new Response(upstream.body,{status:upstream.status,headers:{'Content-Type':upstream.headers.get('content-type')??'application/json','Cache-Control':'no-store'}});
 }catch{return Response.json({detail:'Local Makma API unavailable on port 8765'},{status:503});}
}
export const GET=proxy;
export const POST=proxy;
