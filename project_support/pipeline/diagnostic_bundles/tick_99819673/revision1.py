"""Preregister and apply one evidence-bounded feature-reduction revision."""
import ast
from pathlib import Path
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr'


def main():
    c.guard(1500)
    work=c.tick.load(ROOT/'pipeline/research_work.json');candidate=next(x for x in work['candidates'] if x['id']==c.CID)
    assert not candidate.get('revision_history')
    package=ROOT/'Cluster/framework/model/Quard_model'/NAME
    config=ROOT/'Cluster/configs/Quard/ctf_hcg_csort_rstr'/(NAME+'.yaml')
    archive=OUT/'source_r0';archive.mkdir(exist_ok=False)
    for path in package.glob('*.py'):(archive/path.name).write_bytes(path.read_bytes())
    (archive/'candidate.yaml').write_bytes(config.read_bytes())
    failure=[c.evidence(OUT/'validation_h2_controls_candidate_result.json'),c.evidence(OUT/'validation_trace_trace_candidate_result.json')]
    protocol=c.save('revision1_preregistration.json',{'preregistered_at':c.now(),'candidate_id':c.CID,'revision':1,
        'failure_scope':'implementation','failure_evidence':failure,
        'reason':'Reference-input replay already differs at raw bank by1.907e-6, before new token transport; clone is not necessary for this divergence. Partial trace output preserved; final layout serialization failed on bool subtraction, not a completed trace PASS.',
        'change':'Only SharedClusterBank feature mean pooling: fixed-order segment_csr. Fine members ordered by unchanged xyz within fixed leaf; coarser token members by fixed token index. Pass current sp_pos to that feature-only function. Leave shared aggregate_cluster and original geometry/FPS partitioner unchanged. No fusion/attention/precision/threshold/seed change.',
        'prediction':'Repeated identical full-source rawbanks and encoder outputs become deterministic. Row-inverse may still fail due unchanged global fusion mean/LIA; test rather than promise. New path/finite nonzero native gradients must remain.',
        'controls':'Exact unchanged R0 native loss/full-source controls1e-6; original failures immutable. Recheck resources for current code. No training or commit.',
        'source_r0':[c.evidence(x) for x in sorted(archive.iterdir())],
        'literature':'torch_scatter official scatter docs warn atomic GPU reduction nondeterminism; segment_csr docs state fully deterministic. https://pytorch-scatter.readthedocs.io/en/latest/functions/segment_csr.html'})
    candidate['revision_history']=[{'revision':1,'failure_scope':'implementation','reason':c.tick.load(protocol)['reason'],
        'change':c.tick.load(protocol)['change'],'prediction':c.tick.load(protocol)['prediction'],
        'preregistered_at':c.tick.load(protocol)['preregistered_at'],'failure_evidence':failure,'result':'pending','evidence':[c.evidence(protocol)]}]
    candidate['failure_scope']='implementation';candidate['scientific_admission']=False
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    path=package/'hier_postprocess.py';text=path.read_text(encoding='utf-8')
    text=text.replace('import torch\n','import numpy as np\nimport torch\n',1).replace('from torch_scatter import scatter_mean, scatter_max','from torch_scatter import scatter_mean, scatter_max, segment_csr')
    start=text.index('class SharedClusterBank');end=text.index('\nclass C2F_ClusterAttn_Lite',start)
    bank=text[start:end]
    bank=bank.replace('def build_cluster_feats(self, sp_feats, batch_offsets):','def build_cluster_feats(self, sp_feats, batch_offsets, sp_positions=None):')
    bank=bank.replace("mean_feats = aggregate_cluster(current_feats, flat_ids, pool_type='mean')","mean_feats = aggregate_features_fixed_order(current_feats, flat_ids, sp_positions if lvl == 0 else None)")
    bank=bank.replace('current_feats = aggregate_cluster(current_feats, flat_ids, pool_type=self.cluster_pool_type)',"current_feats = (aggregate_features_fixed_order(current_feats, flat_ids, sp_positions if lvl == 0 else None)\n                    if self.cluster_pool_type == 'mean' else aggregate_cluster(current_feats, flat_ids, pool_type=self.cluster_pool_type))")
    text=text[:start]+bank+text[end:]
    text+='''

def aggregate_features_fixed_order(feats, cluster_ids, positions=None):
    """Fixed feature means only; original geometry/FPS reduction is untouched."""
    if cluster_ids.numel() == 0:
        return feats
    ids = cluster_ids.detach().cpu().numpy()
    if positions is None:
        order = np.argsort(ids, kind='stable')
    else:
        xyz = positions.detach().cpu().numpy()
        if xyz.shape != (len(ids), 3) or not np.isfinite(xyz).all():
            raise ValueError('Invalid feature-member geometry')
        order = np.lexsort((xyz[:, 2], xyz[:, 1], xyz[:, 0], ids))
        same = ids[order[1:]] == ids[order[:-1]]
        tied = np.all(xyz[order[1:]] == xyz[order[:-1]], axis=1)
        if np.any(same & tied):
            raise ValueError('Coincident feature members need a separately reviewed tie rule')
    index = torch.as_tensor(order.copy(), dtype=torch.long, device=feats.device)
    counts = torch.bincount(cluster_ids, minlength=int(ids.max()) + 1)
    pointers = torch.cat((counts.new_zeros(1), counts.cumsum(0)))
    return segment_csr(feats[index], pointers, reduce='mean')
'''
    ast.parse(text);path.write_text(text,encoding='utf-8')
    path=package/'dec.py';text=path.read_text(encoding='utf-8')
    original='batch2flatten(inst_feats, batch_mask), batch_offsets)'
    assert text.count(original)==1
    text=text.replace(original,'batch2flatten(inst_feats, batch_mask), batch_offsets,\n                batch2flatten(sp_pos, batch_mask))')
    ast.parse(text);path.write_text(text,encoding='utf-8')
    frozen=OUT/'source_r1';frozen.mkdir(exist_ok=False)
    for path in package.glob('*.py'):(frozen/path.name).write_bytes(path.read_bytes())
    (frozen/'candidate.yaml').write_bytes(config.read_bytes())
    source=c.save('revision1_source.json',{'revision':1,'preregistration':c.evidence(protocol),'files':[c.evidence(x) for x in sorted(frozen.iterdir())]})
    c.advance([protocol,source], 'Execute R1 current exact source native full-source/backward controls; keep R0 failures. No scientific PASS until frozen gates actually pass.')
    # Immutable new controller/source copies: earlier test scripts stay hash-valid.
    controller=(OUT/'validation_h2.py').read_text(encoding='utf-8').replace('_validation_h2','_validation_r1').replace("OUT/'validation_h2'","OUT/'validation_r1'")
    controller=controller.replace('validation_h2_preregistration','validation_r1_execution_preregistration').replace('validation_h2_staging','validation_r1_staging').replace("'validation_h2_'+label","'validation_r1_'+label")
    with (OUT/'validation_r1.py').open('x',encoding='utf-8') as stream:stream.write(controller)
    print('revision1 preregistered/applied; native tests pending')


if __name__=='__main__':main()
