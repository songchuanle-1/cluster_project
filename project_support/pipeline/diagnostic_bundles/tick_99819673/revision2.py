"""Final default-bounded revision: canonical active-encoder SP ordering."""
import ast
from pathlib import Path
import register
c=register.c
ROOT,OUT=register.ROOT,register.OUT
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_rstr'


def main():
    c.guard(1500)
    work=c.tick.load(ROOT/'pipeline/research_work.json');candidate=next(x for x in work['candidates'] if x['id']==c.CID)
    history=candidate['revision_history'];assert len(history)==1 and history[0]['result']=='pending'
    r1=c.tick.load(OUT/'validation_r1_controls_candidate_result.json')
    assert r1['execution_completed'] and not r1['all_full_source_controls_passed']
    assert max(v for x in r1['controls']['identity_repeats'] for v in x.values())==0
    assert max(r1['controls']['disabled_vs_original_parent'].values())==0
    result_evidence=[c.evidence(OUT/'validation_r1_controls_candidate_result.json'),c.evidence(OUT/'validation_r1_controls_candidate_execution.json')]
    history[0]['result']='failed';history[0]['evidence']+=result_evidence;history[0]['result_evidence']=result_evidence
    protocol=c.save('revision2_preregistration.json',{'preregistered_at':c.now(),'candidate_id':c.CID,'revision':2,
        'failure_scope':'implementation','failure_evidence':result_evidence,
        'reason':'R1 removes all repeat/disabled-parent differences (exact0) but row reversal changes language1.907e-6 and inst2.861e-6. Language LIA source attention is BEFORE bank/transport, so deterministic bank alone cannot address its reduction order. Fusion global mean and ILA also use row order.',
        'change':'Only active final Encoder_layer wrapper: stable xyz lexicographic ordering of valid SP rows, apply identical permutation to inst_feats, batch_mask, sp_pos and first-level bank membership; leave language/query/proposal/query_pos and every middle/coarse token ID/FPS tree untouched. Execute existing active encoder body on canonical rows, inverse-restore point output and restore original bank membership object in finally. No feature/coordinate values, model params, precision, threshold, attention or supervision change.',
        'prediction':'Native full-source replay and transported SP row reversal enter the same complete active encoder row sequence; identity,row-inverse,disabled-original-parent feature controls<=1e-6 and native loss gradients remain finite/nonzero. Sorting itself is no efficacy mechanism or new candidate.',
        'scope':'One local numerical ordering repair, final default revision2. Original R0/R1 failures preserved; no R3 without scoped authorization. No original FPS rerun/change, no seed/dtype/tolerance change.',
        'ties':'Require unique valid xyz; if coincident centroids occur, fail rather than invent a favorable tie rule. Padding kept after valid rows and inverse-restored.',
        'controls':'Retest complete actual native backward/source controls, independent source/config, resource pair on exact current code; then affected8scene content/strict controls before admission.',
        'training':0,'commit':False})
    history.append({'revision':2,'failure_scope':'implementation','reason':c.tick.load(protocol)['reason'],
        'change':c.tick.load(protocol)['change'],'prediction':c.tick.load(protocol)['prediction'],
        'preregistered_at':c.tick.load(protocol)['preregistered_at'],'failure_evidence':result_evidence,'result':'pending','evidence':[c.evidence(protocol)]})
    candidate['next_action']='Execute final bounded R2 exact-source full native controls/backward/resources and affected content controls; no further repair or admission from incomplete gates.'
    c.tick.save(ROOT/'pipeline/research_work.json',work)
    package=ROOT/'Cluster/framework/model/Quard_model'/NAME
    path=package/'dec.py';text=path.read_text(encoding='utf-8').replace('import torch\n','import numpy as np\nimport torch\n',1)
    marker='    def forward(self, lang_feats, lang_masks, inst_feats, batch_mask,\n                query, sp_pos, query_pos,\n                batch_offsets=None):'
    assert text.count(marker)==1
    wrapper='''    def forward(self, lang_feats, lang_masks, inst_feats, batch_mask,
                query, sp_pos, query_pos, batch_offsets=None):
        if not self.use_cluster or batch_offsets is None:
            return self._forward_native(lang_feats, lang_masks, inst_feats, batch_mask,
                                        query, sp_pos, query_pos, batch_offsets)
        permutations = []
        inverses = []
        width = inst_feats.shape[1]
        for b in range(inst_feats.shape[0]):
            valid = int((~batch_mask[b]).sum())
            xyz = sp_pos[b, :valid].detach().cpu().numpy()
            order = np.lexsort((xyz[:, 2], xyz[:, 1], xyz[:, 0]))
            if np.any(np.all(xyz[order[1:]] == xyz[order[:-1]], axis=1)):
                raise ValueError('Coincident SP positions need a reviewed canonical tie rule')
            index = torch.as_tensor(np.concatenate((order, np.arange(valid, width))).copy(),
                                    device=inst_feats.device, dtype=torch.long)
            permutations.append(index)
            inverses.append(torch.argsort(index))
        aligned_feats = torch.stack([x[p] for x, p in zip(inst_feats, permutations)])
        aligned_mask = torch.stack([x[p] for x, p in zip(batch_mask, permutations)])
        aligned_pos = torch.stack([x[p] for x, p in zip(sp_pos, permutations)])
        original_ids = self.cluster_bank.cluster_ids_list
        aligned_ids = [list(level) for level in original_ids]
        for b, ids in enumerate(original_ids[0]):
            aligned_ids[0][b] = ids[permutations[b][:ids.numel()]]
        self.cluster_bank.cluster_ids_list = aligned_ids
        try:
            language, points = self._forward_native(
                lang_feats, lang_masks, aligned_feats, aligned_mask,
                query, aligned_pos, query_pos, batch_offsets)
        finally:
            self.cluster_bank.cluster_ids_list = original_ids
        restored = torch.stack([x[p] for x, p in zip(points, inverses)])
        return language, restored

    def _forward_native(self, lang_feats, lang_masks, inst_feats, batch_mask,
                        query, sp_pos, query_pos, batch_offsets=None):'''
    text=text.replace(marker,wrapper)
    ast.parse(text);path.write_text(text,encoding='utf-8')
    frozen=OUT/'source_r2';frozen.mkdir(exist_ok=False)
    for path in package.glob('*.py'):(frozen/path.name).write_bytes(path.read_bytes())
    (frozen/'candidate.yaml').write_bytes((ROOT/'Cluster/configs/Quard/ctf_hcg_csort_rstr'/(NAME+'.yaml')).read_bytes())
    source=c.save('revision2_source.json',{'revision':2,'preregistration':c.evidence(protocol),'files':[c.evidence(x) for x in sorted(frozen.iterdir())]})
    c.advance([protocol,source,Path(__file__)],'Execute final default R2; preserve all prior failures and unchanged original gates.')
    controller=(OUT/'validation_h2.py').read_text(encoding='utf-8').replace('_validation_h2','_validation_r2').replace("OUT/'validation_h2'","OUT/'validation_r2'")
    controller=controller.replace('validation_h2_preregistration','validation_r2_execution_preregistration').replace('validation_h2_staging','validation_r2_staging').replace("'validation_h2_'+label","'validation_r2_'+label")
    with (OUT/'validation_r2.py').open('x',encoding='utf-8') as stream:stream.write(controller)
    print('revision2 preregistered/applied; native gates pending')


if __name__=='__main__':main()
