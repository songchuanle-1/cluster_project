"""Private resource-policy copy only; no adapter entry, Git, remote or shared writes."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_operational_prepare'
NATIVE=ROOT/'pipeline/diagnostic_bundles/tick_928313fd/sfc_native_prepare'
SERVERS_SHA='19b3753d13a8253263c6525f19a739795b816be141e21a9f9b3aaccddf4f8265'
GRANT={'path':'pipeline/authorizations/server4_gpu1_20261030.json','sha256':'6529ecf4cb9bc39c698650e3116df67870a2f82e76c046296c8a1e74aa0d68c2'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def write(name,value):
 p=HERE/name
 if p.exists():raise RuntimeError('Do not overwrite '+name)
 p.write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert not (HERE/'adapter.py').exists()
old=json.loads((OLD/'preparation.json').read_text(encoding='utf-8'))
assert sha(OLD/'adapter.py')=='7253f131dd3f8e5d104e800d49dfa1907df8aa9ec0ffb3d76535a7efe2c9d9cf'
assert sha(OLD/'remote_ops.py')=='37d7b75d853b601b177668b34349ae24dc3570402c914c2cdcadb1931db1418d'
assert sha(NATIVE/'preparation.json')=='173e5f02eaabfa02c37ad71646f9f136d9655a771aa3baf9b4382c6b3a90da77'
assert sha(ROOT/'SERVERS.yaml')==SERVERS_SHA and sha(ROOT/GRANT['path'])==GRANT['sha256']
source=(OLD/'adapter.py').read_text(encoding='utf-8')
changes=[
 ("RESOURCE_AUTHORIZATION = {'path':'pipeline/authorizations/server4_gpu0_only_20261026.json','sha256':'94075ebd59f352b98209c9572faa5ea0cb260178645e067b5d01b1602ea7da09'}",
  "RESOURCE_AUTHORIZATION = "+repr(GRANT)+"\nSERVERS_POLICY_SHA256 = '"+SERVERS_SHA+"'\nPOLICY_GPU_UUIDS = {0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}"),
 ("'Current explicit GPU0-only authorization changed'","'Current explicit retained-GPU0 plus GPU1 resource authorization changed'"),
 ("        server=yaml.safe_load((self.root/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']",
  "        require(sha(self.root/'SERVERS.yaml')==SERVERS_POLICY_SHA256,'Current exact SERVERS resource policy changed')\n        server=yaml.safe_load((self.root/'SERVERS.yaml').read_text(encoding='utf-8'))['servers']['server-4']"),
 ('all(type(g) is int and g in GPU_UUIDS for g in allowed)','all(type(g) is int and g in POLICY_GPU_UUIDS for g in allowed)'),
 ("'GPU whitelist is unknown or outside this GPU0-only packet'","'GPU whitelist is unknown or outside the current exact resource policy'"),
 ("require(allowed==[0],'This SFC packet supports only current GPU0 authorization')","require(allowed==[0,1],'This SFC policy copy requires exact current [0,1] authorization; selected capability remains GPU0 only')"),
 ('all(uuids.get(str(g))==GPU_UUIDS[g] for g in allowed)','all(uuids.get(str(g))==POLICY_GPU_UUIDS[g] for g in allowed)')]
for before,after in changes:
 assert source.count(before)==1,before
 source=source.replace(before,after,1)
compile(source,'private policy-compatible adapter','exec');(HERE/'adapter.py').write_text(source,encoding='utf-8',newline='\n')
(HERE/'remote_ops.py').write_bytes((OLD/'remote_ops.py').read_bytes())
release=json.loads((OLD/'release_template.json').read_text(encoding='utf-8'))
release['source_hashes']={n:sha(HERE/n) for n in ('adapter.py','remote_ops.py')}
release['selection_scope']='Current live policy is exact allowed[0,1]/max_tasks_per_gpu1; this packet can explicitly select only physicalGPU0. No GPU1 selection, fallback, old-binding replay or eviction. Fresh owner, actual idle/card UUID, parent receipt and three locks remain mandatory.'
release['resource_policy']={'SERVERS_sha256':SERVERS_SHA,'authorization':GRANT,'live_allowed_gpus':[0,1],'selected_GPU_capability':[0],'max_tasks_per_gpu':1}
write('release_template.json',release)
def functions(t):
 out={}
 for n in t.body:
  if isinstance(n,ast.FunctionDef):out[n.name]=ast.dump(n,include_attributes=False)
  elif isinstance(n,ast.ClassDef):out.update({n.name+'.'+m.name:ast.dump(m,include_attributes=False) for m in n.body if isinstance(m,ast.FunctionDef)})
 return out
a=functions(ast.parse((OLD/'adapter.py').read_text(encoding='utf-8')));b=functions(ast.parse(source))
assert a.keys()==b.keys();changed=[k for k in a if a[k]!=b[k]];assert changed==['Adapter.guard'],changed
write('policy_port_provenance.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'reference_operational_preparation':ref(OLD/'preparation.json'),
 'reference_module_hashes':{n:sha(OLD/n) for n in ('adapter.py','remote_ops.py')},'ordered_literal_changes':[{'before':x,'after':y} for x,y in changes],
 'actual_changed_function_ASTs':changed,'all_other_adapter_function_ASTs_exact':True,'remote_ops_byte_identical':sha(HERE/'remote_ops.py')==sha(OLD/'remote_ops.py'),
 'native_preparation':ref(NATIVE/'preparation.json'),'native_worker':ref(NATIVE/'worker.py'),'unchanged_native_manifest_template':ref(NATIVE/'manifest_template.json'),
 'scope':'Resource policy compatibility only. Original GPU0 selected-capability predicates/remote PHYSICAL_GPU0, source9/native173e/worker/protocol/data/science/three-lock/RPC/owner/deadline/parentreceipt/replay code unchanged. New global whitelist uses separate POLICY map0,1. No active directory/lease/productionrelease/native run.'})
print(json.dumps({'adapter':sha(HERE/'adapter.py'),'remote':sha(HERE/'remote_ops.py'),'release':sha(HERE/'release_template.json'),'changed_functions':changed}))
