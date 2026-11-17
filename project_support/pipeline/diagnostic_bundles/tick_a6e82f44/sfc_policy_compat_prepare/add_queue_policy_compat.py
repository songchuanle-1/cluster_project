"""Preserve initial private draft, then distinguish policy-valid other-card reservations."""
from pathlib import Path
import ast,hashlib,json
HERE=Path(__file__).resolve().parent
OLD=Path('D:/project/cluster_project/pipeline/diagnostic_bundles/tick_928313fd/sfc_operational_prepare')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=HERE/'adapter.py';assert sha(p)=='6187cbf6f4a17d4a92b47d78645367f8fc4c0168fbc9ed7b6c3cdff52a0d3d22'
for src,dst in [('adapter.py','adapter.initial_policy_only.py.txt'),('policy_port_provenance.json','policy_port_provenance.initial.json'),('release_template.json','release_template.initial.json')]:
 target=HERE/dst;assert not target.exists();target.write_bytes((HERE/src).read_bytes())
before="require((type(value) is int and value in GPU_UUIDS) or (type(value) is str and value in ('0',)),'Active queue GPU is malformed/unknown')"
after="require((type(value) is int and value in POLICY_GPU_UUIDS) or (type(value) is str and value in ('0','1')),'Active queue GPU is malformed/unknown')"
s=p.read_text(encoding='utf-8');assert s.count(before)==1;s=s.replace(before,after,1);compile(s,str(p),'exec');p.write_text(s,encoding='utf-8',newline='\n')
pr=json.loads((HERE/'policy_port_provenance.json').read_text(encoding='utf-8'));pr['ordered_literal_changes'].append({'before':before,'after':after})
pr.update(actual_changed_function_ASTs=['Adapter.guard','Adapter._local_idle'],all_other_adapter_function_ASTs_exact=True,
          initial_private_draft_preserved=['adapter.initial_policy_only.py.txt','policy_port_provenance.initial.json','release_template.initial.json'],
          queue_policy_scope='An active queue reservation on currently authorized physical1 is recognized and does not reserve selected0. Unknown/bool/malformed assignments still refuse; any active/pending/uncertain selected0 assignment still refuses. No GPU1 compute capability is added.',
          native_manifest_policy='Native runtime1d635 has UUID map0+1 and hard PHYSICAL_GPU==0; unchanged prepare/binding retains liveallowed[0,1] in manifest and lease. No diagnostic-subset rewriting is needed.')
(HERE/'policy_port_provenance.json').write_text(json.dumps(pr,indent=2,allow_nan=False)+'\n',encoding='utf-8')
release=json.loads((HERE/'release_template.json').read_text(encoding='utf-8'));release['source_hashes']['adapter.py']=sha(p)
(HERE/'release_template.json').write_text(json.dumps(release,indent=2,allow_nan=False)+'\n',encoding='utf-8')
print(json.dumps({'adapter':sha(p),'remote':sha(HERE/'remote_ops.py'),'release':sha(HERE/'release_template.json')}))
