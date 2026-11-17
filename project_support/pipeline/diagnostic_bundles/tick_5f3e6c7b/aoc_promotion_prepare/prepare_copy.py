"""Private current-owner copy of frozen AOC R1 promotion templates; no entry execution."""
from pathlib import Path
from datetime import datetime,timezone
import ast,difflib,hashlib,json
ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
ORIGIN=ROOT/'pipeline/diagnostic_bundles/tick_f8d84d12/aoc_promotion_prepare_r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):(HERE/name).write_text(json.dumps(value,indent=2,allow_nan=False)+'\n',encoding='utf-8')
assert sha(ORIGIN/'preparation.json')=='38abf859f7ba669238f45a46c7cee654020be05b690caa60b5b0ad240d49522c'
old=json.loads((ORIGIN/'preparation.json').read_text(encoding='utf-8'))
for name,expected in old['prepared_file_hashes'].items():assert sha(ORIGIN/name)==expected,name
anchor=ast.parse((HERE.parent/'anchor.py').read_text(encoding='utf-8'))
owner=next(ast.literal_eval(n.value) for n in anchor.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='EXPECTED' for t in n.targets))
files=['aoc_evidence.py','summarize_aoc_actual.py','fast_forward_tested_aoc.py','admit_aoc_queue.py','dispatch_aoc_once.py','source_bindings.json','evidence_bindings.json']
changes={};checks=[]
for name in files:
    before=(ORIGIN/name).read_bytes();after=before
    if name=='admit_aoc_queue.py':
        text=before.decode('utf-8');assert text.count(old['prepared_for_owner']['token'])==1
        after=text.replace(old['prepared_for_owner']['token'],owner['token']).encode('utf-8')
    if name=='dispatch_aoc_once.py':
        text=before.decode('utf-8');assert text.count('.f8d84d12.dispatch.tmp')==1
        after=text.replace('.f8d84d12.dispatch.tmp','.5f3e6c7b.dispatch.tmp').encode('utf-8')
    (HERE/name).write_bytes(after)
    if name.endswith('.py'):compile(after.decode('utf-8'),name,'exec')
    changes[name]={'origin_sha256':hashlib.sha256(before).hexdigest(),'new_sha256':hashlib.sha256(after).hexdigest(),
        'byte_identical':before==after,'exact_diff':''.join(difflib.unified_diff(before.decode('utf-8').splitlines(keepends=True),after.decode('utf-8').splitlines(keepends=True),fromfile='origin/'+name,tofile='current/'+name))}
    checks.append({'name':'exact_metadata_copy_'+name,'passed':True})
evidence=json.loads((HERE/'evidence_bindings.json').read_text(encoding='utf-8'))
assert all(evidence[k] is None for k in ('independent_review','actual_four_result_review','actual_raw_results'))
assert (HERE/'aoc_evidence.py').read_text(encoding='utf-8').count('DRAFT_EXECUTION_DISABLED=True')==1
assert "['shapes']" in (HERE/'aoc_evidence.py').read_text(encoding='utf-8')
checks.extend([{'name':'DRAFT_true_and_three_actual_refs_NULL','passed':True},{'name':'R1_common_shapes_key_preserved','passed':True}])
save('port_provenance.json',{'origin_preparation':ref(ORIGIN/'preparation.json'),'origin_schema_correction_history':old.get('superseded_static_interface_failure'),
    'current_owner':owner,'changes':changes,'scope':'Only admit literal currentowner token and dispatcher temp suffix differ; five helper numerical/evidence/canonical safety contracts otherwise unchanged. Dynamic SCRIPT.parent resolves new current tick. Source bindings remain original real0314/base9c/native9cf/op e45/proto a041; actual evidence refs remainNone. No generic substring replacement.',
    'new_source_model_or_revision':False,'actual_native_or_promotion_performed':False})
(HERE/'README.md').write_text('''# Current-owner AOC promotion templates (disabled)

The five helpers are copied from frozen tick_f8d84d12/aoc_promotion_prepare_r1 (38ab), which already retains the corrected `shapes` common-parameter key. Only the ordinary-training owner-token assertion and dispatcher temp suffix are rebound to this current tick. All other helper bytes and source_bindings/evidence_bindings bytes match that R1 source. Original0314/base9c/native9cf/op e45/prototypef7/protocol a041 remain unchanged.

Common DRAFT is True and actual raw/local review/independent peer references are null. No result is pre-signed. Root's separate default-readonly bind_aoc_actual_review.py can make one private active copy only after four real current terminal rc0 envelopes and a real SHA-bound independent semantic review, with exact current owner/manifest/lease/source. It must leave this template untouched; its only active common change is True→False plus actual evidence JSON, journaled before exclusive destination creation. Partial copies are reconciled read-only, never blindly repeated.

Root must capture protected_assets_before.json after real PES canonical terminal archival and before summary/ff/admission, while primary still9c, index empty and the original28 files unchanged. The helpers use that fresh current-tick baseline and a fresh complete lifecycle capture from the summary; no old running/earlystop assumption is rebound. Sequence after actual binding: summary → exact9A ff9c→0314 → canonical admission/receipt/FIFO waiting → one canonical GPU0 dispatch. Each mutation retains real current owner/original deadline/auth/locks and once-intent/no-replay checks. No GPU1, extra scientific gate, PES4E schema or training-exclusive field is introduced.

Only private copying/compile/AST checks occurred here. No helper entry, native/SSH/Git/shared write, receipt, queue or launch was executed.
''',encoding='utf-8',newline='\n')
save('static_validation.json',{'status':'PASS_CURRENT_METADATA_COPY_ONLY_NOT_NATIVE_OR_PROMOTION','recorded_at':datetime.now(timezone.utc).isoformat(),'checks':checks,'check_count':len(checks),'helpers_imported_or_executed':False,'native_SSH_GPU_Git_shared_operation':False})
prepared={p.name:sha(p) for p in sorted(HERE.iterdir()) if p.is_file() and p.name!='preparation.json'}
packet={key:old[key] for key in ('schema_version','candidate_id','experiment_id','code_commit','source_parent_commit')}
packet.update(status='DISABLED_CURRENT_OWNER_AOC_PROMOTION_TEMPLATES_NOT_NATIVE_PASS',recorded_at=datetime.now(timezone.utc).isoformat(),
    prepared_for_owner=owner,origin_preparation=ref(ORIGIN/'preparation.json'),source_bindings=ref(HERE/'source_bindings.json'),evidence_bindings=ref(HERE/'evidence_bindings.json'),
    actual_independent_review=None,actual_four_result_review=None,actual_raw_results=None,draft_execution_disabled=True,
    native_resources_standards_admission_queue_launch='NOT_RUN_NOT_CREATED_BY_THIS_COPY',static_validation=ref(HERE/'static_validation.json'),
    port_provenance=ref(HERE/'port_provenance.json'),actual_software_checks_count=len(checks),material_concerns=[],prepared_file_hashes=prepared)
save('preparation.json',packet)
print(json.dumps({'preparation':ref(HERE/'preparation.json'),'files':{name:sha(HERE/name) for name in files},'copy_checks':len(checks)}))
