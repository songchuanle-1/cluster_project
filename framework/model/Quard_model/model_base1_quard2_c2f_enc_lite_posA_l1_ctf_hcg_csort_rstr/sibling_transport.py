"""Fixed projection-free, reversible fine-sibling transport (diagnostic R0)."""
import math
import torch


def transport(tokens, parent, counts, wrong_affinity=False, heads=8, matrices=False):
    assert tokens.ndim==2 and tokens.shape[1]%heads==0
    assert parent.numel()==counts.numel()==tokens.shape[0]
    assert tokens.dtype==torch.float32
    dim=tokens.shape[1]//heads
    output=tokens.clone()
    stats=[]
    valid=counts>0
    for owner in parent[valid].unique(sorted=True):
        indices=torch.nonzero(valid & (parent==owner),as_tuple=False).flatten()
        values=tokens[indices].reshape(-1,heads,dim).transpose(0,1)
        mass=counts[indices].to(tokens.dtype)
        pi=mass/mass.sum()
        if wrong_affinity=='equal_mass':
            donor=torch.arange(len(indices),device=tokens.device)
            for size in counts[indices].unique(sorted=True):
                positions=torch.nonzero(counts[indices]==size,as_tuple=False).flatten()
                donor[positions]=positions.roll(1)
            affinity_values=values[:,donor]
        else:
            affinity_values=values.roll(1,dims=1) if wrong_affinity else values
        q=torch.softmax(torch.matmul(affinity_values,affinity_values.transpose(1,2))/math.sqrt(dim),dim=-1)
        flow=pi[None,:,None]*q
        conductance=torch.minimum(flow,flow.transpose(1,2))
        eye=torch.eye(len(indices),device=tokens.device,dtype=tokens.dtype).unsqueeze(0)
        off=(conductance/pi[None,:,None])*(1-eye)
        p=off+torch.diag_embed(1-off.sum(-1))
        changed=torch.matmul(p,values)
        output[indices]=changed.transpose(0,1).reshape(len(indices),-1)
        if matrices:
            stats.append({'indices':indices,'pi':pi,'p':p,'q':q,'before':values,'after':changed})
    return (output,stats) if matrices else output

