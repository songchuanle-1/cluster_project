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


def primitive_tests(device):
    torch.manual_seed(1999)
    values=torch.randn(7,256,device=device,dtype=torch.float32,requires_grad=True)
    parent=torch.tensor([0,0,0,1,1,2,3],device=device)
    counts=torch.tensor([1,2,4,3,5,7,0],device=device)
    output,groups=transport(values,parent,counts,matrices=True)
    errors={'row_sum':0.,'stationarity':0.,'detailed_balance':0.,'weighted_mean':0.}
    minimum=1.
    for g in groups:
        p,pi=g['p'],g['pi']
        errors['row_sum']=max(errors['row_sum'],float((p.sum(-1)-1).abs().max()))
        flow=pi[None,:,None]*p
        errors['detailed_balance']=max(errors['detailed_balance'],float((flow-flow.transpose(1,2)).abs().max()))
        errors['stationarity']=max(errors['stationarity'],float(((pi[None,:,None]*p).sum(1)-pi).abs().max()))
        before=(g['before'].double()*pi.double()[None,:,None]).sum(1)
        after=(g['after'].double()*pi.double()[None,:,None]).sum(1)
        errors['weighted_mean']=max(errors['weighted_mean'],float((before-after).abs().max()))
        minimum=min(minimum,float(p.min()))
    constant=torch.ones_like(values)*.25
    errors['constant_identity']=float((transport(constant,parent,counts)-constant).abs().max())
    errors['singleton_identity']=float((output[5]-values[5]).abs().max())
    errors['padding_identity']=float((output[6]-values[6]).abs().max())
    permutation=torch.tensor([4,2,6,0,5,1,3],device=device)
    inverse=torch.argsort(permutation)
    restored=transport(values[permutation],parent[permutation],counts[permutation])[inverse]
    errors['relabel_inverse']=float((restored-output).abs().max())
    receiver_probe=torch.linspace(-1,1,256,device=device)
    gradient=torch.autograd.grad((output[0]*receiver_probe).sum(),values,retain_graph=True)[0]
    errors['cross_parent_gradient']=float(gradient[3:].abs().max())
    sibling_gradient=float(gradient[1:3].abs().max())
    all_gradient=torch.autograd.grad(output.square().mean(),values)[0]
    return {'errors':errors,'minimum_transition':minimum,'finite_gradients':bool(torch.isfinite(all_gradient).all()),
        'sibling_gradient_max':sibling_gradient,'passed':max(errors.values())<=1e-6 and minimum>=0 and bool(torch.isfinite(all_gradient).all()) and sibling_gradient>1e-6}
