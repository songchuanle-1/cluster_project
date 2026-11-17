"""Private SFC source assembly, no model imports, Git or shared writes."""
from pathlib import Path
import hashlib,json,shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
review=HERE.parent/'sfc_proposal_boundary_review.json'
assert hashlib.sha256(review.read_bytes()).hexdigest()=='98dd303432e20e14e3532745e6b0244b9ca06990ff56b13d626d6ea9133d28e2'
assert json.loads(review.read_text(encoding='utf-8'))['material_concerns']==[]
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_sfc')
MODEL.mkdir(parents=True,exist_ok=True)
for p in BASE.glob('*.py'):shutil.copyfile(p,MODEL/p.name)
config=Path('configs/Quard/ctf_hcg_csort_sfc')/(NAME+'_sfc.yaml')
target=HERE/'staged_repository'/config;target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml'),target)
source=(BASE/'hier_postprocess.py').read_text(encoding='utf-8')
source='from .synchronous_forest import SynchronousForestComposition\n'+source
needle='''        self.cluster_ffn_norm = nn.ModuleList([
            nn.LayerNorm(d_model) for _ in range(num_scales)
        ])'''
assert source.count(needle)==1
source=source.replace(needle,needle+'''
        if num_scales != 3 or dropout != 0.0:
            raise ValueError('SFC uses the original three-scale zero-dropout native configuration')
        # Preserve original FFN/LN RNG construction before isolated new-cell initialization.
        with torch.random.fork_rng(devices=[]):
            self.synchronous_forest = SynchronousForestComposition(d_model)
        self.cluster_ffn = nn.ModuleList([nn.Identity() for _ in range(num_scales)])''')
needle='''        refined_cluster_feats = []
        for lvl in range(self.num_scales):
            cf = cluster_feats_list[lvl]  # [B, K_lvl, C]
            # Pre-norm residual FFN
            refined = cf + self.cluster_ffn[lvl](self.cluster_ffn_norm[lvl](cf))
            refined_cluster_feats.append(refined)'''
assert source.count(needle)==1
source=source.replace(needle,'''        normalized = [self.cluster_ffn_norm[lvl](cf)
                      for lvl, cf in enumerate(cluster_feats_list)]
        deltas = self.synchronous_forest(normalized, cluster_ids_list)
        refined_cluster_feats = [cf + deltas[lvl]
                                 for lvl, cf in enumerate(cluster_feats_list)]''')
(MODEL/'hier_postprocess.py').write_text(source,encoding='utf-8',newline='\n')
print(json.dumps({'model':str(MODEL),'config':str(config)}))
