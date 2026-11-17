"""M228 NEC: persistent true-node and true-edge feature-state composition."""
import torch
import torch.nn as nn


def build_node_edge_plan(point_ids,fine_to_middle,middle_to_coarse,bank_sizes):
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
    position={key:i for i,key in enumerate(keys)}
    edges=([(position[(0,i)],position[(1,fm[i])]) for i in fine]+
           [(position[(1,j)],position[(2,mc[j])]) for j in middle])
    incident=[[] for _ in keys];neighbors=[[] for _ in keys]
    for edge,(a,b) in enumerate(edges):
        incident[a].append(edge);incident[b].append(edge);neighbors[a].append(b);neighbors[b].append(a)
    for row in neighbors:row.sort()
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
        components.append({'root_id':root,'nodes':sorted(first),
            'edges':sorted({edge for node in first for edge in incident[node]}),'diameter':diameter})
    return {'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'node_keys':keys,
            'edges':edges,'incident':incident,'neighbors':neighbors,'components':components,'point_count':len(points)}


def prepare_node_edge_plans(levels,cluster_ids_list):
    if len(levels)!=3 or len(cluster_ids_list)!=3 or any(x.ndim!=3 for x in levels):
        raise ValueError('Original three rank-three banks and memberships required')
    batch=int(levels[0].shape[0]);channels=int(levels[0].shape[2]);widths=[int(x.shape[1]) for x in levels]
    if any(int(x.shape[0])!=batch or int(x.shape[2])!=channels or x.device!=levels[0].device or x.dtype!=levels[0].dtype for x in levels):
        raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(values)!=batch for values in cluster_ids_list):raise ValueError('Membership batch mismatch')
    return [build_node_edge_plan(*(values[b].detach().cpu().tolist() for values in cluster_ids_list),widths)
            for b in range(batch)]


def build_node_edge_rounds(plans):
    components=[];node_offset=edge_offset=0
    for plan in plans:
        components.extend((node_offset,edge_offset,component,plan) for component in plan['components'])
        node_offset+=len(plan['node_keys']);edge_offset+=len(plan['edges'])
    rounds=[]
    for r in range(max((c['diameter'] for _,_,c,_ in components),default=0)):
        edges=[];left=[];right=[];nodes=[];sources=[];receivers=[];counts=[]
        for no,eo,component,plan in components:
            if r>=component['diameter']:continue
            for edge in component['edges']:
                a,b=plan['edges'][edge];edges.append(eo+edge);left.append(no+a);right.append(no+b)
            for node in component['nodes']:
                row=len(nodes);nodes.append(no+node);counts.append(len(plan['incident'][node]))
                sources.extend(eo+edge for edge in plan['incident'][node]);receivers.extend([row]*len(plan['incident'][node]))
        rounds.append({'round_index':r,'edge_receivers':edges,'left_nodes':left,'right_nodes':right,
            'node_receivers':nodes,'incident_sources':sources,'incident_receivers':receivers,'node_counts':counts})
    return rounds


def mean_endpoint_nodes(old_nodes,round_plan):
    left=torch.tensor(round_plan['left_nodes'],device=old_nodes.device,dtype=torch.long)
    right=torch.tensor(round_plan['right_nodes'],device=old_nodes.device,dtype=torch.long)
    summed=old_nodes.index_select(0,left)+old_nodes.index_select(0,right)
    return summed/old_nodes.new_tensor([2]*len(round_plan['edge_receivers'])).unsqueeze(-1)


def mean_incident_edges(new_edges,round_plan):
    source=torch.tensor(round_plan['incident_sources'],device=new_edges.device,dtype=torch.long)
    receiver=torch.tensor(round_plan['incident_receivers'],device=new_edges.device,dtype=torch.long)
    gathered=new_edges.index_select(0,source)
    summed=new_edges.new_zeros((len(round_plan['node_receivers']),int(new_edges.shape[1]))).index_add(0,receiver,gathered)
    return summed/new_edges.new_tensor(round_plan['node_counts']).unsqueeze(-1)


class NodeEdgeComposition(nn.Module):
    def __init__(self,channels):
        super().__init__()
        if type(channels) is not int or channels<=0:raise ValueError('Positive integer channels required')
        self.channels=channels
        self.edge_cell=nn.Linear(2*channels,channels)
        self.node_cell=nn.Linear(2*channels,channels)
        self.activation=nn.GELU()

    def forward(self,normalized,cluster_ids_list):
        plans=prepare_node_edge_plans(normalized,cluster_ids_list)
        if any(int(x.shape[2])!=self.channels for x in normalized):raise ValueError('NEC channels changed')
        batch=int(normalized[0].shape[0]);widths=[int(x.shape[1]) for x in normalized];c=self.channels
        flat=[x.reshape(batch*widths[level],c) for level,x in enumerate(normalized)]
        output=[x.new_zeros(x.shape) for x in flat]
        rows=[];destinations=[[],[],[]];positions=[[],[],[]]
        for b,plan in enumerate(plans):
            for level,original_id in plan['node_keys']:
                positions[level].append(len(rows));destinations[level].append(b*widths[level]+original_id)
                rows.append(flat[level][b*widths[level]+original_id])
        if not rows:return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
        node_state=torch.stack(rows,dim=0)
        edge_state=node_state.new_zeros((sum(len(plan['edges']) for plan in plans),c))
        for round_plan in build_node_edge_rounds(plans):
            edge_index=torch.tensor(round_plan['edge_receivers'],device=normalized[0].device,dtype=torch.long)
            old_edges=edge_state.index_select(0,edge_index)
            endpoint_mean=mean_endpoint_nodes(node_state,round_plan)
            next_edges=self.activation(self.edge_cell(torch.cat([old_edges,endpoint_mean],dim=-1)))
            edge_state=edge_state.index_copy(0,edge_index,next_edges)
            node_index=torch.tensor(round_plan['node_receivers'],device=normalized[0].device,dtype=torch.long)
            old_nodes=node_state.index_select(0,node_index)
            incident_mean=mean_incident_edges(edge_state,round_plan)
            next_nodes=self.activation(self.node_cell(torch.cat([old_nodes,incident_mean],dim=-1)))
            node_state=node_state.index_copy(0,node_index,next_nodes)
        for level in range(3):
            if destinations[level]:
                index=torch.tensor(destinations[level],device=normalized[0].device,dtype=torch.long)
                source=torch.tensor(positions[level],device=normalized[0].device,dtype=torch.long)
                output[level]=output[level].index_copy(0,index,node_state.index_select(0,source))
        return [x.reshape(normalized[level].shape) for level,x in enumerate(output)]
