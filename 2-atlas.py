"""Complete bounded term-partition atlas. Not a count of full interpretations."""
from . import validate, _model


def partitions(n):
    """Restricted-growth recursion; expose each block's smallest original ID."""
    def visit(labels,largest):
        if len(labels)==n:
            first={}
            yield [first.setdefault(x,i)for i,x in enumerate(labels)]
        else:
            for x in range(largest+2):yield from visit(labels+[x],max(x,largest))
    yield from visit([0],0)


def compatible(data,p):
    if any(p[a]!=p[b]for a,b in data['equalities'])or any(p[a]==p[b]for a,b in data['disequalities']):return False
    rows={}
    for i,t in enumerate(data['terms']):
        key=(t['symbol'],tuple(p[a]for a in t['args']))
        if key in rows and rows[key]!=p[i]:return False
        rows[key]=p[i]
    return True


def analyze(raw):
    data=validate(raw);n=len(data['terms']);allp=list(partitions(n));ps=sorted(p for p in allp if compatible(data,p));hist=[];needed=set();pairs=[]
    for size in range(1,n+1):
        ids=[i for i,p in enumerate(ps)if len(set(p))==size]
        if ids:hist.append(dict(size=size,count=len(ids),witness=ids[0]));needed.add(ids[0])
    for a in range(n):
        row=[]
        for b in range(n):
            yes=next((i for i,p in enumerate(ps)if p[a]==p[b]),None);no=next((i for i,p in enumerate(ps)if p[a]!=p[b]),None)
            state='inconsistent'if not ps else 'forced-equal'if no is None else 'forced-different'if yes is None else 'flexible'
            row.append(dict(state=state,equal_witness=yes,different_witness=no));needed.update(i for i in [yes,no]if i is not None)
        pairs.append(row)
    return dict(schema='euflab-atlas-v1',input=data,satisfiable=bool(ps),candidate_count=len(allp),partitions=ps,histogram=hist,minimum_domain_size=hist[0]['size']if hist else None,pairs=pairs,witnesses=[dict(partition=i,model=_model(data,ps[i]))for i in sorted(needed)])


def verify(report):
    """Independent subset/block cover enumeration and direct semantic evaluation."""
    import json
    def fail():raise ValueError('Invalid finite-model atlas')
    keys={'schema','input','satisfiable','candidate_count','partitions','histogram','minimum_domain_size','pairs','witnesses'}
    if type(report)is not dict or set(report)!=keys:fail()
    data=validate(report['input']);ts=data['terms'];n=len(ts)
    def cover(left,blocks):
        if not left:
            p=[0]*n
            for block in blocks:
                for i in block:p[i]=min(block)
            yield p;return
        first=min(left);rest=sorted(left-{first})
        for mask in range(1<<len(rest)):
            block={first}|{v for k,v in enumerate(rest)if mask&(1<<k)}
            yield from cover(left-block,blocks+[block])
    ps=[];count=0
    for p in cover(set(range(n)),[]):
        count+=1
        if any(p[a]!=p[b]for a,b in data['equalities'])or any(p[a]==p[b]for a,b in data['disequalities']):continue
        sound=True
        for i,x in enumerate(ts):
            for j,y in enumerate(ts):
                if x['symbol']==y['symbol']and [p[a]for a in x['args']]==[p[a]for a in y['args']]and p[i]!=p[j]:sound=False
        if sound:ps.append(p)
    ps.sort();hist=[];needed=set();pairs=[]
    for size in sorted({len(set(p))for p in ps}):
        ids=[i for i,p in enumerate(ps)if len(set(p))==size];hist.append(dict(size=size,count=len(ids),witness=ids[0]));needed.add(ids[0])
    for a in range(n):
        row=[]
        for b in range(n):
            eq=[i for i,p in enumerate(ps)if p[a]==p[b]];ne=[i for i,p in enumerate(ps)if p[a]!=p[b]]
            yes=eq[0]if eq else None;no=ne[0]if ne else None
            state='inconsistent'if not ps else 'flexible'if eq and ne else 'forced-equal'if eq else 'forced-different'
            row.append(dict(state=state,equal_witness=yes,different_witness=no));needed.update(i for i in [yes,no]if i is not None)
        pairs.append(row)
    witnesses=[]
    for ix in sorted(needed):
        p=ps[ix];fs=[]
        for s in sorted({t['symbol']for t in ts}):
            nodes=[i for i,t in enumerate(ts)if t['symbol']==s];args=sorted({tuple(p[a]for a in ts[i]['args'])for i in nodes});rows=[]
            for key in args:
                ids=[i for i in nodes if tuple(p[a]for a in ts[i]['args'])==key];rows.append(dict(args=list(key),value=p[ids[0]],terms=ids))
            fs.append(dict(symbol=s,arity=len(ts[nodes[0]]['args']),rows=rows))
        m=dict(domain=sorted(set(p)),term_values=p,default=min(p),functions=fs);values=[]
        for t in ts:
            f=next(f for f in fs if f['symbol']==t['symbol']);arg=[values[j]for j in t['args']];values.append(next((r['value']for r in f['rows']if r['args']==arg),m['default']))
        if values!=p:fail()
        witnesses.append(dict(partition=ix,model=m))
    expected=dict(schema='euflab-atlas-v1',input=data,satisfiable=bool(ps),candidate_count=count,partitions=ps,histogram=hist,minimum_domain_size=hist[0]['size']if hist else None,pairs=pairs,witnesses=witnesses)
    # JSON serialization preserves boolean versus integer and rejects nonfinite values.
    try:
        if json.dumps(report,sort_keys=True,allow_nan=False)!=json.dumps(expected,sort_keys=True,allow_nan=False):fail()
    except (TypeError,ValueError,OverflowError):fail()
    return True


if __name__=='__main__':
    from .__main__ import main
    raise SystemExit(main(analyze,verify,'euflab-atlas-v1'))


def cli():
    from .__main__ import main
    return main(analyze,verify,'euflab-atlas-v1')
