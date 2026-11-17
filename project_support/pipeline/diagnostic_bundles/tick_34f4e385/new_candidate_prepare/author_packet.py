"""Private WFC source authoring from frozen bytes only; never reads primary/dirty files."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[3]
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
OLD=FROZEN/'staged_repository/framework/model/Quard_model'/(BASE+'_elc')
DEST=HERE/'staged_repository/framework/model/Quard_model'/(BASE+'_wfc')
ORIGINAL_HIER_SHA='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
HELPER='''"""M226 WFC: one nonlinear factor per true original-tree neighbor-pair wedge."""
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
'''

def restored_original_hier():
    tree=ast.parse((FROZEN/'author_packet.py').read_text(encoding='utf-8'))
    main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
    literals={n.targets[0].id:ast.literal_eval(n.value) for n in main.body if isinstance(n,ast.Assign) and len(n.targets)==1 and isinstance(n.targets[0],ast.Name) and n.targets[0].id in ('old','new','marker','extension')}
    source=(OLD/'hier_postprocess.py').read_text(encoding='utf-8')
    assert source.startswith('from .edge_line_graph import EdgeLineGraphComposition\n')
    source=source.removeprefix('from .edge_line_graph import EdgeLineGraphComposition\n')
    assert source.count(literals['new'])==source.count(literals['marker']+literals['extension'])==1
    source=source.replace(literals['new'],literals['old'],1).replace(literals['marker']+literals['extension'],literals['marker'],1)
    assert hashlib.sha256(source.encode('utf-8')).hexdigest()==ORIGINAL_HIER_SHA
    return source,literals

def main():
    assert not DEST.exists(),'Preserve existing private source bytes'
    assert hashlib.sha256((FROZEN/'preparation.json').read_bytes()).hexdigest()=='c77746ae35e4f3bfbc1c58e62aff629798946bb91dd0befbd08f247ca5dd7dd8'
    frozen=json.loads((FROZEN/'preparation.json').read_text(encoding='utf-8'))
    for name,h in frozen['prepared_file_hashes'].items():assert hashlib.sha256((FROZEN/name).read_bytes()).hexdigest()==h,name
    source,literals=restored_original_hier();DEST.mkdir(parents=True)
    for name in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py'):(DEST/name).write_bytes((OLD/name).read_bytes())
    source='from .wedge_factor import WedgeFactorComposition\n'+source
    changed='''        normalized = [self.cluster_ffn_norm[level](cluster_feats_list[level])
                      for level in range(self.num_scales)]
        delta = self.wedge_factor(normalized, cluster_ids_list)
        refined_cluster_feats = [cf + value for cf, value in zip(cluster_feats_list, delta)]'''
    source=source.replace(literals['old'],changed,1)
    addition='''
        if num_scales != 3:
            raise ValueError('WFC requires the original three hierarchy scales')
        # Original FFN/LN RNG consumption precedes isolated new-map construction.
        with torch.random.fork_rng(devices=[]):
            self.wedge_factor = WedgeFactorComposition(d_model)
        self.cluster_ffn = nn.ModuleList([nn.Identity() for _ in range(num_scales)])'''
    source=source.replace(literals['marker'],literals['marker']+addition,1)
    (DEST/'hier_postprocess.py').write_text(source,encoding='utf-8',newline='\n')
    (DEST/'wedge_factor.py').write_text(HELPER,encoding='utf-8',newline='\n')
    yaml=next((FROZEN/'staged_repository/configs').rglob('*.yaml'))
    assert hashlib.sha256(yaml.read_bytes()).hexdigest()=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
    target=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_wfc'/(BASE+'_wfc.yaml')
    target.parent.mkdir(parents=True);target.write_bytes(yaml.read_bytes())
    print(json.dumps({'private_source_files':len(list(DEST.glob('*.py')))+1,'helper_sha256':hashlib.sha256((DEST/'wedge_factor.py').read_bytes()).hexdigest(),'frozen_M95_hier_recovered_sha256':ORIGINAL_HIER_SHA,'primary_or_dirty_file_read':False}))

if __name__=='__main__':main()
