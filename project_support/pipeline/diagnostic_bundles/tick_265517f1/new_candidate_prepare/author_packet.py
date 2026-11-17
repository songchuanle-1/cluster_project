"""Create one private independent HVD source/config package from frozen M95."""
from pathlib import Path
import ast, hashlib, json
import author_guard as ag
ag.author_guard()
ROOT=ag.ROOT
HERE=ag.HERE
FROZEN=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/new_candidate_prepare'
BASE='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
OLD=FROZEN/'staged_repository/framework/model/Quard_model'/(BASE+'_wfc')
NAME=BASE+'_hvd'
STAGE=HERE/'staged_repository'
DEST=STAGE/'framework/model/Quard_model'/NAME
ORIGINAL=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/lft_candidate_prepare/original_m95_hier_postprocess.py.txt'
assert ag.sha(ORIGINAL)=='7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
for name in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py'):
    ag.write_bytes(DEST/name,(OLD/name).read_bytes())
original=ORIGINAL.read_text(encoding='utf-8')
tree=ast.parse(original)
cls=next(node for node in tree.body if isinstance(node,ast.ClassDef) and node.name=='C2F_ClusterAttn_CTF')
forward=next(node for node in cls.body if isinstance(node,ast.FunctionDef) and node.name=='forward')
old_forward=ast.get_source_segment(original,forward)
new_forward='''def forward(self, point_feats, query, point_mask,
                cluster_feats_list, child_cluster_maps, cluster_ids_list):
        normalized = [self.cluster_ffn_norm[level](cluster_feats_list[level])
                      for level in range(self.num_scales)]
        changes = self.variance_decomposition(
            point_feats, point_mask, normalized, cluster_ids_list)
        refined_cluster_feats = [raw + delta
                                 for raw, delta in zip(cluster_feats_list, changes)]
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
            raise ValueError('HVD requires the original three hierarchy scales')
        with torch.random.fork_rng(devices=[]):
            self.variance_decomposition = HierarchicalVarianceDecomposition(d_model)
        self.cluster_ffn = nn.ModuleList([nn.Identity() for _ in range(num_scales)])''')
changed='from .variance_decomposition import HierarchicalVarianceDecomposition\n'+changed
ag.write_text(DEST/'hier_postprocess.py',changed)
ag.write_bytes(DEST/'variance_decomposition.py',(HERE/'variance_decomposition_source.txt').read_bytes())
yaml=FROZEN/'staged_repository/configs/Quard/ctf_hcg_csort_wfc'/(BASE+'_wfc.yaml')
assert ag.sha(yaml)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
config='configs/Quard/ctf_hcg_csort_hvd/'+NAME+'.yaml'
ag.write_bytes(STAGE/config,yaml.read_bytes())
files={str(p.relative_to(STAGE)).replace('\\','/'):ag.sha(p) for p in sorted(STAGE.rglob('*')) if p.is_file()}
assert len(files)==9 and len(list(DEST.glob('*.py')))==8
manifest={
 'schema_version':1,'candidate_id':'hierarchy-native-variance-decomposition-composition',
 'experiment_id':'M230-HVD','code_commit':None,'source_commit':None,
 'source_parent_commit':None,'actual_parent':None,'future_version_parent':None,
 'config':config,'source_file_count':9,'model_file_count':8,
 'source_files':files,'source_files_exact9':files,
 'staged_repository':str(STAGE.relative_to(ROOT)).replace('\\','/'),
 'original_M95_hier_recovered_sha256':ag.sha(ORIGINAL),
 'original_YAML_sha256':ag.sha(yaml),'primary_or_dirty_user_file_read':False,
 'scope':'Private source preparation only; no version saved, registration, native run or admission.'}
ag.write_json(HERE/'source_manifest.json',manifest)
print(json.dumps({'file_count':len(files),'helper_sha256':ag.sha(DEST/'variance_decomposition.py'),
                  'manifest_sha256':ag.sha(HERE/'source_manifest.json')}))
