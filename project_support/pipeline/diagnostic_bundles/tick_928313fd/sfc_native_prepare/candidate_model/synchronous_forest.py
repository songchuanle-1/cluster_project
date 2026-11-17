"""M224 SFC: synchronous full-neighbor states on the original support forest."""
import torch
import torch.nn as nn


def build_synchronous_forest_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    """Only true original nodes/edges; genuine tree diameter fixes component rounds."""
    if len(bank_sizes) != 3 or any(type(k) is not int or k < 0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    def ids(values, limit):
        values = list(values)
        if any(type(i) is not int or i < 0 or i >= limit for i in values):
            raise ValueError('Integer original hierarchy IDs in range required')
        return values
    k0,k1,k2 = bank_sizes
    points = ids(point_ids,k0);f2m = ids(fine_to_middle,k1);m2c = ids(middle_to_coarse,k2)
    if len(f2m)>k0 or len(m2c)>k1:
        raise ValueError('Membership exceeds original child bank')
    fine=sorted(set(points))
    if any(i>=len(f2m) for i in fine):raise ValueError('Supported fine row lacks original parent')
    middle=sorted({f2m[i] for i in fine})
    if any(j>=len(m2c) for j in middle):raise ValueError('Supported middle row lacks original parent')
    coarse=sorted({m2c[j] for j in middle})
    node_keys=[(level,i) for level,values in enumerate((fine,middle,coarse)) for i in values]
    position={key:i for i,key in enumerate(node_keys)}
    neighbors=[[] for _ in node_keys]
    for child,parent in ([(position[(0,i)],position[(1,f2m[i])]) for i in fine]+
                         [(position[(1,j)],position[(2,m2c[j])]) for j in middle]):
        neighbors[child].append(parent);neighbors[parent].append(child)
    for values in neighbors:values.sort()
    def distances(start):
        found={start:0};queue=[start]
        for node in queue:
            for other in neighbors[node]:
                if other not in found:found[other]=found[node]+1;queue.append(other)
        return found
    components=[]
    for root in coarse:
        first=distances(position[(2,root)])
        farthest=max(first,key=lambda node:(first[node],-node))
        second=distances(farthest)
        components.append({'root_id':root,'nodes':sorted(first),'diameter':max(second.values()),
                           'edge_count':sum(len(neighbors[i]) for i in first)//2})
    return {'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':node_keys,
            'neighbors':neighbors,'components':components,'edge_count':len(fine)+len(middle),
            'point_count':len(points)}


def prepare_synchronous_forest_plans(levels, cluster_ids_list):
    if len(levels)!=3 or len(cluster_ids_list)!=3 or any(x.ndim!=3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch=int(levels[0].shape[0]);channels=int(levels[0].shape[2]);widths=[int(x.shape[1]) for x in levels]
    if any(int(x.shape[0])!=batch or int(x.shape[2])!=channels or x.device!=levels[0].device or x.dtype!=levels[0].dtype for x in levels):
        raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(values)!=batch for values in cluster_ids_list):raise ValueError('Membership batch mismatch')
    return [build_synchronous_forest_plan(*(values[b].detach().cpu().tolist() for values in cluster_ids_list),widths)
            for b in range(batch)]


def build_synchronous_rounds(plans):
    components=[];offset=0
    for plan in plans:
        for component in plan['components']:
            components.append((offset,component,plan['neighbors']))
        offset+=len(plan['node_keys'])
    rounds=[]
    for r in range(max((component['diameter'] for _,component,_ in components),default=0)):
        receivers=[];sources=[];source_receivers=[];counts=[]
        for offset,component,neighbors in components:
            if r>=component['diameter']:continue
            for node in component['nodes']:
                row=len(receivers);receivers.append(offset+node);counts.append(len(neighbors[node]))
                sources.extend(offset+other for other in neighbors[node])
                source_receivers.extend([row]*len(neighbors[node]))
        rounds.append({'receivers':receivers,'sources':sources,'source_receivers':source_receivers,'counts':counts})
    return rounds


def mean_neighbor_states(old_state, round_plan):
    """All neighbors use the same OLD state, with each real adjacent node equally weighted."""
    device=old_state.device
    sources=torch.tensor(round_plan['sources'],device=device,dtype=torch.long)
    receivers=torch.tensor(round_plan['source_receivers'],device=device,dtype=torch.long)
    gathered=old_state.index_select(0,sources)
    summed=old_state.new_zeros((len(round_plan['receivers']),old_state.shape[1])).index_add(0,receivers,gathered)
    return summed/old_state.new_tensor(round_plan['counts']).unsqueeze(-1)


class SynchronousForestComposition(nn.Module):
    def __init__(self,channels):
        super().__init__()
        if type(channels) is not int or channels<=0:raise ValueError('Positive integer channels required')
        self.channels=channels
        self.cell=nn.Linear(2*channels,channels)
        self.activation=nn.GELU()

    def forward(self,normalized,cluster_ids_list):
        plans=prepare_synchronous_forest_plans(normalized,cluster_ids_list)
        if any(int(x.shape[2])!=self.channels for x in normalized):raise ValueError('SFC channels changed')
        batch=int(normalized[0].shape[0]);widths=[int(x.shape[1]) for x in normalized];c=self.channels
        flat=[x.reshape(batch*widths[level],c) for level,x in enumerate(normalized)]
        output=[x.new_zeros(x.shape) for x in flat]
        states=[];destinations=[[],[],[]];positions=[[],[],[]]
        for b,plan in enumerate(plans):
            for level,original_id in plan['node_keys']:
                positions[level].append(len(states));destinations[level].append(b*widths[level]+original_id)
                states.append(flat[level][b*widths[level]+original_id])
        if not states:return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
        state=torch.stack(states,dim=0)
        for round_plan in build_synchronous_rounds(plans):
            index=torch.tensor(round_plan['receivers'],device=normalized[0].device,dtype=torch.long)
            own=state.index_select(0,index)
            neighbor=mean_neighbor_states(state,round_plan)
            updated=self.activation(self.cell(torch.cat([own,neighbor],dim=-1)))
            # Single functional replacement after EVERY old-state gather/mean/map.
            state=state.index_copy(0,index,updated)
        for level in range(3):
            if destinations[level]:
                index=torch.tensor(destinations[level],device=normalized[0].device,dtype=torch.long)
                source=torch.tensor(positions[level],device=normalized[0].device,dtype=torch.long)
                output[level]=output[level].index_copy(0,index,state.index_select(0,source))
        return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
