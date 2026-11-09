import copy,itertools,json,os,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from euflab import analyze as closure
from euflab import atlas
ROOT=Path(__file__).resolve().parents[1]
CONTROLS=json.loads((ROOT/'docs/atlas-controls.json').read_text())


def labeled_reference(data):
    """Independent surjective value assignments, canonicalized after direct evaluation."""
    n=len(data['terms']);valid=set()
    for values in itertools.product(range(n),repeat=n):
        # Fix one representative of all value-label permutations.
        if values[0]!=0 or any(values[i]>1+max(values[:i])for i in range(1,n)):continue
        if any(values[a]!=values[b]for a,b in data['equalities'])or any(values[a]==values[b]for a,b in data['disequalities']):continue
        fs={};ok=True
        for i,t in enumerate(data['terms']):
            key=(t['symbol'],tuple(values[a]for a in t['args']))
            if key in fs and fs[key]!=values[i]:ok=False;break
            fs[key]=values[i]
        if ok:valid.add(tuple(values.index(x)for x in values))
    return sorted(map(list,valid))


def evaluate(data,p):
    from euflab import _model
    m=_model(data,p);values=[]
    for t in data['terms']:
        f=next(f for f in m['functions']if f['symbol']==t['symbol']);arg=[values[j]for j in t['args']];values.append(next((r['value']for r in f['rows']if r['args']==arg),m['default']))
    assert values==p
    assert all(values[a]==values[b]for a,b in data['equalities'])
    assert all(values[a]!=values[b]for a,b in data['disequalities'])
    # Total functions stay defined in the original domain and a one-element extension.
    for f in m['functions']:
        for args in itertools.product(m['domain']+[len(p)],repeat=f['arity']):
            value=next((r['value']for r in f['rows']if r['args']==list(args)),m['default']);assert value in m['domain']


class AtlasTests(unittest.TestCase):
 def test_controls_complete_models_and_bell(self):
    for c in CONTROLS:
        r=atlas.analyze(c['input']);self.assertTrue(atlas.verify(r));self.assertEqual(r['satisfiable'],closure(c['input'])['consistent'])
        if len(c['input']['terms'])<=5:self.assertEqual(r['partitions'],labeled_reference(c['input']))
        for p in r['partitions']:evaluate(c['input'],p)
    r=atlas.analyze(CONTROLS[10]['input']);self.assertEqual(r['candidate_count'],4140);self.assertEqual([h['count']for h in r['histogram']],[1,127,966,1701,1050,266,28,1])
 def test_graphs_and_pair_refutation(self):
    terms=[dict(symbol=x,args=[])for x in 'abcd'];edges=list(itertools.combinations(range(4),2))
    for mask in range(64):
        d=dict(terms=terms,equalities=[],disequalities=[list(e)for k,e in enumerate(edges)if mask&(1<<k)]);r=atlas.analyze(d);self.assertEqual(r['partitions'],labeled_reference(d))
        for a,b in edges:
            forced=not closure(dict(d,equalities=[[a,b]]))['consistent'];self.assertEqual(r['pairs'][a][b]['state']=='forced-different',forced)
 def test_random_dags_and_all_pair_classes(self):
    import random
    rng=random.Random(713)
    for _ in range(60):
        n=rng.randint(1,5);ts=[]
        for i in range(n):
            if i and rng.random()<.6:ts.append(dict(symbol='f',args=[rng.randrange(i)]))
            else:ts.append(dict(symbol=chr(97+i),args=[]))
        pairs=[[rng.randrange(n),rng.randrange(n)]for _ in range(6)];d=dict(terms=ts,equalities=pairs[:rng.randrange(4)],disequalities=pairs[3:3+rng.randrange(4)]);r=atlas.analyze(d);self.assertTrue(atlas.verify(r));self.assertEqual(r['partitions'],labeled_reference(d))
        if not r['satisfiable']:continue
        for a in range(n):
            for b in range(n):
                equal=closure(d)['equal'][a][b];different=not closure(dict(d,equalities=d['equalities']+[[a,b]]))['consistent'];self.assertEqual(r['pairs'][a][b]['state'],'forced-equal'if equal else 'forced-different'if different else 'flexible')
 def test_boundary_semantics(self):
    rs=[atlas.analyze(c['input'])for c in CONTROLS]
    self.assertEqual(rs[0]['minimum_domain_size'],1);self.assertEqual(rs[1]['minimum_domain_size'],3);self.assertEqual(rs[2]['minimum_domain_size'],3);self.assertEqual(rs[3]['minimum_domain_size'],2)
    self.assertEqual(rs[4]['pairs'][0][1]['state'],'forced-different');self.assertEqual(rs[5]['pairs'][0][2]['state'],'flexible');self.assertEqual(rs[5]['pairs'][1][3]['state'],'flexible');self.assertEqual(rs[7]['pairs'][0][2]['state'],'forced-equal');self.assertFalse(rs[9]['satisfiable']);self.assertEqual(rs[11]['minimum_domain_size'],2)
 def test_verifier_is_independent(self):
    r=atlas.analyze(CONTROLS[10]['input'])
    with patch.object(atlas,'analyze',side_effect=AssertionError),patch.object(atlas,'partitions',side_effect=AssertionError),patch.object(atlas,'compatible',side_effect=AssertionError),patch.object(atlas,'_model',side_effect=AssertionError):self.assertTrue(atlas.verify(r))
 def test_forged_certificates(self):
    r=atlas.analyze(CONTROLS[0]['input']);mutations=[lambda x:x.update(candidate_count=True),lambda x:x.update(minimum_domain_size=2),lambda x:x['partitions'].pop(),lambda x:x['partitions'].append(x['partitions'][0]),lambda x:x['partitions'].reverse(),lambda x:x['histogram'][0].update(count=7),lambda x:x['pairs'][0][1].update(state='forced-equal'),lambda x:x['pairs'][0][1].update(equal_witness=None),lambda x:x['witnesses'][0]['model'].update(default=99),lambda x:x['witnesses'][0]['model']['functions'][0]['rows'][0].update(value=99),lambda x:x['witnesses'].pop(),lambda x:x.update(extra=1),lambda x:x['input']['terms'][0]['args'].append(True)]
    for mutation in mutations:
        bad=copy.deepcopy(r);mutation(bad)
        with self.assertRaises((ValueError,TypeError)):atlas.verify(bad)
 def test_cli_atomic_and_size(self):
    with tempfile.TemporaryDirectory()as tmp:
        p=Path(tmp)/'input.json';q=Path(tmp)/'report.json';p.write_text(json.dumps(CONTROLS[10]['input']))
        cmd=[sys.executable,'-m','euflab.atlas'];subprocess.run(cmd+[str(p),'--output',str(q)],check=True,capture_output=True);self.assertLess(q.stat().st_size,8*1024*1024);subprocess.run(cmd+[str(q),'--verify'],check=True,capture_output=True)
        before=q.read_bytes();p.write_text('{"terms":[],"terms":[]}');self.assertEqual(subprocess.run(cmd+[str(p),'--output',str(q)],capture_output=True).returncode,2);self.assertEqual(before,q.read_bytes())

if __name__=='__main__':unittest.main()
