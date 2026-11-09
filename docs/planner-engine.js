import {analyze as diagnose} from './cardinality-engine.js';
import {model} from './atlas-engine.js';
export function validatePlan(raw){
 if(!raw||typeof raw!=='object'||Array.isArray(raw)||Object.keys(raw).sort().join(',')!=='costs,input,limit,protected')throw Error('Expected input, limit, costs and protected');
 // Diagnosis validates the bounded ground input and cap before any mask work.
 const d=diagnose({input:raw.input,limit:raw.limit}),m=d.assertions.length;
 if(!Array.isArray(raw.costs)||raw.costs.length!==m||raw.costs.some(c=>!Number.isInteger(c)||c<0||c>1000000))throw Error('One integer deletion cost from 0 to 1000000 per occurrence');
 if(!Array.isArray(raw.protected)||raw.protected.some((j,i)=>!Number.isInteger(j)||j<0||j>=m||(i&&j<=raw.protected[i-1])))throw Error('Protected IDs must be unique, increasing occurrence IDs');
 return d;
}
export function analyze(raw){
 const d=validatePlan(raw),costs=raw.costs.slice(),protectedIds=raw.protected.slice(),m=costs.length,full=(1<<m)-1,feasible=[];
 for(let mask=0;mask<=full;mask++){
  const removed=d.assertions.filter(a=>mask&(1<<a.id)).map(a=>a.id),kept=d.assertions.filter(a=>!(mask&(1<<a.id))).map(a=>a.id),s=d.subsets[full^mask];
  if(removed.some(j=>protectedIds.includes(j))||s.minimum_domain_size===null||s.minimum_domain_size>d.limit)continue;
  const minimal=removed.every(j=>{const v=d.subsets[(full^mask)|(1<<j)].minimum_domain_size;return v===null||v>d.limit;});
  feasible.push({mask,removed,kept,cost:removed.reduce((v,j)=>v+costs[j],0),count:removed.length,minimal,minimum_domain_size:s.minimum_domain_size,partition:s.witness,model:model(d.input,d.background.partitions[s.witness])});
 }
 const optimum=feasible.length?Math.min(...feasible.map(p=>p.cost)):null,frontier=feasible.filter(p=>!feasible.some(q=>q.cost<=p.cost&&q.count<=p.count&&(q.cost<p.cost||q.count<p.count))).map(p=>p.mask);
 return {schema:'euflab-planner-v1',diagnosis:d,costs,protected:protectedIds,feasible,optimum_cost:optimum,optimal_masks:feasible.filter(p=>p.cost===optimum).map(p=>p.mask),frontier_masks:frontier,blocked_cores:d.cores.flatMap((c,i)=>c.assertions.every(j=>protectedIds.includes(j))?[i]:[])};
}
