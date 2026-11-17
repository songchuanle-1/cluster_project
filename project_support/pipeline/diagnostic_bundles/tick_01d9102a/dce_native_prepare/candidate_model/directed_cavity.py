"""M220 directed recipient-cavity composition on original support forest."""
import torch
import torch.nn as nn

def build_cavity_plan(point_ids, fine_to_middle, middle_to_coarse, bank_sizes):
    if len(bank_sizes)!=3 or any(type(k) is not int or k<0 for k in bank_sizes):
        raise ValueError('Three nonnegative original bank widths required')
    k0,k1,k2=bank_sizes
    def ids(values,limit):
        values=list(values)
        if any(type(i) is not int or i<0 or i>=limit for i in values):raise ValueError('Invalid original IDs')
        return values
    points=ids(point_ids,k0);f2m=ids(fine_to_middle,k1);m2c=ids(middle_to_coarse,k2)
    if len(f2m)>k0 or len(m2c)>k1:raise ValueError('Membership exceeds original bank')
    fine=sorted(set(points))
    if any(i>=len(f2m) for i in fine):raise ValueError('Supported fine row lacks parent')
    middle=sorted({f2m[i] for i in fine})
    if any(j>=len(m2c) for j in middle):raise ValueError('Supported middle row lacks parent')
    coarse=sorted({m2c[j] for j in middle});mp={j:i for i,j in enumerate(middle)};cp={k:i for i,k in enumerate(coarse)}
    fm=[mp[f2m[i]] for i in fine];mc=[cp[m2c[j]] for j in middle]
    fg=[[] for _ in middle];mg=[[] for _ in coarse]
    for i,j in enumerate(fm):fg[j].append(i)
    for j,k in enumerate(mc):mg[k].append(j)
    return {'fine_ids':fine,'middle_ids':middle,'coarse_ids':coarse,'fine_parent_positions':fm,'middle_parent_positions':mc,
            'fine_groups':fg,'middle_groups':mg,'fine_counts':[len(g) for g in fg],'middle_counts':[len(g) for g in mg],'point_count':len(points)}

def prepare_cavity_plans(levels, cluster_ids_list):
    if len(levels)!=3 or len(cluster_ids_list)!=3:raise ValueError('Original three banks/ID lists required')
    batch=int(levels[0].shape[0]);channels=int(levels[0].shape[2]);widths=[int(x.shape[1]) for x in levels]
    if any(x.ndim!=3 or int(x.shape[0])!=batch or int(x.shape[2])!=channels or x.device!=levels[0].device or x.dtype!=levels[0].dtype for x in levels):raise ValueError('Bank shape/device/dtype mismatch')
    if any(len(ids)!=batch for ids in cluster_ids_list):raise ValueError('Membership batch mismatch')
    return [build_cavity_plan(*(ids[b].detach().cpu().tolist() for ids in cluster_ids_list),widths) for b in range(batch)]

def mean_by_parent(messages, parent_positions, counts):
    index=torch.tensor(parent_positions,device=messages.device,dtype=torch.long)
    summed=messages.new_zeros((len(counts),messages.shape[1])).index_add(0,index,messages)
    return summed/messages.new_tensor(counts).unsqueeze(-1)

def exclusive_group_sums(messages, groups):
    """Each output uses only before/after rows; no total-minus-own cancellation."""
    output=messages.new_zeros(messages.shape)
    for group in groups:
        index=torch.tensor(group,device=messages.device,dtype=torch.long)
        values=messages.index_select(0,index);zero=values.new_zeros((1,values.shape[1]))
        prefix=torch.cat([zero,torch.cumsum(values,dim=0)[:-1]],dim=0)
        suffix=torch.cat([torch.cumsum(values.flip([0]),dim=0)[:-1].flip([0]),zero],dim=0)
        output=output.index_copy(0,index,prefix+suffix)
    return output

class DirectedCavityComposition(nn.Module):
    def __init__(self,channels):
        super().__init__();self.channels=channels
        self.up=nn.Linear(2*channels,channels)
        self.down_root=nn.Linear(2*channels,channels)
        self.down_middle=nn.Linear(2*channels,channels)
        self.read_fine=nn.Linear(2*channels,channels)
        self.read_middle=nn.Linear(2*channels,channels)
        self.read_coarse=nn.Linear(2*channels,channels)
        self.activation=nn.GELU()
    def forward(self,normalized,cluster_ids_list):
        plans=prepare_cavity_plans(normalized,cluster_ids_list)
        if any(int(x.shape[2])!=self.channels for x in normalized):raise ValueError('Channels changed')
        batch=int(normalized[0].shape[0]);widths=[int(x.shape[1]) for x in normalized];c=self.channels
        flat=[x.reshape(batch*widths[l],c) for l,x in enumerate(normalized)]
        ids=[[],[],[]];fm=[];mc=[];fg=[];mg=[];fc=[];cc=[]
        for b,p in enumerate(plans):
            fo,mo,co=(len(x) for x in ids)
            for l,key in enumerate(('fine_ids','middle_ids','coarse_ids')):ids[l].extend(b*widths[l]+i for i in p[key])
            fm.extend(mo+i for i in p['fine_parent_positions']);mc.extend(co+i for i in p['middle_parent_positions'])
            fg.extend([[fo+i for i in g] for g in p['fine_groups']]);mg.extend([[mo+j for j in g] for g in p['middle_groups']])
            fc.extend(p['fine_counts']);cc.extend(p['middle_counts'])
        delta=[x.new_zeros(x.shape) for x in flat]
        if not ids[0]:return [x.reshape(normalized[l].shape) for l,x in enumerate(delta)]
        device=normalized[0].device
        index=[torch.tensor(x,device=device,dtype=torch.long) for x in ids]
        z=[x.index_select(0,index[l]) for l,x in enumerate(flat)]
        fmp=torch.tensor(fm,device=device,dtype=torch.long);mcp=torch.tensor(mc,device=device,dtype=torch.long)
        fine_mean=mean_by_parent(z[0],fm,fc)
        up=self.activation(self.up(torch.cat([z[1],fine_mean],dim=-1)))
        coarse_mean=mean_by_parent(up,mc,cc)
        other_middle=exclusive_group_sums(up,mg)
        other_count=[cc[k]-1 if cc[k]>1 else 1 for k in mc]
        root_context=other_middle/up.new_tensor(other_count).unsqueeze(-1)
        down_root=self.activation(self.down_root(torch.cat([z[2].index_select(0,mcp),root_context],dim=-1)))
        other_fine=exclusive_group_sums(z[0],fg)
        fine_context=(other_fine+down_root.index_select(0,fmp))/z[0].new_tensor([fc[j] for j in fm]).unsqueeze(-1)
        down_middle=self.activation(self.down_middle(torch.cat([z[1].index_select(0,fmp),fine_context],dim=-1)))
        # Middle incoming neighbors are each fine child plus its one parent, equally weighted.
        middle_context=(fine_mean*z[1].new_tensor(fc).unsqueeze(-1)+down_root)/z[1].new_tensor([n+1 for n in fc]).unsqueeze(-1)
        refined=[self.activation(self.read_fine(torch.cat([z[0],down_middle],dim=-1))),
                 self.activation(self.read_middle(torch.cat([z[1],middle_context],dim=-1))),
                 self.activation(self.read_coarse(torch.cat([z[2],coarse_mean],dim=-1)))]
        return [delta[l].index_copy(0,index[l],refined[l]).reshape(normalized[l].shape) for l in range(3)]
