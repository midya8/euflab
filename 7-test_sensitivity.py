import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from euflab.sensitivity import analyze,verify
from euflab.planner import analyze as plan
C=json.loads((Path(__file__).resolve().parents[1]/'docs/sensitivity-controls.json').read_text())

def brute(planning,j,x):
    ps=[(p['mask'],sum(x if i==j else planning['costs'][i]for i in p['removed']))for p in planning['feasible']];value=min((v for _,v in ps),default=None);return [m for m,v in ps if v==value],value

class SensitivityTests(unittest.TestCase):
    def check(self,raw):
        r=analyze(raw);self.assertTrue(verify(r));p=r['planning']
        for j,f in enumerate(r['profiles']):
            self.assertEqual(f['assertion'],j);self.assertEqual(f['segments'][0]['lo'],0);self.assertEqual(f['segments'][-1]['hi'],1000000)
            for a,b in zip(f['segments'],f['segments'][1:]):self.assertEqual(a['hi']+1,b['lo']);self.assertNotEqual(a['optimal_masks'],b['optimal_masks'])
            xs=set(range(15))|{1000000,p['costs'][j]}
            for s in f['segments']:xs|={s['lo'],s['hi'],max(0,s['lo']-1),min(1000000,s['hi']+1)}
            for x in xs:
                s=next(s for s in f['segments']if s['lo']<=x<=s['hi']);masks,value=brute(p,j,x);self.assertEqual(s['optimal_masks'],masks)
                if s['kind']=='tie':self.assertEqual(s['lo'],s['hi'])
            nominal=f['segments'][f['current_segment']];self.assertTrue(nominal['lo']<=p['costs'][j]<=nominal['hi']);self.assertEqual(nominal['optimal_masks'],p['optimal_masks'])
        return r

    def test_controls_endpoints_ties_classes_and_full_coverage(self):
        for c in C:self.check(c['input'])
        for i in [3,4]:self.assertTrue(all(f['segments']==[dict(lo=0,hi=1000000,kind='blocked',optimal_masks=[])]for f in analyze(C[i]['input'])['profiles']))
        r=analyze(C[12]['input']);self.assertEqual(r['profiles'][0]['segments'][-1],dict(lo=1000000,hi=1000000,kind='tie',optimal_masks=[1,6]));self.assertEqual(analyze(C[13]['input'])['profiles'][0]['crossing'],2000000)
        r=analyze(C[1]['input']);self.assertTrue(any(not p['minimal']for p in r['planning']['feasible']if p['mask']in r['profiles'][0]['segments'][0]['optimal_masks']))
        r=analyze(C[2]['input']);self.assertIsNone(r['profiles'][0]['delete']['base']);self.assertEqual(len(r['profiles'][0]['segments']),1)
        r=analyze(C[10]['input']);self.assertTrue(all(f['keep']['base']is None for f in r['profiles']))
        self.assertEqual(analyze(C[9]['input'])['profiles'],[])

    def test_all216_cost_pin_policies_independent_repricing(self):
        raw=copy.deepcopy(C[5]['input']);count=0
        for costs in itertools.product(range(3),repeat=3):
            for hard in range(8):
                raw['costs']=list(costs);raw['protected']=[j for j in range(3)if hard&(1<<j)];r=self.check(raw)
                for j in range(3):
                    for x in range(6):
                        changed=copy.deepcopy(raw);changed['costs'][j]=x;expected=plan(changed);f=r['profiles'][j];s=next(s for s in f['segments']if s['lo']<=x<=s['hi']);self.assertEqual(s['optimal_masks'],expected['optimal_masks'])
                count+=1
        self.assertEqual(count,216)

    def test_labeled_functional_reference(self):
        from test_planner import reference
        rng=random.Random(681255)
        for _ in range(24):
            terms=[dict(symbol='a',args=[]),dict(symbol='b',args=[]),dict(symbol='f',args=[0]),dict(symbol='f',args=[1])];raw=dict(input=dict(terms=terms,equalities=[[rng.randrange(4),rng.randrange(4)]for _ in range(2)],disequalities=[[rng.randrange(4),rng.randrange(4)]for _ in range(2)]),limit=rng.choice([1,2,3]),costs=[rng.randrange(5)for _ in range(4)],protected=[j for j in range(4)if rng.random()<.2]);r=self.check(raw)
            for j in range(4):
                for x in range(7):
                    changed=copy.deepcopy(raw);changed['costs'][j]=x;_,value,masks,_=reference(changed);self.assertEqual(masks,next(s['optimal_masks']for s in r['profiles'][j]['segments']if s['lo']<=x<=s['hi']));self.assertEqual(value,brute(r['planning'],j,x)[1])

    def test_costvalue_concavity_and_monotone_occurrence_choice(self):
        for c in C:
            r=analyze(c['input']);p=r['planning']
            for j,f in enumerate(r['profiles']):
                vs=[brute(p,j,x)[1]for x in range(20)]
                if vs[0]is None:continue
                diffs=[b-a for a,b in zip(vs,vs[1:])];self.assertTrue(all(d in [0,1]for d in diffs));self.assertEqual(diffs,sorted(diffs,reverse=True))
                kinds=[s['kind']for s in f['segments']];self.assertEqual(kinds,sorted(kinds,key={'delete':0,'tie':1,'keep':2}.get))

    def test_independent_verifier_and_mutation_rejection(self):
        r=analyze(C[0]['input'])
        with patch('euflab.sensitivity.analyze',side_effect=AssertionError),patch('euflab.sensitivity.plan',side_effect=AssertionError),patch('euflab.planner.analyze',side_effect=AssertionError):self.assertTrue(verify(r))
        bad=[]
        for field,value in [('schema','wrong'),('cost_max',999999),('cost_max',True),('profiles',[])]:b=copy.deepcopy(r);b[field]=value;bad.append(b)
        for field,value in [('crossing',False),('assertion',False),('current_segment',False)]:b=copy.deepcopy(r);b['profiles'][0][field]=value;bad.append(b)
        for field,value in [('lo',1),('hi',1000000),('kind','blocked'),('optimal_masks',[])]:b=copy.deepcopy(r);b['profiles'][0]['segments'][0][field]=value;bad.append(b)
        b=copy.deepcopy(r);b['profiles'][0]['segments'].pop();bad.append(b)
        b=copy.deepcopy(r);b['profiles'][0]['keep']['masks'].pop();bad.append(b)
        b=copy.deepcopy(r);b['planning']['feasible'].pop();bad.append(b)
        b=copy.deepcopy(r);b['extra']=0;bad.append(b)
        for b in bad:
            with self.assertRaises(ValueError):verify(b)

    def test_maximum256plans_and_invalid_policies(self):
        raw=dict(input=dict(terms=[dict(symbol='x'+str(i),args=[])for i in range(8)],equalities=[[i,i]for i in range(8)],disequalities=[]),limit=8,costs=[0]*8,protected=[]);r=self.check(raw);self.assertEqual(len(r['planning']['optimal_masks']),256);self.assertTrue(all(len(f['segments'][0]['optimal_masks'])==256 for f in r['profiles']));self.assertLess(len(json.dumps(r,indent=2).encode()),8<<20)
        for b in [None,[],{},dict(raw,costs=[True]*8),dict(raw,protected=[1,0]),dict(raw,extra=0)]:
            with self.assertRaises(ValueError):analyze(b)

    def test_cli_atomic_size_validation_and_roundtrip(self):
        cmd=[sys.executable,'-m','euflab.sensitivity'];p=subprocess.run(cmd+['-'],input=json.dumps(C[0]['input']),capture_output=True,text=True);self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(verify(json.loads(p.stdout)));v=subprocess.run(cmd+['-','--verify'],input=p.stdout,capture_output=True,text=True);self.assertEqual(v.returncode,0,v.stderr);self.assertEqual(json.loads(v.stdout),dict(valid=True,schema='euflab-sensitivity-v1'))
        with tempfile.TemporaryDirectory()as d:
            out=Path(d)/'report.json';out.write_text('preserve')
            for body,flags in [('{',[]),(' '*65537,[]),(' '*((8<<20)+1),['--verify'])]:
                p=subprocess.run(cmd+['-','--output',str(out)]+flags,input=body,capture_output=True,text=True);self.assertEqual(p.returncode,2);self.assertEqual(p.stdout,'');self.assertEqual(out.read_text(),'preserve')
