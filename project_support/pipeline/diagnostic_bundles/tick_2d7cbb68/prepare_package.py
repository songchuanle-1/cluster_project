"""Build an isolated structural package;do not touch any existing model."""
import ast
import shutil
import yaml
from ops import *
guard(600)
new_name=NAME+'_cpa_r1'
source=ROOT/'Cluster/framework/model/Quard_model'/NAME
target=ROOT/'Cluster/framework/model/Quard_model'/new_name
assert not target.exists()
target.mkdir()
for path in source.iterdir():
    if path.is_file() and path.suffix=='.py':shutil.copyfile(path,target/path.name)
hierarchy=ast.parse((source/'hier_postprocess.py').read_text(encoding='utf-8-sig'))
base=next(c for c in hierarchy.body if isinstance(c,ast.ClassDef) and c.name=='C2F_ClusterAttn_CTF_HCG')
gather=copy_gather=ast.parse(ast.unparse(next(m for m in base.body if isinstance(m,ast.FunctionDef) and m.name=='_cluster_to_points'))).body[0]
loop=next(n for n in gather.body if isinstance(n,ast.For) and ast.unparse(n.target)=='lvl')
insertion=ast.parse("""if lvl==num_scales-1:
    message,_=coarse_readback(point_feats,cluster_feats_list[lvl],point_mask,heads=self.nhead,key_features=self._raw_coarse_keys)
    scale_msgs.append(message)
    continue
""").body
loop.body[0:0]=insertion
newclass=ast.parse('''class C2F_ClusterAttn_CTF_HCG_CPA_CSORT(C2F_ClusterAttn_CTF_HCG_CSORT):
    def forward(self,point_feats,query,point_mask,cluster_feats_list,child_cluster_maps,cluster_ids_list):
        self._raw_coarse_keys=cluster_feats_list[-1]
        try:
            return super().forward(point_feats,query,point_mask,cluster_feats_list,child_cluster_maps,cluster_ids_list)
        finally:
            self._raw_coarse_keys=None
''').body[0]
newclass.body.append(gather)
hierarchy.body.insert(0,ast.ImportFrom(module='coarse_cross_attention',names=[ast.alias(name='coarse_readback')],level=1))
hierarchy.body.append(newclass)
ast.fix_missing_locations(hierarchy)
(target/'hier_postprocess.py').write_text(ast.unparse(hierarchy)+'\n',encoding='utf-8')
dec=ast.parse((source/'dec.py').read_text(encoding='utf-8-sig'))
imports=0;mapping=0
for node in ast.walk(dec):
    if isinstance(node,ast.ImportFrom) and node.module=='hier_postprocess' and node.level==1:
        node.names.append(ast.alias(name='C2F_ClusterAttn_CTF_HCG_CPA_CSORT'));imports+=1
    if isinstance(node,ast.Assign) and len(node.targets)==1 and ast.unparse(node.targets[0])=='cluster_att_classes':
        node.value.keys.append(ast.Constant('ctf_hcg_cpa_csort'))
        node.value.values.append(ast.Name(id='C2F_ClusterAttn_CTF_HCG_CPA_CSORT',ctx=ast.Load()));mapping+=1
assert imports==mapping==1
ast.fix_missing_locations(dec)
(target/'dec.py').write_text(ast.unparse(dec)+'\n',encoding='utf-8')
shutil.copyfile(OUT/'raw_key_revision1/coarse_cross_attention_r1.py',target/'coarse_cross_attention.py')
config_path=ROOT/'Cluster/configs/Quard/ctf_hcg_csort'/str(NAME+'.yaml')
cfg=yaml.safe_load(config_path.read_text(encoding='utf-8'))
cfg['model']['dec']['cluster_mode']='ctf_hcg_cpa_csort'
destination=ROOT/'Cluster/configs/Quard/ctf_hcg_csort_cpa_r1'/str(new_name+'.yaml')
destination.parent.mkdir(exist_ok=False)
destination.write_text(yaml.safe_dump(cfg,sort_keys=False),encoding='utf-8')
same=yaml.safe_load(destination.read_text())
same['model']['dec']['cluster_mode']='ctf_hcg_csort'
assert same==yaml.safe_load(config_path.read_text())
sources={p.name:tick.digest(p) for p in target.glob('*.py')}
foreign=[]
for p in target.glob('*.py'):
    parsed=ast.parse(p.read_text(encoding='utf-8'))
    for n in ast.walk(parsed):
        if isinstance(n,ast.ImportFrom) and n.module and 'model_base1' in n.module:foreign.append([p.name,n.module])
        if isinstance(n,ast.Import):
            foreign.extend([p.name,a.name] for a in n.names if 'model_base1' in a.name)
assert not foreign,foreign
save('independent_package.json',{'name':new_name,'source_path':target.as_posix(),'source_hashes':sources,
 'candidate_config':evidence(destination),'baseline_config':evidence(config_path),
 'only_config_change':'model.dec.cluster_mode=ctf_hcg_cpa_csort;independent filename/package',
 'foreign_variant_imports':foreign,'new_trainable_parameters':0,'existing_sources_modified':False,
 'scientific_admission':False,'full_native_candidate_backward':'pending','resources':'pending','diagnosis':'not yet passed'})
advance([OUT/'independent_package.json',destination,*target.glob('*.py')],stage='validation',
 next_action='Execute independent package full native loss/backward and matched resource checks;do not train until all gates and diagnosis are genuinely passed')
print(json.dumps({'package':new_name,'files':len(sources),'isolated':True,'config_hyperparameters_unchanged':True,'admission':False}))
