"""Read-only native fine-attention support and target-mixing statistics."""
import math
import torch

def prepare(features,graph,heads=8):
    n,c=features.shape;d=c//heads
    ids=graph['indices'].to(features.device);allowed=graph['allowed'].to(features.device)
    gathered=features[ids].reshape(n,ids.shape[1],heads,d)
    scores=(features.reshape(n,1,heads,d)*gathered).sum(-1)/math.sqrt(d)
    probability=scores.masked_fill(~allowed.unsqueeze(-1),-torch.inf).softmax(1)
    source=(probability.unsqueeze(-1)*gathered).sum(1).reshape(n,c)
    self_edge=(ids==torch.arange(n,device=features.device).unsqueeze(-1))&allowed
    groups=graph['group_ids'].to(features.device)
    count=torch.bincount(groups).to(features.dtype)
    fallback=graph['fallback'].to(features.device)
    if bool(fallback.any()):
        mean=features.new_zeros(len(count),c).index_add(0,groups,features)/count.unsqueeze(-1)
        source=torch.where(fallback.unsqueeze(-1),mean[groups],source)
    return source,{'ids':ids,'allowed':allowed,'nonself':allowed&~self_edge,'probability':probability,
                   'groups':groups,'count':count,'fallback':fallback,'heads':heads}

def mixing(state,labels):
    ids=state['ids'];support=state['nonself'];p=state['probability'];heads=state['heads']
    labels=labels.to(p.device)
    assert labels.ndim==1 and len(labels)==len(ids) and bool(((labels==0)|(labels==1)).all())
    cross=(labels[ids]!=labels.unsqueeze(-1))&support
    mass=(p*support.unsqueeze(-1)).sum(1)
    cross_mass=(p*cross.unsqueeze(-1)).sum(1)
    degree=support.sum(1)
    uniform=cross.sum(1).to(p.dtype)/degree.clamp_min(1)
    if bool(state['fallback'].any()):
        g=state['groups'];count=state['count'];fallback=state['fallback']
        positive=p.new_zeros(len(count)).index_add(0,g,labels.to(p.dtype))
        cross_count=torch.where(labels.bool(),count[g]-positive[g],positive[g])
        cross_mass=torch.where(fallback.unsqueeze(-1),(cross_count/count[g]).unsqueeze(-1).expand(-1,heads),cross_mass)
        mass=torch.where(fallback.unsqueeze(-1),((count[g]-1)/count[g]).unsqueeze(-1).expand(-1,heads),mass)
        uniform=torch.where(fallback,cross_count/(count[g]-1).clamp_min(1),uniform)
        degree=torch.where(fallback,(count[g]-1).long(),degree)
    eligible=(mass>0)&(degree>0).unsqueeze(-1)
    fraction=cross_mass/mass.clamp_min(torch.finfo(p.dtype).tiny)
    delta=fraction-uniform.unsqueeze(-1)
    summaries={}
    for name,target in [('target',True),('background',False)]:
        wanted=(labels.bool()==target).unsqueeze(-1).expand(-1,heads)
        take=eligible&wanted
        summaries[name+'_recipients']=int((labels.bool()==target).sum())
        summaries[name+'_eligible_recipients']=int((take.any(-1)).sum())
        summaries[name+'_eligible_head_vectors']=int(take.sum())
        summaries[name+'_weighted_cross_fraction']=float(fraction[take].mean().cpu()) if bool(take.any()) else None
        summaries[name+'_uniform_cross_fraction']=float(uniform.unsqueeze(-1).expand_as(fraction)[take].mean().cpu()) if bool(take.any()) else None
        summaries[name+'_weighted_minus_uniform']=float(delta[take].mean().cpu()) if bool(take.any()) else None
    summaries.update(mean_nonself_mass=float(mass.mean().cpu()),fallback_recipients=int(state['fallback'].sum()),singleton_recipients=int((degree==0).sum()))
    return summaries,{'fraction':fraction,'uniform':uniform,'eligible':eligible,'cross_mass':cross_mass}
