import copy,itertools,json,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import euflab
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/controls.json').read_text())

def partitions(n):
    def rec(a):
        if len(a)==n:yield a;return
        for x in range(max(a)+2):yield from rec(a+[x])
    yield from rec([0])

def models(data,negative=False):
    ts=data['terms']
    for p in partitions(len(ts)):
        if any(p[a]!=p[b]for a,b in data['equalities']):continue
        if any(t['symbol']==u['symbol']and all(p[a]==p[b]for a,b in zip(t['args'],u['args']))and p[i]!=p[j]for i,t in enumerate(ts)for j,u in enumerate(ts)):continue
        if negative and any(p[a]==p[b]for a,b in data['disequalities']):continue
        yield p

def oracle(data):
    ms=list(models(data));n=len(data['terms']);return [[all(p[a]==p[b]for p in ms)for b in range(n)]for a in range(n)],any(models(data,True))

class Core(unittest.TestCase):
    def check(self,data,full=True):
        r=euflab.analyze(data);self.assertTrue(euflab.verify(r))
        if full:
            relation,sat=oracle(data);self.assertEqual(r['equal'],relation);self.assertEqual(r['consistent'],sat)
        if r['model']:
            m=r['model'];self.assertEqual(m['term_values'],[min(c)for i in range(len(data['terms']))for c in r['classes']if i in c])
            for f in m['functions']:
                table={tuple(row['args']):row['value']for row in f['rows']}
                for args in itertools.product(m['domain'],repeat=f['arity']):self.assertIn(table.get(args,m['default']),m['domain'])
            self.assertTrue(all(m['term_values'][a]!=m['term_values'][b]for a,b in data['disequalities']))
        return r
    def test_controls_and_complete_model(self):
        for c in CONTROLS:self.check(c['input'])
        self.assertFalse(euflab.analyze(CONTROLS[1]['input'])['equal'][0][1])
        self.assertTrue(euflab.analyze(CONTROLS[2]['input'])['consistent'])
        self.assertEqual(len(euflab.analyze(CONTROLS[9]['input'])['conflicts']),2)
    def test_exhaustive_constant_conjunctions(self):
        terms=[dict(symbol=s,args=[])for s in 'abc'];pairs=list(itertools.combinations(range(3),2))
        for flags in itertools.product(range(3),repeat=3):self.check(dict(terms=terms,equalities=[list(p)for p,f in zip(pairs,flags)if f==1],disequalities=[list(p)for p,f in zip(pairs,flags)if f==2]))
    def test_exhaustive_congruence_assumption_subsets(self):
        terms=CONTROLS[1]['input']['terms'];pairs=list(itertools.combinations(range(4),2))
        for mask in range(64):
            d=dict(terms=terms,equalities=[list(p)for i,p in enumerate(pairs)if mask>>i&1],disequalities=[]);r=self.check(d)
            for a,b in pairs:
                d2=copy.deepcopy(d);d2['disequalities']=[[a,b]];q=euflab.analyze(d2);self.assertEqual(q['consistent'],not r['equal'][a][b]);self.assertTrue(euflab.verify(q))
    def test_seeded_term_dags(self):
        rng=random.Random(4619)
        for k in range(80):
            n=1+k%8;ts=[]
            for i in range(n):
                arity=rng.randrange(min(i,2)+1);s=['a','f','g'][arity];ts.append(dict(symbol=s,args=[rng.randrange(i)for _ in range(arity)]))
            d=dict(terms=ts,equalities=[[rng.randrange(n),rng.randrange(n)]for _ in range(k%9)],disequalities=[[rng.randrange(n),rng.randrange(n)]for _ in range(k%4)])
            self.check(d,full=n<=5)
    def test_independent_checker_without_generator(self):
        reports=[euflab.analyze(c['input'])for c in CONTROLS]
        with patch('euflab.analyze',side_effect=AssertionError),patch('euflab._model',side_effect=AssertionError),patch('euflab.deque',side_effect=AssertionError):
            for r in reports:self.assertTrue(euflab.verify(r))
    def test_proof_and_model_forgery(self):
        for c in CONTROLS:
            r=euflab.analyze(c['input']);bad=[]
            for i,p in enumerate(r['proofs']):
                x=copy.deepcopy(r);x['proofs'][i]['premises']=[i];bad.append(x)
            for key in ['consistent','classes','equal','evidence','conflicts','model']:
                x=copy.deepcopy(r);x[key]='forged';bad.append(x)
            for x in bad:
                with self.assertRaises((ValueError,TypeError)):euflab.verify(x)
        r=euflab.analyze(CONTROLS[1]['input']);r['model']['default']=True
        with self.assertRaises(ValueError):euflab.verify(r)
        r=euflab.analyze(CONTROLS[0]['input']);r['proofs'][0]['left']=False
        with self.assertRaises(ValueError):euflab.verify(r)
    def test_integral_json_numbers_normalize(self):
        d=copy.deepcopy(CONTROLS[1]['input']);d['equalities']=[[2.0,3.0]];d['terms'][2]['args']=[0.0];r=euflab.analyze(d);self.assertTrue(euflab.verify(r));self.assertEqual(type(r['input']['equalities'][0][0]),int)
        for v in [0.5,float('nan'),float('inf')]:
            d['equalities']=[[v,1]]
            with self.assertRaises(ValueError):euflab.analyze(d)
    def test_strict_boundary_validation(self):
        d=copy.deepcopy(CONTROLS[0]['input']);bads=[{},dict(d,extra=1),dict(d,terms=[]),dict(d,terms=d['terms']*2),dict(d,equalities=[[False,1]]),dict(d,disequalities=[[0,99]]),dict(d,equalities=[[0,1]]*9)]
        for term in [dict(symbol='F',args=[]),dict(symbol='a',args=[0]),dict(symbol='a',args=[True]),dict(symbol='a',args=[0,0,0]),dict(symbol='a',args=[],extra=1)]:bads.append(dict(d,terms=[term]))
        bads.append(dict(d,terms=[dict(symbol='a',args=[]),dict(symbol='a',args=[0])]))
        for x in bads:
            with self.assertRaises(ValueError):euflab.analyze(x)
    def test_cli_roundtrip_and_atomic_rejection(self):
        r=euflab.analyze(CONTROLS[0]['input'])
        for data,args in [(CONTROLS[0]['input'],[]),(r,['--verify'])]:
            p=subprocess.run([sys.executable,'-m','euflab','-',*args],input=json.dumps(data),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr)
            self.assertEqual(json.loads(p.stdout),r if not args else dict(valid=True,schema='euflab-v1'))
        with tempfile.TemporaryDirectory()as tmp:
            out=Path(tmp)/'out.json';out.write_text('preserve')
            for text in ['{"terms":[],"terms":[]}','NaN','{}','x'*65537]:
                p=subprocess.run([sys.executable,'-m','euflab','-','--output',str(out)],input=text,text=True,capture_output=True);self.assertEqual(p.returncode,2);self.assertEqual(out.read_text(),'preserve')
