"""Exact one-coordinate integer deletion-cost profiles over every feasible plan."""
from .planner import analyze as plan, verify as verify_plan
MAX_COST=1000000


def analyze(raw):
    planning=plan(raw);profiles=[]
    for j,current in enumerate(planning['costs']):
        classes=[]
        for deleted in [False,True]:
            ps=[p for p in planning['feasible']if bool(p['mask']&(1<<j))==deleted];base=min((p['cost']-(current if deleted else 0)for p in ps),default=None)
            classes.append(dict(base=base,masks=[p['mask']for p in ps if p['cost']-(current if deleted else 0)==base]))
        a,b=classes;threshold=a['base']-b['base']if a['base']is not None and b['base']is not None else None
        cuts={0,MAX_COST+1}
        if threshold is not None:
            cuts.update(x for x in [threshold,threshold+1]if 0<x<MAX_COST+1)
        segments=[];cs=sorted(cuts)
        for lo,hi in zip(cs,cs[1:]):
            values=[a['base'],b['base']+lo if b['base']is not None else None];best=min((v for v in values if v is not None),default=None);winning=[i for i,v in enumerate(values)if v is not None and v==best];kind='blocked'if not winning else'tie'if len(winning)==2 else'keep'if winning==[0]else'delete';masks=sorted(x for i in winning for x in classes[i]['masks']);segments.append(dict(lo=lo,hi=hi-1,kind=kind,optimal_masks=masks))
        segment=next(i for i,s in enumerate(segments)if s['lo']<=current<=s['hi']);profiles.append(dict(assertion=j,keep=a,delete=b,crossing=threshold,segments=segments,current_segment=segment))
    return dict(schema='euflab-sensitivity-v1',planning=planning,cost_max=MAX_COST,profiles=profiles)


def verify(report):
    """Independently derive candidate critical points and all minimizing affine lines."""
    import json
    def fail():raise ValueError('Invalid sensitivity report')
    if type(report)is not dict or set(report)!={'schema','planning','cost_max','profiles'}:fail()
    r=report['planning'];verify_plan(r);expected=[]
    for j,current in enumerate(r['costs']):
        lines=[(p['mask'],int(j in p['removed']),sum(r['costs'][i]for i in p['removed']if i!=j))for p in r['feasible']];groups=[]
        for slope in [0,1]:
            values=[v for _,s,v in lines if s==slope];value=min(values)if values else None;groups.append(dict(base=value,masks=[mask for mask,s,v in lines if s==slope and v==value]))
        # All possible cross-slope intersections, not the generator's two-minimum cut.
        cuts={0,MAX_COST+1}
        for _,s,a in lines:
            for _,t,b in lines:
                if s==0 and t==1:
                    for x in [a-b,a-b+1]:
                        if 0<x<MAX_COST+1:cuts.add(x)
        cells=[];cs=sorted(cuts)
        for lo,stop in zip(cs,cs[1:]):
            def winners(x):
                values=[(s*x+b,mask,s)for mask,s,b in lines];v=min((a for a,_,_ in values),default=None);return [mask for a,mask,_ in values if a==v],{s for a,_,s in values if a==v}
            masks,slopes=winners(lo);other,_=winners(stop-1)
            if masks!=other:fail()
            kind='blocked'if not masks else'tie'if len(slopes)==2 else'delete'if slopes=={1}else'keep'
            if cells and cells[-1]['optimal_masks']==masks:cells[-1]['hi']=stop-1
            else:cells.append(dict(lo=lo,hi=stop-1,kind=kind,optimal_masks=masks))
        a,b=groups;expected.append(dict(assertion=j,keep=a,delete=b,crossing=a['base']-b['base']if a['base']is not None and b['base']is not None else None,segments=cells,current_segment=next(i for i,s in enumerate(cells)if s['lo']<=current<=s['hi'])))
    target=dict(schema='euflab-sensitivity-v1',planning=r,cost_max=MAX_COST,profiles=expected)
    try:
        if json.dumps(report,sort_keys=True,allow_nan=False)!=json.dumps(target,sort_keys=True,allow_nan=False):fail()
    except(TypeError,ValueError,OverflowError):fail()
    return True


def cli():
    from .__main__ import main
    return main(analyze,verify,'euflab-sensitivity-v1')


if __name__=='__main__':raise SystemExit(cli())
