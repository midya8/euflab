// Independent dense relation saturation; no union-find or native proof-forest traversal.
export function validate(raw){
 const object=x=>x!==null&&typeof x==='object'&&!Array.isArray(x),keys=(x,ks)=>object(x)&&Object.keys(x).sort().join(',')===ks.sort().join(',');
 if(!keys(raw,['terms','equalities','disequalities']))throw Error('Input needs exactly terms, equalities, disequalities');
 const ts=raw.terms;if(!Array.isArray(ts)||ts.length<1||ts.length>8)throw Error('Need 1..8 terms');const sig=new Map();
 for(let i=0;i<ts.length;i++){const t=ts[i];if(!keys(t,['symbol','args'])||typeof t.symbol!=='string'||! /^[a-z][a-z0-9_]{0,7}$/.test(t.symbol))throw Error('Invalid term or symbol');if(!Array.isArray(t.args)||t.args.length>2||t.args.some(x=>!Number.isInteger(x)||x<0||x>=i))throw Error('Arguments must be earlier term IDs, arity at most 2');if(sig.has(t.symbol)&&sig.get(t.symbol)!==t.args.length)throw Error('A symbol has one fixed arity');sig.set(t.symbol,t.args.length);}
 for(const k of ['equalities','disequalities'])if(!Array.isArray(raw[k])||raw[k].length>8||raw[k].some(p=>!Array.isArray(p)||p.length!==2||p.some(x=>!Number.isInteger(x)||x<0||x>=ts.length)))throw Error('At most 8 pairs of valid term IDs');
 return JSON.parse(JSON.stringify(raw));
}
export function analyze(raw){
 const input=validate(raw),ts=input.terms,n=ts.length,proofs=[],evidence=Array.from({length:n},()=>Array(n).fill(null));
 const add=(rule,left,right,premises=[],extra={})=>{const id=proofs.length;proofs.push({rule,left,right,premises,...extra});evidence[left][right]=id;return id;};
 for(let i=0;i<n;i++)add('reflexivity',i,i);
 input.equalities.forEach(([a,b],i)=>{if(evidence[a][b]===null)add('assumption',a,b,[],{assumption:i});});
 let changed=true;while(changed){changed=false;
  for(let a=0;a<n;a++)for(let b=0;b<n;b++)if(evidence[a][b]===null&&evidence[b][a]!==null){add('symmetry',a,b,[evidence[b][a]]);changed=true;}
  for(let a=0;a<n;a++)for(let b=0;b<n;b++)for(let c=0;c<n;c++)if(evidence[a][c]===null&&evidence[a][b]!==null&&evidence[b][c]!==null){add('transitivity',a,c,[evidence[a][b],evidence[b][c]]);changed=true;}
  for(let a=0;a<n;a++)for(let b=0;b<n;b++)if(evidence[a][b]===null&&ts[a].symbol===ts[b].symbol&&ts[a].args.every((v,i)=>evidence[v][ts[b].args[i]]!==null)){add('congruence',a,b,ts[a].args.map((v,i)=>evidence[v][ts[b].args[i]]));changed=true;}
 }
 const equal=evidence.map(r=>r.map(p=>p!==null)),reps=equal.map(r=>r.findIndex(Boolean)),domain=[...new Set(reps)].sort((a,b)=>a-b),classes=domain.map(r=>reps.map((v,i)=>v===r?i:null).filter(x=>x!==null));
 const conflicts=input.disequalities.flatMap(([a,b],index)=>equal[a][b]?[{index,proof:evidence[a][b]}]:[]);let model=null;
 if(!conflicts.length){const functions=[...new Set(ts.map(t=>t.symbol))].sort().map(symbol=>{const map=new Map();ts.forEach((t,i)=>{if(t.symbol===symbol){const args=t.args.map(j=>reps[j]),key=JSON.stringify(args);if(!map.has(key))map.set(key,{args,value:reps[i],terms:[]});map.get(key).terms.push(i);}});const rows=[...map.values()].sort((a,b)=>{for(let i=0;i<a.args.length;i++)if(a.args[i]!==b.args[i])return a.args[i]-b.args[i];return 0;});return {symbol,arity:ts.find(t=>t.symbol===symbol).args.length,rows};});model={domain,term_values:reps,default:domain[0],functions};}
 return {schema:'euflab-v1',input,consistent:!conflicts.length,classes,equal,proofs,evidence,conflicts,model};
}
