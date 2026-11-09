import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync} from 'node:child_process';import {analyze} from '../docs/planner-engine.js';
const controls=JSON.parse(fs.readFileSync(new URL('../docs/planner-controls.json',import.meta.url)));
test('complete native/browser planning reports: controls, cost/pin lattice and graph caps',()=>{
 const requests=controls.map(c=>c.input),base=controls[5].input;
 for(let a=0;a<3;a++)for(let b=0;b<3;b++)for(let c=0;c<3;c++)for(let hard=0;hard<8;hard++)requests.push({...base,costs:[a,b,c],protected:[0,1,2].filter(j=>hard&(1<<j))});
 const pairs=[];for(let a=0;a<4;a++)for(let b=a+1;b<4;b++)pairs.push([a,b]);
 for(let graph=0;graph<64;graph++)for(const limit of [1,2]){const edges=pairs.filter((_,i)=>graph&(1<<i));requests.push({input:{terms:Array.from({length:4},(_,i)=>({symbol:String.fromCharCode(97+i),args:[]})),equalities:[],disequalities:edges},limit,costs:edges.map((_,j)=>(j+graph)%4),protected:edges.flatMap((_,j)=>j%3===1?[j]:[])});}
 const native=JSON.parse(execFileSync(process.env.PYTHON||'python',['-c','import json,sys;from euflab.planner import analyze;print(json.dumps([analyze(x)for x in json.load(sys.stdin)]))'],{input:JSON.stringify(requests),maxBuffer:128<<20}));const reports=requests.map(analyze);assert.deepEqual(reports,native);assert.equal(reports.length,358);
 const verified=execFileSync(process.env.PYTHON||'python',['-c','import json,sys;from euflab.planner import verify;rs=json.load(sys.stdin);assert all(verify(r)for r in rs);print(len(rs))'],{input:JSON.stringify(reports),maxBuffer:128<<20});assert.equal(verified.toString().trim(),'358');console.log('358 complete reports matched and independently verified');
});
test('zero costs, tied coordinates, hard obstructions and strict policy fields',()=>{
 let r=analyze(controls[1].input);assert.equal(r.optimal_masks.length,7);assert.equal(r.frontier_masks.length,3);assert.equal(r.feasible.filter(p=>!p.minimal).length,4);
 r=analyze(controls[5].input);assert.deepEqual(r.optimal_masks,[6]);assert.deepEqual(r.frontier_masks,[1,6]);r=analyze(controls[6].input);assert.deepEqual(r.optimal_masks,[1,6]);assert.deepEqual(r.frontier_masks,[1]);
 for(const i of [3,4,13]){r=analyze(controls[i].input);assert.equal(r.optimum_cost,null);assert.deepEqual(r.feasible,[]);assert.ok(r.blocked_cores.length);}
 const raw=controls[0].input;for(const costs of [null,{},[],[true,1,2],[-1,1,2],[1.1,1,2],[1000001,1,2],[NaN,1,2],[Infinity,1,2]])assert.throws(()=>analyze({...raw,costs}));for(const protectedIds of [null,{},[true],[-1],[3],[1,0],[0,0]])assert.throws(()=>analyze({...raw,protected:protectedIds}));for(const bad of [null,[],{...raw,extra:0},{input:raw.input,limit:raw.limit,costs:raw.costs}])assert.throws(()=>analyze(bad));
});
