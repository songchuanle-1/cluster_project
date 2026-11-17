"""Bounded FCB final-map, original integration AST and actual CTF forward checks.
Only stdlib carriers, no module imports or Tensor/native results.
"""
from pathlib import Path
from types import SimpleNamespace
from itertools import product
import ast, hashlib, json

R = Path('D:/project/cluster_project')
B = Path(__file__).resolve().parent
P = B / 'new_candidate_prepare'
S = P / 'staged_repository'
pkg = S / 'framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_fcb'
oldpkg = R / 'pipeline/diagnostic_bundles/tick_e666cac0/new_candidate_prepare/staged_repository/framework/model/Quard_model/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_aoc'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
prep = json.loads((P / 'preparation.json').read_text())
checks = []
def ck(value, label):
    assert value, label
    checks.append(label)
ck(sha(P / 'preparation.json') == '44c63ca146496f9052f3823f1ab299bf3fa8e044bab0df014abc33c2ff9343a2', 'final preparation bound')
for name, digest in prep['prepared_file_hashes'].items():
    ck(sha(P / name) == digest, 'actual frozen map: ' + name)
for name, digest in prep['source_files'].items():
    ck(sha(S / name) == digest, 'actual nine source/config map: ' + name)
ck(len(prep['prepared_file_hashes']) == 18 and len(prep['source_files']) == 9, 'exact eighteen-map and nine-source scopes')
ck(all(prep[k] is None for k in ('code_commit', 'source_commit', 'source_parent_commit')), 'unversioned declarations remain null')
for name in ('__init__.py', 'backbone.py', 'dec.py', 'loss.py', 'network.py', 'sample_model.py'):
    ck((pkg / name).read_bytes() == (oldpkg / name).read_bytes(), 'original common model bytes: ' + name)
ck(prep['source_files'][next(k for k in prep['source_files'] if k.endswith('.yaml'))] == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a', 'original YAML exact hash')
ht = ast.parse((pkg / 'hier_postprocess.py').read_text(encoding='utf-8'))
ot = ast.parse((oldpkg / 'hier_postprocess.py').read_text(encoding='utf-8'))
dump = lambda n: ast.dump(n, include_attributes=False)
new_defs = {n.name:n for n in ht.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
old_defs = {n.name:n for n in ot.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
ck(set(new_defs) == set(old_defs), 'original hierarchy function/class inventory unchanged')
for name,n in new_defs.items():
    if name != 'C2F_ClusterAttn_CTF':
        ck(dump(n) == dump(old_defs[name]), 'original hierarchy AST: ' + name)
ctf = new_defs['C2F_ClusterAttn_CTF']; octf = old_defs['C2F_ClusterAttn_CTF']
ctor = next(n for n in ctf.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
octor = next(n for n in octf.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
prefix = lambda n:n.body[:next(i for i,v in enumerate(n.body) if isinstance(v,ast.If))]
ck([dump(n) for n in prefix(ctor)] == [dump(n) for n in prefix(octor)], 'original super/three FFN/three LN allocation order before fork')
ck('with torch.random.fork_rng(devices=[]):' in ast.unparse(ctor), 'new-map constructor restores original CPU RNG stream')
ck('self.cluster_ffn = nn.ModuleList([nn.Identity() for _ in range(num_scales)])' in ast.unparse(ctor), 'all three replaced FFNs unregistered')
ck('FineCoarseBipartiteComposition(d_model)' in ast.unparse(ctor), 'new two-map module wired')

# Reuse carrier definitions only, not any old suite or the earlier independent controls.
carrier_tree = ast.parse((R / 'pipeline/diagnostic_bundles/tick_01d9102a/dce_independent_software.py').read_text())
env={'product':product}
defs=[n for n in carrier_tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and n.name in ('T','prod','cat')]
exec(compile(ast.fix_missing_locations(ast.Module(defs,[])),'carrier_definitions_only','exec'),env)
T=env['T']
forward=next(n for n in ctf.body if isinstance(n,ast.FunctionDef) and n.name=='forward')
fn={}
exec(compile(ast.fix_missing_locations(ast.Module([forward],[])),str(pkg/'hier_postprocess.py'),'exec'),fn)
for empty in (False,True):
    events=[]; raw=[T([float(l+1),float(l+3)],(1,2,1)) for l in range(3)]
    delta=[T([0.,0.] if empty else [.1*(l+1),.2*(l+1)],(1,2,1)) for l in range(3)]
    point_feats=object(); query=object(); memberships=object(); children=object()
    class Mask:
        def unsqueeze(self,axis):
            assert axis==-1; events.append('mask_unsqueeze');return self
    mask=Mask()
    class Message:
        def masked_fill(self,actualmask,value):
            assert actualmask is mask and value==0;events.append('original_mask');return self
    message=Message()
    class Owner:
        def fine_coarse_bipartite(self,normalized,ids):
            ck(ids is memberships, 'CTF forwards actual original memberships')
            ck(all(n.v==[v+10+l for v in raw[l].v] for l,n in enumerate(normalized)), 'new core consumes three actual normalized banks')
            events.append('core');return delta
        def _cluster_to_points(self,p,refined,ids,m):
            ck(p is point_feats and ids is memberships and m is mask, 'original HCG receives original identities')
            ck(all(f.v==[x+y for x,y in zip(r.v,d.v)] for f,r,d in zip(refined,raw,delta)), 'only original raw plus delta skips, not normalized plus delta')
            events.append('HCG');return message
        def message_norm(self,m):
            ck(m is message, 'original message norm input identity');events.append('message_norm');return m
    owner=Owner()
    def norm(l):
        def f(x):
            ck(x is raw[l], 'original LN input identity level'+str(l));events.append('LN'+str(l));return x+10+l
        return f
    owner.cluster_ffn_norm=[norm(l) for l in range(3)]
    result=fn['forward'](owner,point_feats,query,mask,raw,children,memberships)
    ck(result=={'point':message}, 'actual CTF returns original masked message')
    ck(events==['LN0','LN1','LN2','core','HCG','message_norm','mask_unsqueeze','original_mask'], 'actual production CTF phase/order exactly once'+(' empty delta' if empty else ' nonempty delta'))

proof={'status':'FCB_FROZEN_MAP_AND_ACTUAL_CTF_FORWARD_INTEGRATION_STDLIB_VALIDATED_NOT_NATIVE',
       'checks':checks,'actual_check_count':len(checks),
       'scope':'Read actual eighteen hashes/nine source-config hashes, six copied model bytes, unchanged hierarchy AST including raw pooling/FPS/HCG/CSORT, original constructor prefix and fork. Executed actual production CTF forward with transparent stdlib three-LN/core/message carriers for zero/nonzero deltas. Original dec/network bytes preserve single instance readback/mask integration. No Torch, model construction, learned map/GELU, FP32, gradient, native or resource execution.',
       'helper_sha256':sha(pkg/'fine_coarse_bipartite.py'),'hierarchy_sha256':sha(pkg/'hier_postprocess.py')}
if __name__=='__main__': print(json.dumps(proof,indent=2,allow_nan=False))
