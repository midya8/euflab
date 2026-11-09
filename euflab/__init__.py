"""Tiny ground EUF, proof-producing union-find and independent relation replay."""
import re
from collections import deque


def validate(raw):
    if type(raw) is not dict or set(raw) != {'terms','equalities','disequalities'}:
        raise ValueError('Input needs exactly terms, equalities, disequalities')
    integer=lambda x:type(x)in (int,float)and -1000000<x<1000000 and int(x)==x
    ts=raw['terms']
    if type(ts) is not list or not 1 <= len(ts) <= 8:raise ValueError('Need 1..8 terms')
    signatures={};terms=[]
    for i,t in enumerate(ts):
        if type(t) is not dict or set(t)!={'symbol','args'}:raise ValueError('Term needs symbol and args')
        s=t['symbol'];args=t['args']
        if type(s) is not str or not re.fullmatch('[a-z][a-z0-9_]{0,7}',s):raise ValueError('Invalid symbol')
        if type(args) is not list or len(args)>2 or any(not integer(x) or not 0<=x<i for x in args):raise ValueError('Arguments must be earlier term IDs, arity at most 2')
        if s in signatures and signatures[s]!=len(args):raise ValueError('A symbol has one fixed arity')
        signatures[s]=len(args);terms.append(dict(symbol=s,args=list(map(int,args))))
    out={'terms':terms}
    for k in ['equalities','disequalities']:
        xs=raw[k]
        if type(xs)is not list or len(xs)>8 or any(type(x)is not list or len(x)!=2 or any(not integer(v) or not 0<=v<len(ts)for v in x)for x in xs):raise ValueError('At most 8 pairs of valid term IDs')
        out[k]=[list(map(int,x))for x in xs]
    return out


def _model(data,reps):
    functions=[];ts=data['terms']
    for s in sorted({t['symbol']for t in ts}):
        rows={}
        for i,t in enumerate(ts):
            if t['symbol']==s:
                key=tuple(reps[a]for a in t['args'])
                if key not in rows:rows[key]={'args':list(key),'value':reps[i],'terms':[]}
                rows[key]['terms'].append(i)
        functions.append(dict(symbol=s,arity=len(next(t['args']for t in ts if t['symbol']==s)),rows=[rows[k]for k in sorted(rows)]))
    return dict(domain=sorted(set(reps)),term_values=reps,default=min(reps),functions=functions)


def analyze(raw):
    data=validate(raw);ts=data['terms'];n=len(ts);parent=list(range(n));graph=[[]for _ in ts];proofs=[];cache={}
    def add(rule,a,b,premises=(),**kw):
        proofs.append(dict(rule=rule,left=a,right=b,premises=list(premises),**kw));return len(proofs)-1
    def find(x):
        while parent[x]!=x:x=parent[x]
        return x
    for i in range(n):cache[i,i]=add('reflexivity',i,i)
    def merge(a,b,p):
        x,y=find(a),find(b)
        if x==y:return False
        parent[max(x,y)]=min(x,y);graph[a].append((b,p));graph[b].append((a,p));return True
    def prove(a,b):
        if (a,b)in cache:return cache[a,b]
        queue=deque([a]);prev={a:None}
        while b not in prev:
            x=queue.popleft()
            for y,p in graph[x]:
                if y not in prev:prev[y]=(x,p);queue.append(y)
        path=[];x=b
        while x!=a:
            y,p=prev[x];q=proofs[p]
            if (q['left'],q['right'])!=(y,x):p=add('symmetry',y,x,[p])
            path.append(p);x=y
        path.reverse();p=path[0]
        for q in path[1:]:p=add('transitivity',a,proofs[q]['right'],[p,q])
        cache[a,b]=p;return p
    for i,(a,b)in enumerate(data['equalities']):merge(a,b,add('assumption',a,b,assumption=i))
    while True:
        changed=False
        for a in range(n):
            for b in range(a+1,n):
                x,y=ts[a],ts[b]
                if find(a)!=find(b)and x['symbol']==y['symbol']and all(find(i)==find(j)for i,j in zip(x['args'],y['args'])):
                    p=add('congruence',a,b,[prove(i,j)for i,j in zip(x['args'],y['args'])]);merge(a,b,p);changed=True;break
            if changed:break
        if not changed:break
    equal=[[find(a)==find(b)for b in range(n)]for a in range(n)]
    evidence=[[prove(a,b)if equal[a][b]else None for b in range(n)]for a in range(n)]
    reps=[find(a)for a in range(n)];classes=[[i for i in range(n)if reps[i]==r]for r in sorted(set(reps))]
    conflicts=[dict(index=i,proof=evidence[a][b])for i,(a,b)in enumerate(data['disequalities'])if equal[a][b]]
    return dict(schema='euflab-v1',input=data,consistent=not conflicts,classes=classes,equal=equal,proofs=proofs,evidence=evidence,conflicts=conflicts,model=None if conflicts else _model(data,reps))


def verify(report):
    """Independent complete relational saturation plus local proof/model checks. No generator calls."""
    def fail():raise ValueError('Invalid EUF certificate')
    if type(report)is not dict or set(report)!={'schema','input','consistent','classes','equal','proofs','evidence','conflicts','model'}:fail()
    data=validate(report['input']);ts=data['terms'];n=len(ts)
    # Fixed-point relation, not union-find or proof-graph traversal.
    relation={(i,i)for i in range(n)}|{tuple(e)for e in data['equalities']}
    while True:
        old=set(relation);relation|={(b,a)for a,b in old}
        relation|={(a,c)for a,b in old for x,c in old if b==x}
        relation|={(a,b)for a,x in enumerate(ts)for b,y in enumerate(ts)if x['symbol']==y['symbol']and all((i,j)in old for i,j in zip(x['args'],y['args']))}
        if relation==old:break
    equal=[[(a,b)in relation for b in range(n)]for a in range(n)]
    reps=[min(b for b in range(n)if (a,b)in relation)for a in range(n)]
    classes=[[a for a in range(n)if reps[a]==r]for r in sorted(set(reps))]
    def strict(a,b):
        if type(a)is not type(b):return False
        if type(a)is dict:return set(a)==set(b)and all(strict(a[k],b[k])for k in a)
        if type(a)is list:return len(a)==len(b)and all(strict(x,y)for x,y in zip(a,b))
        return a==b
    if not strict(report['input'],data)or report['schema']!='euflab-v1' or not strict(report['equal'],equal)or not strict(report['classes'],classes):fail()
    ps=report['proofs']
    if type(ps)is not list or len(ps)>4096:fail()
    for k,p in enumerate(ps):
        if type(p)is not dict or not {'rule','left','right','premises'}<=set(p):fail()
        rule=p['rule'];a=p['left'];b=p['right'];prem=p['premises']
        if type(rule)is not str or rule not in ['reflexivity','assumption','symmetry','transitivity','congruence']:fail()
        if set(p)!=({'rule','left','right','premises','assumption'}if rule=='assumption'else {'rule','left','right','premises'}):fail()
        if any(type(v)is not int or not 0<=v<n for v in [a,b])or type(prem)is not list or any(type(v)is not int or not 0<=v<k for v in prem):fail()
        ends=[(ps[i]['left'],ps[i]['right'])for i in prem]
        if rule=='reflexivity' and (a!=b or prem):fail()
        if rule=='assumption':
            ix=p['assumption']
            if type(ix)is not int or not 0<=ix<len(data['equalities'])or data['equalities'][ix]!=[a,b]or prem:fail()
        if rule=='symmetry' and ends!=[(b,a)]:fail()
        if rule=='transitivity' and (len(ends)!=2 or ends[0][0]!=a or ends[0][1]!=ends[1][0]or ends[1][1]!=b):fail()
        if rule=='congruence' and (ts[a]['symbol']!=ts[b]['symbol']or ends!=list(zip(ts[a]['args'],ts[b]['args']))):fail()
    ev=report['evidence']
    if type(ev)is not list or len(ev)!=n or any(type(row)is not list or len(row)!=n for row in ev):fail()
    for a in range(n):
        for b in range(n):
            p=ev[a][b]
            if equal[a][b]:
                if type(p)is not int or not 0<=p<len(ps)or (ps[p]['left'],ps[p]['right'])!=(a,b):fail()
            elif p is not None:fail()
    conflicts=[dict(index=i,proof=ev[a][b])for i,(a,b)in enumerate(data['disequalities'])if equal[a][b]]
    if not strict(report['conflicts'],conflicts)or not strict(report['consistent'],not conflicts):fail()
    if conflicts:
        if report['model']is not None:fail()
    else:
        # Rebuild interpretation independently, then evaluate every original term.
        funcs=[]
        for s in sorted({t['symbol']for t in ts}):
            nodes=[i for i,t in enumerate(ts)if t['symbol']==s];keys=sorted({tuple(reps[j]for j in ts[i]['args'])for i in nodes});rows=[]
            for key in keys:
                origins=[i for i in nodes if tuple(reps[j]for j in ts[i]['args'])==key]
                values={reps[i]for i in origins}
                if len(values)!=1:fail()
                rows.append(dict(args=list(key),value=values.pop(),terms=origins))
            funcs.append(dict(symbol=s,arity=len(ts[nodes[0]]['args']),rows=rows))
        model=dict(domain=sorted(set(reps)),term_values=reps,default=min(reps),functions=funcs)
        if not strict(report['model'],model):fail()
        vals=[]
        for t in ts:
            f=next(f for f in funcs if f['symbol']==t['symbol']);key=[vals[j]for j in t['args']];vals.append(next((r['value']for r in f['rows']if r['args']==key),model['default']))
        if vals!=reps or any(vals[a]!=vals[b]for a,b in data['equalities'])or any(vals[a]==vals[b]for a,b in data['disequalities']):fail()
    return True
