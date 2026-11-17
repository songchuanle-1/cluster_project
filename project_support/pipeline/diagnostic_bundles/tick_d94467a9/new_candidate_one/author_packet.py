"""Independent NEC model package from pinned frozen original M95 bytes only."""
from pathlib import Path
import hashlib,ast
import author_guard as ag
ag.check();ROOT=ag.ROOT;HERE=ag.HERE
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/new_candidate_prepare'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
OLD=FROZEN/'staged_repository/framework/model/Quard_model'/(BASE+'_wfc')
NAME=BASE+'_nec';DEST=HERE/'staged_repository/framework/model/Quard_model'/NAME
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(FROZEN/'preparation.json')=='659528feeee9f8a08f2b5e5aad22af9f21f8cc5994940e8fd04854b1976316c6'
for name in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py'):ag.write_bytes(DEST/name,(OLD/name).read_bytes())
original_path=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/lft_candidate_prepare/original_m95_hier_postprocess.py.txt'
assert sha(original_path)=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
original=original_path.read_text(encoding='utf-8');tree=ast.parse(original)
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='C2F_ClusterAttn_CTF')
forward=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
old_forward=ast.get_source_segment(original,forward)
new_forward='''def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        normalized = [self.cluster_ffn_norm[lvl](cluster_feats_list[lvl])
                      for lvl in range(self.num_scales)]
        delta = self.node_edge_coupling(normalized, cluster_ids_list)
        refined_cluster_feats = [cf + change for cf, change in zip(cluster_feats_list, delta)]
        point_message = self._cluster_to_points(
            point_feats, refined_cluster_feats, cluster_ids_list, point_mask)
        point_message = self.message_norm(point_message)
        point_message = point_message.masked_fill(point_mask.unsqueeze(-1), 0)
        return {'point': point_message}'''
assert original.count(old_forward)==1
changed=original.replace(old_forward,new_forward)
marker='''        self.cluster_ffn_norm = nn.ModuleList([
            nn.LayerNorm(d_model) for _ in range(num_scales)
        ])'''
assert changed.count(marker)==1
changed=changed.replace(marker,marker+'''
        if num_scales != 3:
            raise ValueError('NEC requires original three hierarchy scales')
        with torch.random.fork_rng(devices=[]):
            self.node_edge_coupling = NodeEdgeComposition(d_model)
        self.cluster_ffn = nn.ModuleList([nn.Identity() for _ in range(num_scales)])''')
changed='from .node_edge_coupling import NodeEdgeComposition\n'+changed
ag.write_text(DEST/'hier_postprocess.py',changed)
ag.write_bytes(DEST/'node_edge_coupling.py',(HERE/'node_edge_source.txt').read_bytes())
old_yaml=FROZEN/'staged_repository/configs/Quard/ctf_hcg_csort_wfc'/(BASE+'_wfc.yaml')
assert sha(old_yaml)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
ag.write_bytes(HERE/'staged_repository/configs/Quard/ctf_hcg_csort_nec'/(NAME+'.yaml'),old_yaml.read_bytes())
print({'model_files':len(list(DEST.glob('*.py'))),'new_helper_sha256':sha(DEST/'node_edge_coupling.py')})
