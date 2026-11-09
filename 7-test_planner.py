import copy,itertools,json,os,random,subprocess,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from euflab.planner import analyze,verify,validate_plan
CONTROLS=json.loads((Path(__file__).resolve().parents[1]/'docs/planner-controls.json').read_text())

def reference(raw):
    """Labeled domain assignments, not partition/diagnosis generation."""
    data=raw['input'];m=len(raw['costs']);n=len(data['terms']);lits=[(kind,pair)for kind in ['equalities','disequalities']for pair in data[kind]];truth=set()
    for values in itertools.product(range(raw['limit']),repeat=n):
        rows={}
        for i,t in enumerate(data['terms']):
            key=t['symbol'],tuple(values[a]for a in t['args'])
            if key in rows and rows[key]!=values[i]:break
            rows[key]=values[i]
        else:truth.add(sum(1<<j for j,(kind,(a,b))in enumerate(lits)if((values[a]==values[b])==(kind=='equalities'))))
    ps=[]
    for mask in range(1<<m):
        removed=[j for j in range(m)if mask&(1<<j)];kept=((1<<m)-1)^mask
        if any(j in raw['protected']for j in removed)or not any((t&kept)==kept for t in truth):continue
        ps.append((mask,sum(raw['costs'][j]for j in removed),len(removed)))
    optimum=min((p[1]for p in ps),default=None);optimal=[p[0]for p in ps if p[1]==optimum];frontier=[p[0]for p in ps if not any(q[1]<=p[1]and q[2]<=p[2]and(q[1]<p[1]or q[2]<p[2])for q in ps)]
    return ps,optimum,optimal,frontier

class PlannerTests(unittest.TestCase):
    def check_reference(self,raw):
        r=analyze(raw);ps,optimum,optimal,frontier=reference(raw);self.assertEqual([(p['mask'],p['cost'],p['count'])for p in r['feasible']],ps);self.assertEqual(r['optimum_cost'],optimum);self.assertEqual(r['optimal_masks'],optimal);self.assertEqual(r['frontier_masks'],frontier);self.assertEqual(bool(r['blocked_cores']),not bool(ps));return r

    def test_controls_complete_models_and_zero_cost_semantics(self):
        for c in CONTROLS:
            r=analyze(c['input']);self.assertTrue(verify(r));self.assertEqual(r,analyze(c['input']));d=r['diagnosis']
            for p in r['feasible']:
                v=p['model']['term_values'];self.assertTrue(set(c['input']['protected'])<=set(p['kept']));self.assertEqual(p['cost'],sum(c['input']['costs'][j]for j in p['removed']))
                for a in d['assertions']:
                    holds=(v[a['pair'][0]]==v[a['pair'][1]])==(a['kind']=='equalities')
                    if a['id']in p['kept']:self.assertTrue(holds)
                    elif p['minimal']:self.assertFalse(holds)
                self.assertEqual(p['minimum_domain_size'],len(p['model']['domain']))
        zero=analyze(CONTROLS[1]['input']);self.assertEqual(len(zero['optimal_masks']),7);self.assertEqual(len(zero['frontier_masks']),3);self.assertTrue(any(not p['minimal']for p in zero['feasible']if p['mask']in zero['optimal_masks']))
        r=analyze(CONTROLS[7]['input']);self.assertTrue(any(not p['minimal']and any((p['model']['term_values'][a['pair'][0]]==p['model']['term_values'][a['pair'][1]])==(a['kind']=='equalities')for a in r['diagnosis']['assertions']if a['id']in p['removed'])for p in r['feasible']))
        self.assertEqual(analyze(CONTROLS[5]['input'])['frontier_masks'],[1,6]);self.assertEqual(analyze(CONTROLS[6]['input'])['optimal_masks'],[1,6]);self.assertEqual(analyze(CONTROLS[6]['input'])['frontier_masks'],[1])

    def test_all_four_name_graphs_all_pin_sets_at_two_caps(self):
        pairs=list(itertools.combinations(range(4),2));data=dict(terms=[dict(symbol=chr(97+i),args=[])for i in range(4)],equalities=[],disequalities=[])
        count=0
        for graph in range(64):
            edges=[list(p) for j,p in enumerate(pairs)if graph&(1<<j)];data['disequalities']=edges;m=len(edges)
            for hard in range(1<<m):
                for cap in [1,2]:
                    self.check_reference(dict(input=data,limit=cap,costs=[(j+graph)%4 for j in range(m)],protected=[j for j in range(m)if hard&(1<<j)]));count+=1
        self.assertEqual(count,1458)

    def test_seeded_functional_reference_and_policy_monotonicity(self):
        rng=random.Random(671818)
        for trial in range(40):
            terms=[]
            for i in range(5):
                if i>1 and rng.random()<.7:
                    arity=rng.choice([1,2]);terms.append(dict(symbol='f'if arity==1 else'g',args=[rng.randrange(i)for _ in range(arity)]))
                else:terms.append(dict(symbol='x'+str(i),args=[]))
            eq=[[rng.randrange(5),rng.randrange(5)]for _ in range(2)];ne=[[rng.randrange(5),rng.randrange(5)]for _ in range(3)];raw=dict(input=dict(terms=terms,equalities=eq,disequalities=ne),limit=2,costs=[rng.randrange(4)for _ in range(5)],protected=[j for j in range(5)if rng.random()<.2]);r=self.check_reference(raw);self.assertTrue(verify(r))
            expensive=copy.deepcopy(raw);expensive['costs']=[x+1 for x in raw['costs']];s=analyze(expensive)
            if r['optimum_cost']is not None:self.assertGreaterEqual(s['optimum_cost'],r['optimum_cost']);self.assertTrue(all(p['minimal']for p in s['feasible']if p['mask']in s['optimal_masks']))
            pinned=copy.deepcopy(raw);pinned['protected']=list(range(5));t=analyze(pinned);self.assertTrue(set(p['mask']for p in t['feasible'])<=set(p['mask']for p in r['feasible']))

    def test_cost_variants_exhaustive_and_protected_cores(self):
        base=copy.deepcopy(CONTROLS[5]['input']);count=0
        for costs in itertools.product(range(3),repeat=3):
            for hard in range(8):
                base['costs']=list(costs);base['protected']=[j for j in range(3)if hard&(1<<j)];r=self.check_reference(base);self.assertTrue(verify(r));count+=1
        self.assertEqual(count,216)
        for i in [3,4,13]:
            r=analyze(CONTROLS[i]['input']);self.assertEqual(r['feasible'],[]);self.assertIsNone(r['optimum_cost']);self.assertTrue(r['blocked_cores'])

    def test_validation_and_independent_verifier(self):
        raw=copy.deepcopy(CONTROLS[0]['input']);bad=[]
        for field,vals in [('costs',[None,{},[],[True,1,2],[-1,1,2],[1.0,1,2],[1000001,1,2],[float('nan'),1,2]]),('protected',[None,{},[True],[0.0],[-1],[3],[1,0],[0,0]])]:
            for v in vals:b=copy.deepcopy(raw);b[field]=v;bad.append(b)
        bad.extend([None,[],dict(raw,extra=0),{k:v for k,v in raw.items()if k!='costs'}])
        for b in bad:
            with self.assertRaises(ValueError):analyze(b)
        r=analyze(raw)
        with patch('euflab.planner.analyze',side_effect=AssertionError),patch('euflab.planner.diagnose',side_effect=AssertionError),patch('euflab.planner._model',side_effect=AssertionError),patch('euflab.cardinality.analyze',side_effect=AssertionError),patch('euflab.cardinality.atlas',side_effect=AssertionError):self.assertTrue(verify(r))

    def test_reject_forged_missing_noncanonical_and_type_confused_reports(self):
        r=analyze(CONTROLS[7]['input']);mutations=[]
        for field,value in [('schema','wrong'),('optimum_cost',False),('optimal_masks',[1]),('frontier_masks',[]),('blocked_cores',[0]),('feasible',r['feasible'][:-1]),('protected',[0]),('costs',[1,1,1])]:
            b=copy.deepcopy(r);b[field]=value;mutations.append(b)
        for field in ['cost','count','mask','partition','minimum_domain_size']:
            b=copy.deepcopy(r);b['feasible'][0][field]=True;mutations.append(b)
        b=copy.deepcopy(r);b['feasible'][0]['minimal']=1;mutations.append(b)
        b=copy.deepcopy(r);b['feasible'][0]['model']['default']=99;mutations.append(b)
        b=copy.deepcopy(r);b['feasible'][0]['model']['functions'][0]['rows'][0]['value']=99;mutations.append(b)
        b=copy.deepcopy(r);b['diagnosis']['subsets'].pop();mutations.append(b)
        b=copy.deepcopy(r);b['feasible'].reverse();mutations.append(b)
        b=copy.deepcopy(r);b['feasible'][0]['kept']=[];mutations.append(b)
        b=copy.deepcopy(r);b['extra']=1;mutations.append(b)
        for b in mutations:
            with self.assertRaises(ValueError):verify(b)

    def test_cli_roundtrip_atomic_errors_and_size_caps(self):
        raw=CONTROLS[0]['input'];cmd=[sys.executable,'-m','euflab.planner'];p=subprocess.run(cmd+['-'],input=json.dumps(raw),text=True,capture_output=True);self.assertEqual(p.returncode,0,p.stderr);self.assertTrue(verify(json.loads(p.stdout)))
        q=subprocess.run(cmd+['-','--verify'],input=p.stdout,text=True,capture_output=True);self.assertEqual(q.returncode,0,q.stderr);self.assertEqual(json.loads(q.stdout),dict(valid=True,schema='euflab-planner-v1'))
        with tempfile.TemporaryDirectory()as tmp:
            out=Path(tmp)/'report.json';out.write_text('preserve')
            for value,extra in [('{',[]),(' '*65537,[]),(' '*((8<<20)+1),['--verify'])]:
                q=subprocess.run(cmd+['-','--output',str(out)]+extra,input=value,text=True,capture_output=True);self.assertEqual(q.returncode,2);self.assertEqual(q.stdout,'');self.assertEqual(out.read_text(),'preserve');self.assertTrue(q.stderr)
