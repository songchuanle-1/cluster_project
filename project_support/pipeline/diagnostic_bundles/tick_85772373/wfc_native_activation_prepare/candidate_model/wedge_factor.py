"""M226 WFC: one nonlinear factor per true original-tree neighbor-pair wedge."""
import torch
import torch.nn as nn


def build_wedge_factor_plan(point_ids,fine_to_middle,middle_to_coarse,bank_sizes):
    if len(bank_sizes)!=3 or any(type(k) is not int or k<0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    def ids(values,limit):
        values=list(values)
        if any(type(i) is not int or i<0 or i>=limit for i in values):
            raise ValueError('Integer original hierarchy IDs in range required')
        return values
    k0,k1,k2=bank_sizes
    points=ids(point_ids,k0);fm=ids(fine_to_middle,k1);mc=ids(middle_to_coarse,k2)
    if len(fm)>k0 or len(mc)>k1:raise ValueError('Membership exceeds original child bank')
    fine=sorted(set(points))
    if any(i>=len(fm) for i in fine):raise ValueError('Supported fine row lacks original parent')
    middle=sorted({fm[i] for i in fine})
    if any(j>=len(mc) for j in middle):raise ValueError('Supported middle row lacks original parent')
    coarse=sorted({mc[j] for j in middle})
    keys=[(level,i) for level,values in enumerate((fine,middle,coarse)) for i in values]
    position={key:i for i,key in enumerate(keys)};neighbors=[[] for _ in keys]
    edges=([(position[(0,i)],position[(1,fm[i])]) for i in fine]+
           [(position[(1,j)],position[(2,mc[j])]) for j in middle])
    for child,parent in edges:neighbors[child].append(parent);neighbors[parent].append(child)
    for row in neighbors:row.sort()
    wedges=[];incidence=[[] for _ in keys]
    for center,adjacent in enumerate(neighbors):
        for left in range(len(adjacent)):
            for right in range(left+1,len(adjacent)):
                triple=(adjacent[left],center,adjacent[right]);factor=len(wedges);wedges.append(triple)
                for node in triple:incidence[node].append(factor)
    return {'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':keys,'neighbors':neighbors,
            'edges':edges,'wedges':wedges,'incidence':incidence,'factor_count':len(wedges),'point_count':len(points)}


def prepare_wedge_factor_plans(levels,cluster_ids_list):
    if len(levels)!=3 or len(cluster_ids_list)!=3 or any(x.ndim!=3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch=int(levels[0].shape[0]);channels=int(levels[0].shape[2]);widths=[int(x.shape[1]) for x in levels]
    if any(int(x.shape[0])!=batch or int(x.shape[2])!=channels or x.device!=levels[0].device or x.dtype!=levels[0].dtype for x in levels):
        raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(values)!=batch for values in cluster_ids_list):raise ValueError('Membership batch mismatch')
    return [build_wedge_factor_plan(*(values[b].detach().cpu().tolist() for values in cluster_ids_list),widths)
            for b in range(batch)]


def mean_wedge_incidence(factors,plans):
    """One weight per incident real wedge, no point-count or learned pooling weights."""
    sources=[];receivers=[];counts=[];factor_offset=0;node_offset=0
    for plan in plans:
        for node,incident in enumerate(plan['incidence']):
            sources.extend(factor_offset+i for i in incident)
            receivers.extend([node_offset+node]*len(incident));counts.append(len(incident))
        factor_offset+=plan['factor_count'];node_offset+=len(plan['node_keys'])
    source=torch.tensor(sources,device=factors.device,dtype=torch.long)
    receiver=torch.tensor(receivers,device=factors.device,dtype=torch.long)
    gathered=factors.index_select(0,source)
    summed=factors.new_zeros((node_offset,int(factors.shape[1]))).index_add(0,receiver,gathered)
    return summed/factors.new_tensor(counts).unsqueeze(-1)


class WedgeFactorComposition(nn.Module):
    def __init__(self,channels):
        super().__init__()
        if type(channels) is not int or channels<=0:raise ValueError('Positive integer channels required')
        self.channels=channels
        self.factor_map=nn.Linear(2*channels,channels)
        self.activation=nn.GELU()

    def forward(self,normalized,cluster_ids_list):
        plans=prepare_wedge_factor_plans(normalized,cluster_ids_list)
        if any(int(x.shape[2])!=self.channels for x in normalized):raise ValueError('WFC channels changed')
        batch=int(normalized[0].shape[0]);widths=[int(x.shape[1]) for x in normalized];c=self.channels
        flat=[x.reshape(batch*widths[level],c) for level,x in enumerate(normalized)]
        output=[x.new_zeros(x.shape) for x in flat]
        rows=[];left=[];centers=[];right=[];positions=[[],[],[]];destinations=[[],[],[]]
        for b,plan in enumerate(plans):
            offset=len(rows)
            for node,(level,original_id) in enumerate(plan['node_keys']):
                positions[level].append(offset+node);destinations[level].append(b*widths[level]+original_id)
                rows.append(flat[level][b*widths[level]+original_id])
            for a,m,z in plan['wedges']:left.append(offset+a);centers.append(offset+m);right.append(offset+z)
        if not centers:return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
        nodes=torch.stack(rows,dim=0);device=normalized[0].device
        li=torch.tensor(left,device=device,dtype=torch.long);mi=torch.tensor(centers,device=device,dtype=torch.long);ri=torch.tensor(right,device=device,dtype=torch.long)
        center=nodes.index_select(0,mi);endpoints=nodes.index_select(0,li)+nodes.index_select(0,ri)
        factors=self.activation(self.factor_map(torch.cat([center,endpoints],dim=-1)))
        delta=mean_wedge_incidence(factors,plans)
        for level in range(3):
            if destinations[level]:
                index=torch.tensor(destinations[level],device=device,dtype=torch.long)
                source=torch.tensor(positions[level],device=device,dtype=torch.long)
                output[level]=output[level].index_copy(0,index,delta.index_select(0,source))
        return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
