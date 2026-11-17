"""Private AOC source assembly only; no imports, Git or shared writes."""
from pathlib import Path
import ast, json, shutil
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
BASE=ROOT/'Cluster/framework/model/Quard_model'/NAME
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_aoc')
MODEL.mkdir(parents=True,exist_ok=True)
for p in BASE.glob('*.py'):shutil.copyfile(p,MODEL/p.name)
config=Path('configs/Quard/ctf_hcg_csort_aoc')/(NAME+'_aoc.yaml')
target=HERE/'staged_repository'/config
target.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/(NAME+'.yaml'),target)
source=(BASE/'hier_postprocess.py').read_text(encoding='utf-8')
source='from .ancestral_commutator import AncestralOrderCommutatorComposition\n'+source
needle='''        self.cluster_ffn_norm = nn.ModuleList([
            nn.LayerNorm(d_model) for _ in range(num_scales)
        ])'''
assert source.count(needle)==1
source=source.replace(needle,needle+'''
        if num_scales != 3 or dropout != 0.0:
            raise ValueError('AOC uses the original three-scale zero-dropout native configuration')
        # Preserve original constructor RNG consumption before isolated new-cell construction.
        with torch.random.fork_rng(devices=[]):
            self.ancestral_commutator = AncestralOrderCommutatorComposition(d_model)
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
        deltas = self.ancestral_commutator(normalized, cluster_ids_list)
        refined_cluster_feats = [cf + deltas[lvl]
                                 for lvl, cf in enumerate(cluster_feats_list)]''')
(MODEL/'hier_postprocess.py').write_text(source,encoding='utf-8',newline='\n')
print(json.dumps({'source_model':str(MODEL),'config':str(config)}))
