import test from 'node:test';import assert from 'node:assert/strict';import fs from 'node:fs';import {execFileSync}from 'node:child_process';import {analyze,validate}from '../docs/engine.js';
const controls=JSON.parse(fs.readFileSync(new URL('../docs/controls.json',import.meta.url)));const python=process.env.PYTHON||'python';
test('independent relation engine agrees semantically and every JS proof replays natively',()=>{const fixture=JSON.parse(execFileSync(python,['-c',`import json,itertools,random
from euflab import analyze
cs=json.load(open('docs/controls.json'));cases=[c['input']for c in cs];ts=cs[1]['input']['terms'];pairs=list(itertools.combinations(range(4),2))
for mask in range(64):cases.append(dict(terms=ts,equalities=[list(p)for i,p in enumerate(pairs)if mask>>i&1],disequalities=[]))
r=random.Random(51)
for k in range(80):
 n=1+k%8;terms=[]
 for i in range(n):
  arity=r.randrange(min(i,2)+1);terms.append(dict(symbol=['a','f','g'][arity],args=[r.randrange(i)for _ in range(arity)]))
 cases.append(dict(terms=terms,equalities=[[r.randrange(n),r.randrange(n)]for _ in range(k%9)],disequalities=[[r.randrange(n),r.randrange(n)]for _ in range(k%4)]))
print(json.dumps([[c,analyze(c)]for c in cases]))`],{maxBuffer:32*1024*1024}));const reports=[];for(const[c,native]of fixture){const js=analyze(c);for(const k of ['schema','input','consistent','classes','equal','model'])assert.deepEqual(js[k],native[k],k);assert.deepEqual(js.conflicts.map(x=>x.index),native.conflicts.map(x=>x.index));reports.push(js);}const proof=execFileSync(python,['-c','import json,sys;from euflab import verify;rs=json.load(sys.stdin);assert all(verify(r)for r in rs);print(len(rs))'],{input:JSON.stringify(reports),maxBuffer:32*1024*1024}).toString();assert.equal(Number(proof),156);console.log('156 cross-engine reports, all JavaScript proof DAGs checked by native verifier');});
test('strict JSON input boundaries',()=>{const d=controls[0].input;for(const bad of [{},{...d,extra:1},{...d,terms:[]},{...d,equalities:[[true,1]]},{...d,terms:[{symbol:'a',args:[0]}]},{...d,terms:[{symbol:'a',args:[]},{symbol:'a',args:[0]}]},{...d,disequalities:[[0,Infinity]]}])assert.throws(()=>validate(bad));});
