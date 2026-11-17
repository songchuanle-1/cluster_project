"""Create MIC private source from frozen bytes only, no primary/model imports."""
from pathlib import Path
import ast, json, hashlib
from author_guard import author_guard, write_new, HERE, ROOT, sha
NAME='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'
AOC=ROOT/'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare'
ELC=ROOT/'pipeline/diagnostic_bundles/tick_87f03f29/new_candidate_prepare'
WFC=ROOT/'pipeline/diagnostic_bundles/tick_34f4e385/new_candidate_prepare'
MODEL=HERE/'staged_repository/framework/model/Quard_model'/(NAME+'_mic')

def main():
    author_guard()
    assert sha(ELC/'preparation.json')=='c77746ae35e4f3bfbc1c58e62aff629798946bb91dd0befbd08f247ca5dd7dd8'
    assert sha(WFC/'preparation.json')=='659528feeee9f8a08f2b5e5aad22af9f21f8cc5994940e8fd04854b1976316c6'
    old_model=ELC/'staged_repository/framework/model/Quard_model'/(NAME+'_elc')
    tree=ast.parse((WFC/'author_packet.py').read_text(encoding='utf8'))
    fn=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='restored_original_hier')
    ns={'ast':ast,'hashlib':hashlib,'FROZEN':ELC,'OLD':old_model,'ORIGINAL_HIER_SHA':'7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'}
    exec(compile(ast.Module(body=[fn],type_ignores=[]),'frozen_original_recovery','exec'),ns)
    original,literals=ns['restored_original_hier']()
    write_new('original_m95_hier.py.txt',original)
    helper=(AOC/'staged_repository/framework/model/Quard_model'/(NAME+'_aoc')/'ancestral_commutator.py').read_text(encoding='utf8')
    assert hashlib.sha256(helper.encode()).hexdigest()=='b0a4d1ea71fa9cf94fa090e4f3e6eb63a3be02a62944a0741f8d8125d1a4c470'
    helper=helper.replace('M222 AOC: two private ancestor-order compositions, shared binary cell.','M229 MIC: shared Boolean-lattice ancestry interaction, eight subset vertices.')
    for a,b in [('build_ancestry_path_plan','build_mobius_path_plan'),('prepare_ancestry_path_plans','prepare_mobius_path_plans'),('mean_path_messages','mean_mobius_paths'),('AncestralOrderCommutatorComposition','AncestryMobiusInteraction'),('nn.Linear(2 * channels, channels)','nn.Linear(channels, channels)'),('AOC channels changed','MIC channels changed')]:
        helper=helper.replace(a,b)
    start=helper.index('        # Both order branches')
    end=helper.index('        middle_delta = ',start)
    helper=helper[:start]+'''        # One shared map/GELU call for all eight subset vertices.
        n = len(fine_index)
        zero = a.new_zeros(a.shape)
        subset_inputs = torch.cat([a+b+c, a+b, a+c, b+c, a, b, c, zero], dim=0)
        subset_outputs = self.activation(self.cell(subset_inputs))
        contrast = (subset_outputs[:n] - subset_outputs[n:2*n]
                    - subset_outputs[2*n:3*n] - subset_outputs[3*n:4*n]
                    + subset_outputs[4*n:5*n] + subset_outputs[5*n:6*n]
                    + subset_outputs[6*n:7*n] - subset_outputs[7*n:8*n])
'''+helper[end:]
    for f in ('__init__.py','backbone.py','dec.py','loss.py','network.py','sample_model.py'):
        src=old_model/f
        dest=MODEL/f
        author_guard();dest.parent.mkdir(parents=True,exist_ok=True)
        with dest.open('xb') as out:out.write(src.read_bytes())
    changed='''        normalized = [self.cluster_ffn_norm[level](cluster_feats_list[level])
                      for level in range(self.num_scales)]
        delta = self.mobius_interaction(normalized, cluster_ids_list)
        refined_cluster_feats = [cf + value for cf, value in zip(cluster_feats_list, delta)]'''
    extension='''
        if num_scales != 3:
            raise ValueError('MIC requires the original three hierarchy scales')
        # Preserve original FFN/LN constructor RNG before isolated new core.
        with torch.random.fork_rng(devices=[]):
            self.mobius_interaction = AncestryMobiusInteraction(d_model)
        self.cluster_ffn = nn.ModuleList([nn.Identity() for _ in range(num_scales)])'''
    assert original.count(literals['old'])==original.count(literals['marker'])==1
    hier='from .ancestry_mobius import AncestryMobiusInteraction\n'+original.replace(literals['old'],changed,1).replace(literals['marker'],literals['marker']+extension,1)
    write_new(str((MODEL/'hier_postprocess.py').relative_to(HERE)),hier)
    write_new(str((MODEL/'ancestry_mobius.py').relative_to(HERE)),helper)
    yaml=next((ELC/'staged_repository/configs').rglob('*.yaml'))
    assert sha(yaml)=='a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
    dest=HERE/'staged_repository/configs/Quard/ctf_hcg_csort_mic'/(NAME+'_mic.yaml')
    author_guard();dest.parent.mkdir(parents=True,exist_ok=True)
    with dest.open('xb') as out:out.write(yaml.read_bytes())
    provenance={'scope':'Pinned frozen common6/YAML and recovered original M95 hier only. AOC metadata/packing shell adapted, numerical DAG replaced. No primary dirty files or Torch imports.','frozen_original_hier_sha256':hashlib.sha256(original.encode()).hexdigest(),'frozen_AOC_helper_sha256':'b0a4d1ea71fa9cf94fa090e4f3e6eb63a3be02a62944a0741f8d8125d1a4c470','source_files_exact9':{str(x.relative_to(HERE/'staged_repository')).replace('\\','/'):sha(x) for x in sorted((HERE/'staged_repository').rglob('*')) if x.is_file()},'author':author_guard()}
    write_new('source_provenance.json',json.dumps(provenance,indent=2)+'\n')
    print(json.dumps({'count':len(provenance['source_files_exact9']),'helper':sha(MODEL/'ancestry_mobius.py')}))

if __name__=='__main__':main()
