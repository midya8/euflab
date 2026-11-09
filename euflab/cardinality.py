"""All assertion cores and deletion repairs under a fixed finite-domain cap."""
from . import validate, _model
from .atlas import analyze as atlas, verify as verify_atlas


def validate_request(raw):
    if type(raw)is not dict or set(raw)!={'input','limit'}:raise ValueError('Expected input and limit')
    data=validate(raw['input']);k=raw['limit']
    if type(k)is not int or not 1<=k<=8:raise ValueError('Domain cap must be an integer from 1 to 8')
    if len(data['equalities'])+len(data['disequalities'])>8:raise ValueError('At most eight assertion occurrences combined')
    return data,k


def analyze(raw):
    data,k=validate_request(raw);lits=[(kind,pair)for kind in ['equalities','disequalities']for pair in data[kind]];m=len(lits);full=(1<<m)-1
    bg=atlas(dict(data,equalities=[],disequalities=[]));ps=bg['partitions'];best=[None]*(1<<m)
    for ix,p in enumerate(ps):
        mask=sum((1<<j)for j,(kind,(a,b))in enumerate(lits)if(p[a]==p[b])==(kind=='equalities'));v=(len(set(p)),ix)
        if best[mask]is None or v<best[mask]:best[mask]=v
    # Superset minima: every model satisfying mask also satisfies every submask.
    for j in range(m):
        for mask in range(1<<m):
            if not mask&(1<<j):
                v=best[mask|(1<<j)]
                if v is not None and(best[mask]is None or v<best[mask]):best[mask]=v
    sat=lambda mask:best[mask]is not None and best[mask][0]<=k
    ids=lambda mask:[j for j in range(m)if mask&(1<<j)]
    witness=lambda mask:dict(partition=best[mask][1],model=_model(data,ps[best[mask][1]]))
    cores=[];repairs=[]
    for mask in range(1<<m):
        if not sat(mask)and all(sat(mask^(1<<j))for j in ids(mask)):
            cores.append(dict(assertions=ids(mask),kind='intrinsic'if best[mask]is None else 'cap-only',relaxations=[dict(removed=j,**witness(mask^(1<<j)))for j in ids(mask)]))
        kept=full^mask
        if sat(kept)and all(not sat(kept|(1<<j))for j in ids(mask)):
            repairs.append(dict(removed=ids(mask),kept=ids(kept),minimum_domain_size=best[kept][0],**witness(kept)))
    cores.sort(key=lambda c:(len(c['assertions']),c['assertions']));repairs.sort(key=lambda c:(len(c['removed']),c['removed']))
    return dict(schema='euflab-cardinality-v1',input=data,limit=k,background=bg,assertions=[dict(id=j,kind=kind,pair=pair)for j,(kind,pair)in enumerate(lits)],satisfiable=sat(full),minimum_domain_size=best[full][0]if best[full]else None,subsets=[dict(mask=i,minimum_domain_size=v[0]if v else None,witness=v[1]if v else None)for i,v in enumerate(best)],cores=cores,repairs=repairs)


def verify(report):
    """Check the complete background independently, then scan each assertion subset."""
    import json,itertools
    def fail():raise ValueError('Invalid cardinality report')
    if type(report)is not dict or set(report)!={'schema','input','limit','background','assertions','satisfiable','minimum_domain_size','subsets','cores','repairs'}:fail()
    data,k=validate_request(dict(input=report['input'],limit=report['limit']));bg=report['background'];verify_atlas(bg)
    if bg['input']!=dict(data,equalities=[],disequalities=[]):fail()
    lits=[(kind,pair)for kind in ['equalities','disequalities']for pair in data[kind]];m=len(lits);ps=bg['partitions'];full=(1<<m)-1;best=[]
    for mask in range(1<<m):
        options=[]
        for ix,p in enumerate(ps):
            if all(not(mask&(1<<j))or((p[a]==p[b])if kind=='equalities'else(p[a]!=p[b]))for j,(kind,(a,b))in enumerate(lits)):options.append((len(set(p)),ix))
        best.append(min(options)if options else None)
    def make_model(mask):
        p=ps[best[mask][1]];fs=[]
        for s in sorted({t['symbol']for t in data['terms']}):
            nodes=[i for i,t in enumerate(data['terms'])if t['symbol']==s];keys=sorted({tuple(p[a]for a in data['terms'][i]['args'])for i in nodes});rows=[]
            for args in keys:
                origin=[i for i in nodes if tuple(p[a]for a in data['terms'][i]['args'])==args];rows.append(dict(args=list(args),value=p[origin[0]],terms=origin))
            fs.append(dict(symbol=s,arity=len(data['terms'][nodes[0]]['args']),rows=rows))
        model=dict(domain=sorted(set(p)),term_values=p,default=min(p),functions=fs);values=[]
        for t in data['terms']:
            f=next(f for f in fs if f['symbol']==t['symbol']);args=[values[a]for a in t['args']];values.append(next((r['value']for r in f['rows']if r['args']==args),model['default']))
        if values!=p or len(model['domain'])>k:fail()
        for j,(kind,(a,b))in enumerate(lits):
            if mask&(1<<j)and((values[a]==values[b])!=(kind=='equalities')):fail()
        return dict(partition=best[mask][1],model=model)
    sat=[v is not None and v[0]<=k for v in best];cores=[];repairs=[]
    # Proper-subset checks here differ from the generator's immediate-neighbor test.
    for length in range(m+1):
        for comb in itertools.combinations(range(m),length):
            mask=sum(1<<j for j in comb);proper=[q for q in range(1<<m)if q!=mask and(q&mask)==q]
            if not sat[mask]and all(sat[q]for q in proper):cores.append(dict(assertions=list(comb),kind='intrinsic'if best[mask]is None else 'cap-only',relaxations=[dict(removed=j,**make_model(mask^(1<<j)))for j in comb]))
            kept=full^mask
            if sat[kept]and all(not sat[full^q]for q in proper):repairs.append(dict(removed=list(comb),kept=[j for j in range(m)if j not in comb],minimum_domain_size=best[kept][0],**make_model(kept)))
    expected=dict(schema='euflab-cardinality-v1',input=data,limit=k,background=bg,assertions=[dict(id=j,kind=kind,pair=pair)for j,(kind,pair)in enumerate(lits)],satisfiable=sat[full],minimum_domain_size=best[full][0]if best[full]else None,subsets=[dict(mask=i,minimum_domain_size=v[0]if v else None,witness=v[1]if v else None)for i,v in enumerate(best)],cores=cores,repairs=repairs)
    try:
        if json.dumps(report,sort_keys=True,allow_nan=False)!=json.dumps(expected,sort_keys=True,allow_nan=False):fail()
    except(TypeError,ValueError,OverflowError):fail()
    return True


def cli():
    from .__main__ import main
    return main(analyze,verify,'euflab-cardinality-v1')


if __name__=='__main__':raise SystemExit(cli())
