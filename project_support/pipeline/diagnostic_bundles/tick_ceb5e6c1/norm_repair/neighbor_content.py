"""Read-only fine-message decomposition and matched diagnostic intervention."""
import math
import numpy as np
import torch


def decompose(features, graph, heads=8):
    n,channels=features.shape
    dim=channels//heads
    indices=graph["indices"].to(features.device)
    allowed=graph["allowed"].to(features.device)
    gathered=features[indices].reshape(n,indices.shape[1],heads,dim)
    query=features.reshape(n,1,heads,dim)
    scores=(query*gathered).sum(-1)/math.sqrt(dim)
    scores=scores.masked_fill(~allowed.unsqueeze(-1),-torch.inf)
    probability=scores.softmax(1)
    ordinary=(probability.unsqueeze(-1)*gathered).sum(1).reshape(n,channels)
    self_edge=(indices==torch.arange(n,device=features.device).unsqueeze(-1))&allowed
    mass=(probability*self_edge.unsqueeze(-1)).sum(1)
    self_term=(features.reshape(n,heads,dim)*mass.unsqueeze(-1)).reshape(n,channels)
    nonself_formula=(probability.masked_fill(self_edge.unsqueeze(-1),0).unsqueeze(-1)*gathered).sum(1).reshape(n,channels)
    original=ordinary
    if bool(graph["fallback"].any()):
        groups=graph["group_ids"].to(features.device)
        count=torch.bincount(groups).to(features.dtype).unsqueeze(-1)
        means=features.new_zeros(len(count),channels).index_add(0,groups,features)/count
        alternative=means[groups]
        tied=graph["fallback"].to(features.device)
        original=torch.where(tied.unsqueeze(-1),alternative,ordinary)
        tied_mass=(1/count[groups]).expand(-1,heads)
        mass=torch.where(tied.unsqueeze(-1),tied_mass,mass)
        self_term=torch.where(tied.unsqueeze(-1),features/count[groups],self_term)
        nonself_formula=torch.where(tied.unsqueeze(-1),alternative-features/count[groups],nonself_formula)
    # Retain the native summation's rounding residual in every intervention.
    nonself=original-self_term
    return {"original":original,"self":self_term,"nonself":nonself,"self_mass":mass,
        "nonself_formula":nonself_formula,"formula_max_error":(nonself-nonself_formula).abs().max()}


def permute_nonself(nonself, coordinates, leaves, heads=8, identity=False):
    n,channels=nonself.shape
    dim=channels//heads
    values=nonself.reshape(n,heads,dim)
    coordinates=np.asarray(coordinates,dtype=np.float64)
    leaves=np.asarray(leaves,dtype=np.int64)
    assert coordinates.shape==(n,3) and len(leaves)==n
    norms=values.norm(dim=-1)
    precise_norms=values.double().norm(dim=-1)
    if identity:
        return nonself,{"identity":True,"changed_rows":0,"norm_max_error":0.0,"true_norm_max_error":0.0,"zero_donor_preserved":0,"coordinate_tie_groups":0}
    output=values.clone()
    zero_donor=0;tie_groups=0;eligible_groups=0
    for leaf in np.unique(leaves):
        members=np.flatnonzero(leaves==leaf)
        for head in range(heads):
            eligible=members[(norms[members,head]>0).detach().cpu().numpy()]
            if len(eligible)<2:continue
            eligible_groups+=1
            order=np.lexsort((coordinates[eligible,2],coordinates[eligible,1],coordinates[eligible,0]))
            ordered=eligible[order]
            exact_tie=bool(np.any(np.all(coordinates[ordered][1:]==coordinates[ordered][:-1],axis=-1)))
            index=torch.as_tensor(ordered,device=nonself.device)
            if exact_tie:
                donor=values[index,head].mean(0).expand(len(index),-1)
                tie_groups+=1
            else:
                donor=values[index.roll(1),head]
            donor_norm=donor.norm(dim=-1)
            precise_donor=donor.double().norm(dim=-1)
            safe=torch.where(donor_norm>0,precise_donor,torch.ones_like(precise_donor))
            replacement=(donor.double()*(precise_norms[index,head]/safe).unsqueeze(-1)).to(values.dtype)
            keep=donor_norm==0
            zero_donor+=int(keep.sum())
            output[index,head]=torch.where(keep.unsqueeze(-1),values[index,head],replacement)
    error=float((output.norm(dim=-1)-norms).abs().max().detach().cpu())
    true_error=float((output.double().norm(dim=-1)-precise_norms).abs().max().detach().cpu())
    changed=(output-values).abs().amax(dim=(1,2))>0
    return output.reshape(n,channels),{"identity":False,"changed_rows":int(changed.sum()),"norm_max_error":error,"true_norm_max_error":true_error,
        "zero_donor_preserved":zero_donor,"coordinate_tie_groups":tie_groups,"eligible_leaf_head_groups":eligible_groups,
        "norm_matching":"per-head recipient nonself norm;self term unchanged","new_parameters":0}


def intervention(parts, coordinates, leaves, heads=8, identity=False):
    replacement,receipt=permute_nonself(parts["nonself"],coordinates,leaves,heads,identity)
    result=parts["original"]+(replacement-parts["nonself"])
    receipt["self_term_modified"]=False
    receipt["native_rounding_residual_retained"]=True
    return result,receipt


def padded_intervention(features,padding,positions,fine_ids,build_graph,heads=8,k=32,identity=False):
    original=torch.zeros_like(features)
    altered=torch.zeros_like(features)
    receipts=[]
    for b,ids in enumerate(fine_ids):
        n=len(ids)
        assert int((~padding[b]).sum())==n
        coordinates=positions[b,:n].detach().cpu().numpy()
        leaves=ids.detach().cpu().numpy()
        graph=build_graph(coordinates,leaves,k)
        parts=decompose(features[b,:n],graph,heads)
        value,receipt=intervention(parts,coordinates,leaves,heads,identity)
        original[b,:n]=parts["original"]
        altered[b,:n]=value
        receipt.update(valid_points=n,self_mass_mean=float(parts["self_mass"].mean().detach().cpu()),
            self_mass_min=float(parts["self_mass"].min().detach().cpu()),self_mass_max=float(parts["self_mass"].max().detach().cpu()),
            formula_max_error=float(parts["formula_max_error"].detach().cpu()))
        receipts.append(receipt)
    return original.masked_fill(padding.unsqueeze(-1),0),altered.masked_fill(padding.unsqueeze(-1),0),receipts
