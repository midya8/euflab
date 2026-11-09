"""Complete bounded costed deletion planning, with hard protected occurrences."""
from .cardinality import analyze as diagnose, verify as verify_diagnosis, validate_request
from . import _model


def validate_plan(raw):
    if type(raw)is not dict or set(raw)!={'input','limit','costs','protected'}:raise ValueError('Expected input, limit, costs and protected')
    data,k=validate_request(dict(input=raw['input'],limit=raw['limit']));m=len(data['equalities'])+len(data['disequalities']);costs=raw['costs'];protected=raw['protected']
    if type(costs)is not list or len(costs)!=m or any(type(c)is not int or not 0<=c<=1000000 for c in costs):raise ValueError('One integer deletion cost from 0 to 1000000 per occurrence')
    if type(protected)is not list or any(type(j)is not int or not 0<=j<m for j in protected)or protected!=sorted(set(protected)):raise ValueError('Protected IDs must be unique, increasing occurrence IDs')
    return data,k,costs,protected


def analyze(raw):
    data,k,costs,protected=validate_plan(raw);d=diagnose(dict(input=data,limit=k));m=len(costs);full=(1<<m)-1;hard=sum(1<<j for j in protected);minimal={sum(1<<j for j in p['removed'])for p in d['repairs']};totals=[0]*(1<<m);plans=[]
    for mask in range(1<<m):
        if mask:bit=mask&-mask;totals[mask]=totals[mask^bit]+costs[bit.bit_length()-1]
        kept=full^mask;s=d['subsets'][kept]
        if mask&hard or s['minimum_domain_size']is None or s['minimum_domain_size']>k:continue
        p=d['background']['partitions'][s['witness']]
        plans.append(dict(mask=mask,removed=[j for j in range(m)if mask&(1<<j)],kept=[j for j in range(m)if kept&(1<<j)],cost=totals[mask],count=mask.bit_count(),minimal=mask in minimal,minimum_domain_size=s['minimum_domain_size'],partition=s['witness'],model=_model(data,p)))
    optimum=min((p['cost']for p in plans),default=None);bycount=[min((p['cost']for p in plans if p['count']==i),default=None)for i in range(m+1)]
    frontier=[p['mask']for p in plans if not any(c is not None and c<=p['cost']and(i<p['count']or c<p['cost'])for i,c in enumerate(bycount[:p['count']+1]))]
    return dict(schema='euflab-planner-v1',diagnosis=d,costs=costs,protected=protected,feasible=plans,optimum_cost=optimum,optimal_masks=[p['mask']for p in plans if p['cost']==optimum],frontier_masks=frontier,blocked_cores=[i for i,c in enumerate(d['cores'])if set(c['assertions'])<=set(protected)])


def verify(report):
    """Verify diagnosis, then enumerate all masks and pairwise objective dominance."""
    import json
    def fail():raise ValueError('Invalid planner report')
    if type(report)is not dict or set(report)!={'schema','diagnosis','costs','protected','feasible','optimum_cost','optimal_masks','frontier_masks','blocked_cores'}:fail()
    d=report['diagnosis'];verify_diagnosis(d);data,k,costs,protected=validate_plan(dict(input=d['input'],limit=d['limit'],costs=report['costs'],protected=report['protected']));m=len(costs);full=(1<<m)-1;plans=[]
    # Rebuild canonical function rows here, not through the native model builder.
    for mask in range(1<<m):
        removed=[j for j in range(m)if mask&(1<<j)];kept=[j for j in range(m)if j not in removed];s=d['subsets'][full^mask]
        if set(removed)&set(protected)or s['minimum_domain_size']is None or s['minimum_domain_size']>k:continue
        p=d['background']['partitions'][s['witness']];functions=[]
        for symbol in sorted({t['symbol']for t in data['terms']}):
            nodes=[i for i,t in enumerate(data['terms'])if t['symbol']==symbol];rows=[]
            for args in sorted({tuple(p[a]for a in data['terms'][i]['args'])for i in nodes}):
                origin=[i for i in nodes if tuple(p[a]for a in data['terms'][i]['args'])==args];rows.append(dict(args=list(args),value=p[origin[0]],terms=origin))
            functions.append(dict(symbol=symbol,arity=len(data['terms'][nodes[0]]['args']),rows=rows))
        model=dict(domain=sorted(set(p)),term_values=p,default=min(p),functions=functions);values=[]
        for t in data['terms']:
            f=next(f for f in functions if f['symbol']==t['symbol']);args=[values[a]for a in t['args']];values.append(next((r['value']for r in f['rows']if r['args']==args),model['default']))
        if values!=p or len(model['domain'])>k:fail()
        for j in kept:
            a=d['assertions'][j];x,y=a['pair']
            if((values[x]==values[y])!=(a['kind']=='equalities')):fail()
        proper=[q for q in range(1<<m)if q!=mask and(q&mask)==q];minimal=all(d['subsets'][full^q]['minimum_domain_size']is None or d['subsets'][full^q]['minimum_domain_size']>k for q in proper)
        plans.append(dict(mask=mask,removed=removed,kept=kept,cost=sum(costs[j]for j in removed),count=len(removed),minimal=minimal,minimum_domain_size=s['minimum_domain_size'],partition=s['witness'],model=model))
    optimum=min((p['cost']for p in plans),default=None);frontier=[p['mask']for p in plans if not any(q['cost']<=p['cost']and q['count']<=p['count']and(q['cost']<p['cost']or q['count']<p['count'])for q in plans)]
    expected=dict(schema='euflab-planner-v1',diagnosis=d,costs=costs,protected=protected,feasible=plans,optimum_cost=optimum,optimal_masks=[p['mask']for p in plans if p['cost']==optimum],frontier_masks=frontier,blocked_cores=[i for i,c in enumerate(d['cores'])if all(j in protected for j in c['assertions'])])
    try:
        if json.dumps(expected,sort_keys=True,allow_nan=False)!=json.dumps(report,sort_keys=True,allow_nan=False):fail()
    except(TypeError,ValueError,OverflowError):fail()
    return True


def cli():
    from .__main__ import main
    return main(analyze,verify,'euflab-planner-v1')


if __name__=='__main__':raise SystemExit(cli())
