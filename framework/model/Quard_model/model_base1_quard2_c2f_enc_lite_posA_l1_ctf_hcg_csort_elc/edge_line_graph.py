"""M225 ELC: persistent undirected original-edge states on the line graph."""
import torch
import torch.nn as nn


def build_edge_line_graph_plan(point_ids,fine_to_middle,middle_to_coarse,bank_sizes):
    if len(bank_sizes)!=3 or any(type(k) is not int or k<0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    def ids(values,limit):
        values=list(values)
        if any(type(i) is not int or i<0 or i>=limit for i in values):
            raise ValueError('Integer original hierarchy IDs in range required')
        return values
    k0,k1,k2=bank_sizes
    points=ids(point_ids,k0);f2m=ids(fine_to_middle,k1);m2c=ids(middle_to_coarse,k2)
    if len(f2m)>k0 or len(m2c)>k1:raise ValueError('Membership exceeds original child bank')
    fine=sorted(set(points))
    if any(i>=len(f2m) for i in fine):raise ValueError('Supported fine row lacks original parent')
    middle=sorted({f2m[i] for i in fine})
    if any(j>=len(m2c) for j in middle):raise ValueError('Supported middle row lacks original parent')
    coarse=sorted({m2c[j] for j in middle})
    node_keys=[(level,i) for level,values in enumerate((fine,middle,coarse)) for i in values]
    position={key:i for i,key in enumerate(node_keys)}
    edges=([(position[(0,i)],position[(1,f2m[i])]) for i in fine]+
           [(position[(1,j)],position[(2,m2c[j])]) for j in middle])
    incident=[[] for _ in node_keys];neighbors=[[] for _ in node_keys]
    for e,(child,parent) in enumerate(edges):
        incident[child].append(e);incident[parent].append(e)
        neighbors[child].append(parent);neighbors[parent].append(child)
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
        diameter=max(distances(farthest).values())
        edge_ids=sorted({e for node in first for e in incident[node]})
        components.append({'root_id':root,'nodes':sorted(first),'edges':edge_ids,
                           'tree_diameter':diameter,'line_diameter':diameter-1})
    return {'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':node_keys,
            'edges':edges,'incident':incident,'components':components,'point_count':len(points)}


def prepare_edge_line_graph_plans(levels,cluster_ids_list):
    if len(levels)!=3 or len(cluster_ids_list)!=3 or any(x.ndim!=3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch=int(levels[0].shape[0]);channels=int(levels[0].shape[2]);widths=[int(x.shape[1]) for x in levels]
    if any(int(x.shape[0])!=batch or int(x.shape[2])!=channels or x.device!=levels[0].device or x.dtype!=levels[0].dtype for x in levels):
        raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(values)!=batch for values in cluster_ids_list):raise ValueError('Membership batch mismatch')
    return [build_edge_line_graph_plan(*(values[b].detach().cpu().tolist() for values in cluster_ids_list),widths)
            for b in range(batch)]


def build_edge_rounds(plans):
    components=[];offset=0
    for plan in plans:
        for component in plan['components']:components.append((offset,component,plan['incident'],plan['edges']))
        offset+=len(plan['edges'])
    rounds=[]
    for r in range(max((component['line_diameter'] for _,component,_,_ in components),default=0)):
        receivers=[];counts=[];groups=[]
        for offset,component,incident,edges in components:
            if r>=component['line_diameter']:continue
            for e in component['edges']:
                a,b=edges[e];receivers.append(offset+e);counts.append(len(incident[a])+len(incident[b])-2)
            groups.extend([offset+e for e in incident[node]] for node in component['nodes'])
        rows={e:i for i,e in enumerate(receivers)};buckets={}
        for group in groups:
            bucket=buckets.setdefault(len(group),{'degree':len(group),'edges':[],'receiver_rows':[]})
            bucket['edges'].extend(group);bucket['receiver_rows'].extend(rows[e] for e in group)
        rounds.append({'receivers':receivers,'counts':counts,'endpoint_buckets':[buckets[k] for k in sorted(buckets)]})
    return rounds


def mean_adjacent_edge_states(old_state,round_plan):
    """OTHER incident edges, one weight per edge; no own edge in either exclusive sum."""
    c=int(old_state.shape[1]);device=old_state.device
    summed=old_state.new_zeros((len(round_plan['receivers']),c))
    for bucket in round_plan['endpoint_buckets']:
        degree=bucket['degree']
        index=torch.tensor(bucket['edges'],device=device,dtype=torch.long)
        values=old_state.index_select(0,index).reshape(-1,degree,c)
        prefix=values.cumsum(dim=1)
        suffix=values.flip((1,)).cumsum(dim=1).flip((1,))
        zero=values.new_zeros((int(values.shape[0]),1,c))
        exclusive=torch.cat([zero,prefix[:,:-1]],dim=1)+torch.cat([suffix[:,1:],zero],dim=1)
        rows=torch.tensor(bucket['receiver_rows'],device=device,dtype=torch.long)
        summed=summed.index_add(0,rows,exclusive.reshape(-1,c))
    return summed/old_state.new_tensor(round_plan['counts']).unsqueeze(-1)


def incident_node_means(edge_state,plans):
    """Final equal incident-edge means; unsupported bank rows are scattered as zero outside."""
    sources=[];receivers=[];counts=[];edge_offset=0;node_offset=0
    for plan in plans:
        for node,incident in enumerate(plan['incident']):
            sources.extend(edge_offset+e for e in incident)
            receivers.extend([node_offset+node]*len(incident));counts.append(len(incident))
        edge_offset+=len(plan['edges']);node_offset+=len(plan['node_keys'])
    source=torch.tensor(sources,device=edge_state.device,dtype=torch.long)
    receiver=torch.tensor(receivers,device=edge_state.device,dtype=torch.long)
    gathered=edge_state.index_select(0,source)
    summed=edge_state.new_zeros((node_offset,int(edge_state.shape[1]))).index_add(0,receiver,gathered)
    return summed/edge_state.new_tensor(counts).unsqueeze(-1)


class EdgeLineGraphComposition(nn.Module):
    def __init__(self,channels):
        super().__init__()
        if type(channels) is not int or channels<=0:raise ValueError('Positive integer channels required')
        self.channels=channels
        self.initialize=nn.Linear(2*channels,channels)
        self.cell=nn.Linear(2*channels,channels)
        self.activation=nn.GELU()

    def forward(self,normalized,cluster_ids_list):
        plans=prepare_edge_line_graph_plans(normalized,cluster_ids_list)
        if any(int(x.shape[2])!=self.channels for x in normalized):raise ValueError('ELC channels changed')
        batch=int(normalized[0].shape[0]);widths=[int(x.shape[1]) for x in normalized];c=self.channels
        flat=[x.reshape(batch*widths[level],c) for level,x in enumerate(normalized)]
        output=[x.new_zeros(x.shape) for x in flat]
        children=[];parents=[];destinations=[[],[],[]];positions=[[],[],[]];node_offset=0
        for b,plan in enumerate(plans):
            for child,parent in plan['edges']:
                cl,ci=plan['node_keys'][child];pl,pi=plan['node_keys'][parent]
                children.append(flat[cl][b*widths[cl]+ci]);parents.append(flat[pl][b*widths[pl]+pi])
            for node,(level,original_id) in enumerate(plan['node_keys']):
                positions[level].append(node_offset+node);destinations[level].append(b*widths[level]+original_id)
            node_offset+=len(plan['node_keys'])
        if not children:return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
        state=self.activation(self.initialize(torch.cat([torch.stack(children,dim=0),torch.stack(parents,dim=0)],dim=-1)))
        for round_plan in build_edge_rounds(plans):
            index=torch.tensor(round_plan['receivers'],device=normalized[0].device,dtype=torch.long)
            own=state.index_select(0,index)
            neighbor=mean_adjacent_edge_states(state,round_plan)
            updated=self.activation(self.cell(torch.cat([own,neighbor],dim=-1)))
            state=state.index_copy(0,index,updated)
        node_state=incident_node_means(state,plans)
        for level in range(3):
            if destinations[level]:
                index=torch.tensor(destinations[level],device=normalized[0].device,dtype=torch.long)
                source=torch.tensor(positions[level],device=normalized[0].device,dtype=torch.long)
                output[level]=output[level].index_copy(0,index,node_state.index_select(0,source))
        return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
