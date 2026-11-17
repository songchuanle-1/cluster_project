"""Private exact-literal binder port. Never invokes the binder or reads actual results."""
from pathlib import Path
from datetime import datetime,timezone
import ast,difflib,hashlib,json
ROOT=Path('D:/project/cluster_project')
TICK=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_14fea205/bind_pes_actual_review.py'
SOURCE=TICK/'aoc_promotion_prepare'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(TICK/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert sha(SOURCE/'preparation.json')=='a1c707ce1f24a08c89550ee4a423e7dced2eaac3a77fda549010716d7296d308'
before=ORIGIN.read_text(encoding='utf-8');after=before
literals=[
    ("tick_14fea205')","tick_5f3e6c7b')"),
    ("'pes_promotion_prepare'","'aoc_promotion_prepare'"),("'pes_admission_active'","'aoc_admission_active'"),("'pes_execution'","'aoc_execution'"),
    ("SOURCE_SHA='1c7874c4c626c36fb65f32b466c6a5bee1f36aaefa73f30ff3cd57cf158decae'","SOURCE_SHA='a1c707ce1f24a08c89550ee4a423e7dced2eaac3a77fda549010716d7296d308'"),
    ("MANIFEST_SHA='d7ee1780c08ba1faffdaea28e12b78d2bbaf2ee4380533bb20ac7878dfb6456b'","MANIFEST_SHA=None"),
    ("LEASE_SHA='4a1d7552730d494589be8ca9781a36ad06d950818a4db4c21a9c173c914b0b8b'","LEASE_SHA=None"),
    ("CID='hierarchy-palindromic-euler-state-composition'","CID='hierarchy-ancestral-order-commutator-composition'"),
    ("CODE='9c42fdc4e9168acec18980d782ee9c163e043bb7'","CODE='0314b932a92a8cc7f67804068ecb1c1f7a5f2e33'"),
    ("BASE='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391'","BASE='9c42fdc4e9168acec18980d782ee9c163e043bb7'"),
    ('FOUR_ACTUAL_PES_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED','FOUR_ACTUAL_AOC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'),
    ('pes_evidence.py','aoc_evidence.py'),('summarize_pes_actual.py','summarize_aoc_actual.py'),('fast_forward_tested_pes.py','fast_forward_tested_aoc.py'),
    ('admit_pes_queue.py','admit_aoc_queue.py'),('dispatch_pes_once.py','dispatch_aoc_once.py'),
    ('pes_actual_independent_review.json','aoc_actual_independent_review.json'),('pes_active_binding_intent.json','aoc_active_binding_intent.json'),('pes_active_binding_result.json','aoc_active_binding_result.json')]
for old,new in literals:
    assert old in after,old
    after=after.replace(old,new)
# Manifest/lease bytes do not exist at authoring. Root must supply their real hashes.
after=after.replace('def check_actual(peer_sha):','def check_actual(peer_sha,manifest_sha,lease_sha):')
begin=after.index('def check_actual(');end=after.index('\ndef main():',begin)
block=after[begin:end].replace('MANIFEST_SHA','manifest_sha').replace('LEASE_SHA','lease_sha')
after=after[:begin]+block+after[end:]
needle="    args=ap.parse_args()"
after=after.replace(needle,"    ap.add_argument('--manifest-sha256',default=None)\n    ap.add_argument('--lease-sha256',default=None)\n"+needle)
needle="    guard();assert sys.dont_write_bytecode"
after=after.replace(needle,"    assert all(isinstance(v,str) and re.fullmatch('[0-9a-f]{64}',v) for v in (args.manifest_sha256,args.lease_sha256)),'Real current manifest and lease SHA arguments required'\n"+needle)
after=after.replace('peer,raws=check_actual(args.independent_review_sha256)','peer,raws=check_actual(args.independent_review_sha256,args.manifest_sha256,args.lease_sha256)')
assert 'pes_evidence' not in after and 'PES_NATIVE' not in after and 'tick_14fea205' not in after
compile(after,'bind_aoc_actual_review.py','exec')
(TICK/'bind_aoc_actual_review.py').write_text(after,encoding='utf-8',newline='\n')
tree=ast.parse(after);main=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='main')
checks={'binder_compiles_without_import':True,'default_returns_before_any_guard_raw_or_copy':"if not args.execute_root:\n        print('DEFAULT_READ_ONLY_NO_BINDING_COPY_OR_PROMOTION');return" in after,
    'peer_manifest_lease_hashes_not_prefilled':'MANIFEST_SHA=None' in after and 'LEASE_SHA=None' in after and all(s in after for s in ("'--manifest-sha256',default=None","'--lease-sha256',default=None","'--peer-sha256'")),
    'requires_exact_current_four_terminal_success_and_peer':all(s in after for s in ("envelope['certainty']=='terminal'", "envelope['returncode']==0", "raw['execution_completed'] is True", "peer['material_concerns']==[]", "len(set(request_ids))==4", "b['owner']==EXPECTED and set(b['owner'])==set(EXPECTED)")),
    'only_common_flag_and_actual_evidence_copy':'DRAFT_EXECUTION_DISABLED=True' in after and 'DRAFT_EXECUTION_DISABLED=False' in after and "files['evidence_bindings.json']=encoded(evidence)" in after,
    'durable_intent_no_replay_project_lock_and_finally_close':all(s in after for s in ("not DEST.exists() and not intent.exists() and not result.exists()","write_new(intent",'mon.acquire_lock(str(ROOT))','finally:lock.close()')),
    'all_payload_composed_before_first_intent':after.index("files['activation_binding.json']=encoded(metadata)")<after.index('write_new(intent'),
    'no_subprocess_Git_SSH_native_or_dispatch_call':not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and isinstance(n.func.value,ast.Name) and n.func.value.id=='subprocess' for n in ast.walk(tree))}
assert all(checks.values())
save('aoc_actual_review_binder_preparation.json',{'schema_version':1,'status':'DEFAULT_READONLY_AOC_ACTUAL_REVIEW_BINDER_DRAFT_NOT_EXECUTED',
    'recorded_at':datetime.now(timezone.utc).isoformat(),'candidate_id':'hierarchy-ancestral-order-commutator-composition','code_commit':'0314b932a92a8cc7f67804068ecb1c1f7a5f2e33',
    'source_disabled_preparation':ref(SOURCE/'preparation.json'),'reference_successful_binder':ref(ORIGIN),'binder':ref(TICK/'bind_aoc_actual_review.py'),
    'actual_independent_review':None,'actual_raw_results':None,'actual_manifest_sha256':None,'actual_lease_sha256':None,
    'default_no_binding_or_promotion':True,'checks':checks,'check_count':len(checks),'literal_changes':literals,
    'necessary_interface_change':'Actual future manifest/lease hashes are mandatory explicit CLI inputs, rather than historical PES constants. Peer SHA remains mandatory. Default returns before reading actual result files.',
    'exact_diff':''.join(difflib.unified_diff(before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile='original_successful_PES_binder',tofile='current_AOC_binder')),
    'expected_command':'python -B pipeline/diagnostic_bundles/tick_5f3e6c7b/bind_aoc_actual_review.py --execute-root --peer-sha256 <actualMDCsha> --manifest-sha256 <actualManifestsha> --lease-sha256 <actualLeasesha>',
    'output_directory':'pipeline/diagnostic_bundles/tick_5f3e6c7b/aoc_admission_active','actualrequest_result_shared_Git_SSH_GPU_or_helper_entry_executed':False,'material_concerns':[]})
print(json.dumps({'binder':ref(TICK/'bind_aoc_actual_review.py'),'preparation':ref(TICK/'aoc_actual_review_binder_preparation.json'),'checks':len(checks)}))
