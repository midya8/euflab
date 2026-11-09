import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from euflab import analyze as ordinary
from euflab.cardinality import analyze,verify
CONTROLS=json.loads(Path('docs/cardinality-controls.json').read_text())

def reference(raw):
 d=raw['input'];n=len(d['terms']);lits=[(kind,p)for kind in ['equalities','disequalities']for p in d[kind]];out=[None]*(1<<len(lits))
 for values in itertools.product(range(n),repeat=n):
  if set(values)!=set(range(max(values)+1)):continue
  valid=True
  for i,t in enumerate(d['terms']):
   for j,u in enumerate(d['terms']):
    if t['symbol']==u['symbol']and tuple(values[a]for a in t['args'])==tuple(values[a]for a in u['args'])and values[i]!=values[j]:valid=False
  if not valid:continue
  for mask in range(len(out)):
   if all(not(mask&(1<<j))or((values[a]==values[b])==(kind=='equalities'))for j,(kind,(a,b))in enumerate(lits)):
    size=len(set(values));out[mask]=min(out[mask],size)if out[mask]else size
 return out

class CardinalityTests(unittest.TestCase):
 def check_reference(self,raw):
  r=analyze(raw);assert verify(r);mins=reference(raw);self.assertEqual([s['minimum_domain_size']for s in r['subsets']],mins);sat=[x is not None and x<=raw['limit']for x in mins];m=len(r['assertions']);full=(1<<m)-1
  expected_cores=[];expected_repairs=[]
  for mask in range(1<<m):
   ids=[j for j in range(m)if mask&(1<<j)];proper=[x for x in range(1<<m)if x!=mask and x&mask==x]
   if not sat[mask]and all(sat[x]for x in proper):expected_cores.append(ids)
   if sat[full^mask]and all(not sat[full^x]for x in proper):expected_repairs.append(ids)
  key=lambda x:(len(x),x);self.assertEqual([c['assertions']for c in r['cores']],sorted(expected_cores,key=key));self.assertEqual([p['removed']for p in r['repairs']],sorted(expected_repairs,key=key));return r
 def test_controls_and_model_evaluation(self):
  total=0
  for c in CONTROLS:
   r=analyze(c['input']);self.assertTrue(verify(r));self.assertEqual(r['minimum_domain_size']is None,not ordinary(r['input'])['consistent'])
   ws=[(p,p['kept'])for p in r['repairs']]+[(w,[j for j in core['assertions']if j!=w['removed']])for core in r['cores']for w in core['relaxations']]
   for w,kept in ws:
    model=w['model'];vals=[];self.assertLessEqual(len(model['domain']),r['limit'])
    for t in r['input']['terms']:
     f=next(f for f in model['functions']if f['symbol']==t['symbol']);args=[vals[a]for a in t['args']];vals.append(next((row['value']for row in f['rows']if row['args']==args),model['default']))
    self.assertEqual(vals,model['term_values'])
    for j in kept:
     a=r['assertions'][j];x,y=a['pair'];self.assertEqual(vals[x]==vals[y],a['kind']=='equalities')
    total+=1
  self.assertGreater(total,50)
 def test_reference_graphs_all_caps(self):
  edges=list(itertools.combinations(range(4),2));terms=[dict(symbol=chr(97+i),args=[])for i in range(4)]
  for mask in range(64):
   for k in [1,2,3,4]:self.check_reference(dict(input=dict(terms=terms,equalities=[],disequalities=[list(e)for j,e in enumerate(edges)if mask&(1<<j)]),limit=k))
 def test_seeded_functional_reference(self):
  rng=random.Random(5539)
  for trial in range(32):
   n=rng.randrange(2,6);ts=[]
   for i in range(n):
    if i and rng.random()<.6:
     arity=rng.choice([1,2]);ts.append(dict(symbol='f'if arity==1 else 'g',args=[rng.randrange(i)for _ in range(arity)]))
    else:ts.append(dict(symbol='x'+str(i),args=[]))
   d=dict(terms=ts,equalities=[[rng.randrange(n),rng.randrange(n)]for _ in range(rng.randrange(3))],disequalities=[[rng.randrange(n),rng.randrange(n)]for _ in range(rng.randrange(4))]);self.check_reference(dict(input=d,limit=rng.randrange(1,n+1)))
 def test_duality_and_duplicate_occurrences(self):
  for c in CONTROLS:
   r=analyze(c['input']);m=len(r['assertions']);hits=[]
   for size in range(m+1):
    for xs in itertools.combinations(range(m),size):
     if all(set(xs)&set(core['assertions'])for core in r['cores'])and not any(set(h)<=set(xs)for h in hits):hits.append(list(xs))
   self.assertEqual(hits,[p['removed']for p in r['repairs']])
  r=analyze(CONTROLS[5]['input']);self.assertEqual([c['assertions']for c in r['cores']],[[0],[1]]);self.assertEqual(r['repairs'][0]['removed'],[0,1])
 def test_verifier_independence_and_forgeries(self):
  r=analyze(CONTROLS[4]['input'])
  with patch('euflab.cardinality.analyze',side_effect=AssertionError),patch('euflab.cardinality.atlas',side_effect=AssertionError),patch('euflab.cardinality._model',side_effect=AssertionError),patch('euflab.atlas.analyze',side_effect=AssertionError),patch('euflab.atlas.partitions',side_effect=AssertionError),patch('euflab.atlas.compatible',side_effect=AssertionError),patch('euflab.atlas._model',side_effect=AssertionError):self.assertTrue(verify(r))
  bad=[]
  for key in r:
   x=copy.deepcopy(r);del x[key];bad.append(x)
  for edit in [lambda x:x['cores'].pop(),lambda x:x['repairs'].pop(),lambda x:x['subsets'].pop(),lambda x:x['cores'][0].update(kind='cap-only'),lambda x:x['repairs'][0]['model'].update(default=True),lambda x:x['subsets'][0].update(mask=False),lambda x:x['background']['partitions'].pop(),lambda x:x.update(limit=True),lambda x:x.update(satisfiable=1),lambda x:x['cores'][0]['relaxations'].pop()]:
   x=copy.deepcopy(r);edit(x);bad.append(x)
  for x in bad:
   with self.assertRaises((ValueError,TypeError,KeyError,IndexError)):verify(x)
 def test_cap_monotonicity_and_minimal_vs_minimum(self):
  for c in CONTROLS:
   rs=[analyze(dict(c['input'],limit=k))for k in range(1,9)]
   self.assertEqual([r['subsets']for r in rs],[rs[0]['subsets']]*8)
   self.assertEqual([r['satisfiable']for r in rs],sorted(r['satisfiable']for r in rs))
   for r in rs:
    for repair in r['repairs']:
     for p in r['background']['partitions']:
      if len(set(p))>r['limit']:continue
      holds=[(p[a['pair'][0]]==p[a['pair'][1]])==(a['kind']=='equalities')for a in r['assertions']]
      if all(holds[j]for j in repair['kept']):self.assertTrue(all(not holds[j]for j in repair['removed']))
  self.assertEqual({len(r['removed'])for r in analyze(CONTROLS[12]['input'])['repairs']},{1,2})
 def test_cli_and_limits(self):
  raw=CONTROLS[0]['input']
  with tempfile.TemporaryDirectory()as tmp:
   p=Path(tmp,'in.json');p.write_text(json.dumps(raw));o=Path(tmp,'keep.json');cmd=[sys.executable,'-m','euflab.cardinality'];good=subprocess.run(cmd+[str(p)],capture_output=True,text=True,check=True);self.assertTrue(verify(json.loads(good.stdout)));self.assertEqual(json.loads(subprocess.run(cmd+['-','--verify'],input=good.stdout,text=True,capture_output=True,check=True).stdout),dict(valid=True,schema='euflab-cardinality-v1'))
   for text in ['{"limit":1,"limit":2,"input":{}}',json.dumps(dict(raw,limit=0)),json.dumps(dict(raw,limit=True)),json.dumps(dict(raw,limit=9)),'x'*(65537)]:
    p.write_text(text);o.write_text('sentinel');r=subprocess.run(cmd+[str(p),'--output',str(o)],capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(o.read_text(),'sentinel')
   p.write_bytes(b' '*(8*1024*1024+1));o.write_text('sentinel');r=subprocess.run(cmd+[str(p),'--verify','--output',str(o)],capture_output=True);self.assertEqual(r.returncode,2);self.assertEqual(o.read_text(),'sentinel')
  x=copy.deepcopy(raw);x['input']['equalities']=[[0,0]]*8;x['input']['disequalities']=[[0,1]]
  with self.assertRaises(ValueError):analyze(x)
