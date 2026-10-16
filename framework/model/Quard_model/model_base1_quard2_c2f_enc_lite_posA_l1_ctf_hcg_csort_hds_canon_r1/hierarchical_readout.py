"""One canonical-axis realization of the existing disjoint-support operator."""
import math
import torch

def support_masks(leaf,parent1,parent2,sizes):
    device=leaf.device
    valid_fine=torch.zeros(sizes[0],dtype=torch.bool,device=device)
    valid_fine[leaf.unique()]=True
    valid_middle=torch.zeros(sizes[1],dtype=torch.bool,device=device)
    valid_middle[parent1[leaf.unique()]]=True
    valid_coarse=torch.zeros(sizes[2],dtype=torch.bool,device=device)
    valid_coarse[parent2[parent1[leaf.unique()]]]=True
    mid=parent1[leaf]
    coarse=parent2[mid]
    p1=torch.full((sizes[0],),-1,dtype=torch.long,device=device)
    p2=torch.full((sizes[1],),-1,dtype=torch.long,device=device)
    p1[:len(parent1)]=parent1
    p2[:len(parent2)]=parent2
    fine=(p1[None,:]==mid[:,None])&valid_fine[None,:]
    middle=(p2[None,:]==coarse[:,None])&(torch.arange(sizes[1],device=device)[None,:]!=mid[:,None])&valid_middle[None,:]
    top=(torch.arange(sizes[2],device=device)[None,:]!=coarse[:,None])&valid_coarse[None,:]
    return fine,middle,top

def canonical(points,banks,leaf,parent1,parent2,weights,heads=8):
    valid=len(leaf)
    if not valid:return points*0
    channels=points.shape[-1]
    dim=channels//heads
    query=points[:valid].reshape(valid,heads,dim).transpose(0,1)
    masks=support_masks(leaf,parent1,parent2,[len(bank) for bank in banks])
    output=points[:valid]*0
    for level,(bank,allowed) in enumerate(zip(banks,masks)):
        key=bank.reshape(-1,heads,dim).transpose(0,1)
        scores=(query@key.transpose(-1,-2))/math.sqrt(dim)
        nonempty=allowed.any(dim=-1)
        scores=scores.masked_fill(~allowed.unsqueeze(0),-torch.inf)
        scores=torch.where(nonempty[None,:,None],scores,torch.zeros_like(scores))
        probabilities=scores.softmax(dim=-1)*allowed.unsqueeze(0)
        value=(probabilities@key).transpose(0,1).reshape(valid,channels)
        output=output+value*weights[:valid,level:level+1]
    return torch.cat([output,points[valid:]*0],dim=0)
