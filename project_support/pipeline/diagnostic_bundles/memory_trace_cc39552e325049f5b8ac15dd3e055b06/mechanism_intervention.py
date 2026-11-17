def intervention(self,point_feats,banks,cluster_ids_list,point_mask):
    global branch_calls
    branch_calls+=1
    if condition=='canonical':
        return original_readout(point_feats,banks,cluster_ids_list,point_mask)
    weights=self.level_gate(torch.cat([point_feats,point_feats.mean(1,keepdim=True).expand_as(point_feats)],-1)).softmax(-1)
    fused=torch.zeros_like(point_feats)
    for b in range(point_feats.shape[0]):
        leaf=cluster_ids_list[0][b].long()
        parent1=cluster_ids_list[1][b].long()
        parent2=cluster_ids_list[2][b].long()
        count=len(leaf)
        query=point_feats[b,:count].reshape(count,8,32).transpose(0,1)
        allowed=CONTROL_CORE['support_masks'](leaf,parent1,parent2,[bank.shape[1] for bank in banks])
        if condition=='ancestor':
            ancestors=(leaf,parent1[leaf],parent2[parent1[leaf]])
            allowed=tuple(torch.arange(bank.shape[1],device=leaf.device)[None,:]==ancestor[:,None] for bank,ancestor in zip(banks,ancestors))
        for level,(bank,mask) in enumerate(zip(banks,allowed)):
            key=bank[b].reshape(-1,8,32).transpose(0,1)
            scores=(query@key.transpose(-1,-2))/math.sqrt(32)
            if condition=='uniform':scores=torch.zeros_like(scores)
            nonempty=mask.any(-1)
            scores=scores.masked_fill(~mask.unsqueeze(0),-torch.inf)
            scores=torch.where(nonempty[None,:,None],scores,torch.zeros_like(scores))
            probability=scores.softmax(-1)*mask.unsqueeze(0)
            message=(probability@key).transpose(0,1).reshape(count,256)
            fused[b,:count]+=message*weights[b,:count,level:level+1]
    return self.point_out_proj(self.dropout(fused)).masked_fill(point_mask.unsqueeze(-1),0)

def describe_support(pair,ids):
    rows=[]
    for expression,point_ids in enumerate(ids[0]):
        point_ids=point_ids.detach().cpu().long()
        parent1=ids[1][expression].detach().cpu().long()
        parent2=ids[2][expression].detach().cpu().long()
        leaves=point_ids.unique(sorted=True)
        mids=parent1[leaves]
        tops=parent2[mids]
        missed=duplicate=0.0
        for leaf in leaves:
            middle=parent1[leaf]
            coarse=parent2[middle]
            multiplicity=(leaves==leaf).long()+(mids==middle).long()+(tops==coarse).long()
            weight=float((point_ids==leaf).sum())/len(point_ids)
            missed+=weight*float((multiplicity==0).float().mean())
            duplicate+=weight*float((multiplicity>1).float().mean())
            cut=(mids==middle).long()+((tops==coarse)&(mids!=middle)).long()+(tops!=coarse).long()
            assert torch.all(cut==1)
        rows.append({'pair':pair,'expression':expression,'valid_point_rows':len(point_ids),
            'valid_fine_tokens':len(leaves),'ancestor_missed_leaf_fraction':missed,
            'ancestor_multiply_covered_leaf_fraction':duplicate,'disjoint_exact_cover':True,
            'scope':'Point-weighted branch value-support coverage over valid fine tokens; not all-model context or semantic object coverage.'})
    return rows
