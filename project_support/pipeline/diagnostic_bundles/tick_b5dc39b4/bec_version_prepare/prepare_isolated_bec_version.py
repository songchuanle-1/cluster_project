"""Disabled BEC source-version save draft; no primary/runtime promotion or native run.

Root must independently review/materialize this draft, provide the actual current
BFC admission SHA, and use --execute-root. No default code path invokes Git.
"""
from pathlib import Path
from datetime import datetime,timezone
import argparse
import hashlib
import json
import os
import re
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
REPO=ROOT/'Cluster'
HERE=Path(__file__).resolve().parent
DEST=ROOT/'pipeline/isolated_versions/bec_b5dc39b4'
OLD=ROOT/'pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CID='hierarchy-cross-level-bipartite-edge-composition'
EXP='M215-BEC'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bec'
CONFIG='configs/Quard/ctf_hcg_csort_bec/'+MODEL+'.yaml'
BASE='48fc302c3c02ffef0b241be3593c386b6b65a72e'
PRIMARY=BASE
SOURCE_REFERENCE='48fc302c3c02ffef0b241be3593c386b6b65a72e'
BFC_PARENT='11a811618179ab1ddc0cee299194667413b7fdb9'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
SOURCE_PREP_SHA='2d0606030583fd29719a39a114e11c1c31f44b63ca0fa2cff849baf40e7ca14d'
NATIVE_PROTOCOL_SHA='655591ddcdb017461884381fb27d006e9ba3062f530b9bb6f44dc7dc85466a10'
TOKEN='b5dc39b4780a44c6855520bc22692b65'
EXPECTED_OWNER={'token': 'b5dc39b4780a44c6855520bc22692b65', 'thread_id': '01a159c5-29ab-7a22-ba7f-e79174757253', 'generated_at': '2026-10-25T22:11:14.827798+00:00', 'deadline_at': '2026-10-25T23:11:14.827798+00:00', 'context_sha256': '7082c7c328d7e20f4ca107f32cd4df7929ffff12427ff0883774f2ec2f217f98', 'pending_sha256': '63ff0e9d20d0877f4a3b4d8a790e1881fac5db412656a9fc83e755eb104f18cf'}
DRAFT_EXECUTION_ENABLED=False
PROTECTED_BASELINE=ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json'
PROTECTED_BASELINE_SHA='deb2f6e1093be710fbbae886b4008c187b2e6b63d63276bfb47706b36b4be142'
REVIEWS=[('pipeline/diagnostic_bundles/tick_6bdbcf77/bec_final_source_review.json',
 '24985d1c6ef3444e63a7b0b949d04b1fe3afb678c27d8f075925c12cf79cb0e1')]
BFC_CID='hierarchy-parent-butterfly-token-composition'
BFC_CONFIG='configs/Quard/ctf_hcg_csort_bfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc.yaml'
BFC_SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4/new_candidate_prepare'
BFC_SOURCE_SHA='8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501'
BFC_RECEIPT=ROOT/'pipeline/admissions/M213-BFC.json'
BFC_INDEPENDENT_STATUS='FOUR_ACTUAL_BFC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
BFC_EVIDENCE_TICK='pipeline/diagnostic_bundles/tick_336ca5d7/'
BFC_RECEIPT_SHA='812454a819702e8f4d53080c1b479617d605f2175bf44a3422905688253ca01c'
CTS_COMMIT='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
CTS_REPO=ROOT/'pipeline/isolated_versions/cts_336ca5d7'
CTS_VERSION_PROOF=ROOT/'pipeline/diagnostic_bundles/tick_336ca5d7/cts_version_execute/isolated_source_version.json'
CTS_VERSION_PROOF_SHA='6b666a8c8e9d0f5bed8422fa02e6e2ea17192b1114c6eda5ecf28affb409c2d0'
FROZEN_NATIVE=ROOT/'pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare'
FROZEN_NATIVE_PREP_SHA='322c8ce812ffccda6cfa3d6d2d6e1dd8f73859ab5d3a9835d0c1110328c3e3ff'
OPTIONAL_LEDGER_NAMES=['experiments/M214-CTS.json','admissions/M214-CTS.json','experiments/M215-BEC.json','admissions/M215-BEC.json']
PAIRS={('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')}
PROTECTED_LEDGER_NAMES=['queue.json','running.json','research_work.json',
 'experiments/M206-CGCA.json','experiments/M207-HAP.json','experiments/M210-PSNC.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M213-BFC.json',
 'admissions/M210-PSNC.json','admissions/M211-BTC.json','admissions/M212-BCR.json','admissions/M213-BFC.json']

def require(value,message):
    if not value:raise RuntimeError(message)
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':Path(p).relative_to(ROOT).as_posix(),'sha256':sha(p)}
def artifact(entry):
    require(isinstance(entry,dict) and set(entry)=={'path','sha256'},'Exact artifact path/SHA required')
    require(isinstance(entry['path'],str) and isinstance(entry['sha256'],str) and re.fullmatch(r'[0-9a-f]{64}',entry['sha256']),'Invalid artifact identity')
    p=(ROOT/entry['path']).resolve();require(p.is_relative_to(ROOT.resolve()) and sha(p)==entry['sha256'],'Artifact identity/path mismatch');return p

def git(repo,*args):
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_LFS_SKIP_SMUDGE='1')
    result=subprocess.run(['git','--no-optional-locks','-c','core.autocrlf=false','-c','core.eol=lf',
       '-c','core.fsmonitor=false','-c','submodule.recurse=false','-C',str(repo),*args],capture_output=True,timeout=90,env=env)
    require(result.returncode==0,result.stderr.decode('utf-8',errors='replace'));return result.stdout

def save(name,data):
    with (HERE/name).open('x',encoding='utf-8') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())

def owner_guard():
    require(set(EXPECTED_OWNER)=={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'},'Owner schema changed')
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json');mode=read(ROOT/'pipeline/execution_mode.json')
    require({k:owner.get(k) for k in EXPECTED_OWNER}==EXPECTED_OWNER,'Actual current owner identity changed')
    require(mode['mode']=='foreground' and mode['target_thread_id']==os.environ.get('CODEX_THREAD_ID')==EXPECTED_OWNER['thread_id'],'Actual task is not the foreground owner')
    require(datetime.now(timezone.utc)<datetime.fromisoformat(EXPECTED_OWNER['deadline_at']),'Original deadline expired')
    require(sha(ROOT/'pipeline/headless/.tick_context.json')==EXPECTED_OWNER['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==EXPECTED_OWNER['pending_sha256'],'Snapshot changed')
    require(sha(ROOT/'pipeline/goal.json')==GOAL,'Goal changed');return owner

def source_details():
    require(sha(OLD/'preparation.json')==SOURCE_PREP_SHA and sha(OLD/'native_protocol.md')==NATIVE_PROTOCOL_SHA,'Frozen BEC preparation/protocol changed')
    source=read(OLD/'preparation.json')
    require((source['candidate_id'],source['experiment_id'])==(CID,EXP),'BEC source identity differs')
    require(source['code_commit'] is None and source['source_commit'] is None and source['future_version_parent'] is None,'Do not rewrite/reuse a versioned source packet')
    require(source['base_reference_commit']==SOURCE_REFERENCE and source['source_file_count']==9,'Wrong historical source reference/count')
    for name,h in source['prepared_file_hashes'].items():
        p=(OLD/name).resolve();require(p.is_relative_to(OLD.resolve()) and sha(p)==h,'Frozen BEC prepared file differs')
    for name,h in REVIEWS:
        p=ROOT/name;require(sha(p)==h,'BEC independent review changed');review=read(p)
        require(review['candidate_id']==CID and review['material_concerns']==[] and review['anchors']['source_preparation']==ref(OLD/'preparation.json') and review['anchors']['native_protocol']==ref(OLD/'native_protocol.md'),'BEC independent review binding differs')
    frozen={name.removeprefix('staged_repository/'):h for name,h in source['prepared_file_hashes'].items() if name.startswith('staged_repository/')}
    names={'__init__.py','backbone.py','dec.py','hier_postprocess.py','loss.py','bipartite_edges.py','network.py','sample_model.py'}
    require(set(frozen)=={'framework/model/Quard_model/'+MODEL+'/'+n for n in names}|{CONFIG},'Only exact BEC8+nativeYAML allowed')
    return frozen

def primary_snapshot():
    require(sha(PROTECTED_BASELINE)==PROTECTED_BASELINE_SHA,'Protected28 baseline changed')
    baseline=read(PROTECTED_BASELINE)['protected_existing_worktree'];require(len(baseline)==28,'Protected28 inventory differs')
    raw=git(REPO,'status','--porcelain=v1','-z','--untracked-files=all');rows=[r for r in raw.split(b'\0') if r]
    require(all(b'R' not in r[:2] and b'C' not in r[:2] for r in rows),'Rename/copy status needs review')
    require({(r[:2].decode(),r[3:].decode()) for r in rows}=={(r['status'],r['path']) for r in baseline},'Protected28 status set changed')
    files={}
    for row in baseline:
        name=row['path'];p=(REPO/name).resolve();require(p.is_relative_to(REPO.resolve()) and p.is_file(),'Protected path escaped/missing')
        files[name]=sha(p);require(files[name]==row['sha256'],'Protected28 bytes changed')
    require(not git(REPO,'diff','--cached','--name-only','-z'),'Primary index has staged changes')
    index=Path(git(REPO,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=REPO/index
    return {'HEAD':git(REPO,'rev-parse','HEAD').decode().strip(),'status_hex':raw.hex(),'index_sha256':sha(index),'protected_files':files}

def bfc_tested_primary_gate(admission_sha):
    require(isinstance(admission_sha,str) and re.fullmatch(r'[0-9a-f]{64}',admission_sha),'Actual formal BFC admission SHA required; no placeholder')
    require(admission_sha==BFC_RECEIPT_SHA and sha(BFC_RECEIPT)==admission_sha,'Formal BFC receipt changed/missing')
    receipt=read(BFC_RECEIPT)
    require((receipt['id'],receipt['candidate_id'],receipt['code_commit'],receipt['config'],receipt['goal_sha256'])==('M213-BFC',BFC_CID,BASE,BFC_CONFIG,GOAL),'Formal tested BFC receipt identity differs')
    created=datetime.fromisoformat(receipt['created_at']);require(created.tzinfo is not None and created<=datetime.now(timezone.utc),'Known tested BFC admission has an invalid creation time')
    independent_path=artifact(receipt['independent_review']);require(receipt['independent_review']['path'].startswith(BFC_EVIDENCE_TICK),'BFC review does not bind the original tested native tick')
    independent=read(independent_path)
    require(independent['status']==BFC_INDEPENDENT_STATUS and independent['material_concerns']==[],'Actual BFC native/resource independent review not passed')
    require((independent['candidate_id'],independent['code_commit'],independent['goal_sha256'])==(BFC_CID,BASE,GOAL),'Actual BFC review identity differs')
    raws=independent['raw_results'];require(len(raws)==4 and {(x['mode'],x['target']) for x in raws}==PAIRS,'Exactly four actual BFC arms required')
    for row in raws:
        require(row['execution_path'].startswith(BFC_EVIDENCE_TICK+'bfc_execution/'),'Do not relabel old raw results')
        artifact({'path':row['execution_path'],'sha256':row['execution_sha256']})
    queue=read(ROOT/'pipeline/queue.json');matches=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')=='M213-BFC']
    require(len(matches)<=1,'Ambiguous BFC queue identity')
    task=matches[0] if matches else read(ROOT/'pipeline/experiments/M213-BFC.json')
    require(task.get('code_commit')==BASE and task.get('admission_receipt')==BFC_RECEIPT.relative_to(ROOT).as_posix(),'BFC task/receipt identity differs')
    if not matches:require(task.get('status') in ('done_complete','done_earlystop') and task.get('launch_verified') is True,'Missing current admitted BFC task')
    sys.path.insert(0,str(SKILL));import closure
    closure.admission(str(ROOT),task,completed=not bool(matches))
    require(git(REPO,'rev-parse','HEAD').decode().strip()==BASE,'Actual primary is not tested48fc; refuse to guess parent')
    require(git(REPO,'rev-list','--parents','-n','1',BASE).decode().split()==[BASE,BFC_PARENT],'Tested BFC parent/commit differs')
    require(sha(BFC_SOURCE/'preparation.json')==BFC_SOURCE_SHA,'BFC tested source preparation differs')
    bfc=read(BFC_SOURCE/'preparation.json');frozen={n.removeprefix('staged_repository/'):h for n,h in bfc['prepared_file_hashes'].items() if n.startswith('staged_repository/')};require(len(frozen)==9,'Wrong BFC source count')
    require(sorted(git(REPO,'diff-tree','--no-commit-id','--name-status','-r',BASE).decode().splitlines())==sorted('A\t'+n for n in frozen),'Tested primary48fc must be exactly BFC9A')
    require({n:hashlib.sha256(git(REPO,'show',BASE+':'+n)).hexdigest() for n in frozen}==frozen,'Actual primary BFC blobs differ from tested source')
    return {'formal_admission':ref(BFC_RECEIPT),'independent_review':receipt['independent_review'],'actual_primary_HEAD':BASE,'tested_BFC_nine_blobs_exact':True}

def git_hooks_filters_guard():
    result=subprocess.run(['git','-c','core.fsmonitor=false','-C',str(REPO),'config','--get-regexp',r'^(core\.hooksPath|filter\..*)$'],capture_output=True,timeout=20)
    require(result.returncode in (0,1),'Cannot inspect Git hook/filter configuration')
    configured=dict(row.split(' ',1) for row in result.stdout.decode().splitlines())
    allowed={'filter.lfs.clean':'git-lfs clean -- %f','filter.lfs.smudge':'git-lfs smudge -- %f','filter.lfs.process':'git-lfs filter-process','filter.lfs.required':'true'}
    require(all(k in allowed and allowed[k]==v for k,v in configured.items()),'Nonstandard Git hook/filter needs review')
    hooks=Path(git(REPO,'rev-parse','--git-path','hooks').decode().strip())
    if not hooks.is_absolute():hooks=REPO/hooks
    require(not hooks.exists() or not any(p.is_file() and not p.name.endswith('.sample') for p in hooks.iterdir()),'Active Git hooks need review')


def lifecycle_snapshot():
    result={}
    for name in PROTECTED_LEDGER_NAMES+OPTIONAL_LEDGER_NAMES:
        p=ROOT/'pipeline'/name
        result[name]={'exists':p.is_file(),'sha256':sha(p) if p.is_file() else None}
    require(all(result[n]['exists'] for n in PROTECTED_LEDGER_NAMES),'Missing established lifecycle/receipt ledger')
    return result


def frozen_native_snapshot():
    p=FROZEN_NATIVE/'preparation.json';require(sha(p)==FROZEN_NATIVE_PREP_SHA,'Frozen native322c preparation changed')
    prep=read(p)
    require(prep['candidate_id']==CID and prep['code_commit'] is None and prep['source_commit'] is None and prep['source_parent_commit'] is None and prep['future_version_parent'] is None and prep['draft_execution_disabled'] is True,'Do not bind or enable the old native draft')
    files={name:sha(FROZEN_NATIVE/name) for name in prep['prepared_file_hashes']}
    require(files==prep['prepared_file_hashes'],'Frozen native payload changed')
    require(all(v is None for v in prep['manifest_execution_fields'].values()),'Old native draft acquired active fields')
    return {'preparation':ref(p),'prepared_file_hashes':files,'code_commit':None,'source_parent_commit':None,'draft_execution_disabled':True}


def cts_snapshot():
    require(sha(CTS_VERSION_PROOF)==CTS_VERSION_PROOF_SHA,'Pending CTS version proof changed')
    proof=read(CTS_VERSION_PROOF)
    require(proof['candidate_id']=='hierarchy-parent-cyclic-triadic-state-composition' and proof['code_commit']==CTS_COMMIT and proof['parent_commit']==BASE and Path(proof['worktree']).resolve()==CTS_REPO.resolve(),'Pending CTS identity changed')
    require(git(CTS_REPO,'rev-parse','HEAD').decode().strip()==CTS_COMMIT,'CTS worktree HEAD changed')
    require(git(CTS_REPO,'rev-list','--parents','-n','1',CTS_COMMIT).decode().split()==[CTS_COMMIT,BASE],'CTS is not the preserved sibling source')
    status=git(CTS_REPO,'status','--porcelain=v1','-z','--untracked-files=all');require(not status,'Pending CTS worktree is dirty; never reset/stash it')
    require(not git(CTS_REPO,'diff','--cached','--name-only','-z'),'Pending CTS index has staged changes')
    frozen=proof['frozen_source_files'];require(len(frozen)==9,'Pending CTS9 inventory differs')
    blobs={n:hashlib.sha256(git(CTS_REPO,'show',CTS_COMMIT+':'+n)).hexdigest() for n in frozen}
    require(blobs==frozen and {n:sha(CTS_REPO/n) for n in frozen}==frozen,'Pending CTS committed/working source bytes differ')
    require(sorted(git(CTS_REPO,'diff-tree','--no-commit-id','--name-status','-r',CTS_COMMIT).decode().splitlines())==sorted('A\t'+n for n in frozen),'Pending CTS commit differs from exact9A')
    index=Path(git(CTS_REPO,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=CTS_REPO/index
    return {'HEAD':CTS_COMMIT,'parent':BASE,'status_hex':status.hex(),'index_sha256':sha(index),'committed_blob_sha256':blobs,'working_source_sha256':{n:sha(CTS_REPO/n) for n in frozen},'original_version_proof':ref(CTS_VERSION_PROOF)}


def execute(admission_sha):
    owner_guard();frozen=source_details();require(not DEST.exists() and DEST.resolve().is_relative_to(ROOT.resolve()),'Worktree exists/escapes project')
    require(not (HERE/'isolated_source_version.json').exists() and not (HERE/'isolated_version_operation_intent.json').exists(),'Previous attempt needs exact reconciliation; do not replay')
    policy=read(ROOT/'pipeline/closure_policy.json');grant=policy['experiment_first']['authorization']
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and sha(ROOT/grant['path'])==grant['sha256'],'Current source preparation authorization differs')
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));require(lock is not None,'Canonical project lock busy')
    try:
        bfc=bfc_tested_primary_gate(admission_sha);git_hooks_filters_guard();before=primary_snapshot();require(before['HEAD']==PRIMARY,'Primary HEAD differs')
        require(not(set(frozen)&set(before['protected_files'])),'BEC paths overlap protected worktree')
        for n,h in frozen.items():require(not git(REPO,'ls-tree',BASE,'--',n),'BEC target already tracked');require(not (REPO/n).exists(),'BEC target exists in primary; never overwrite')
        ledgers=lifecycle_snapshot();cts_before=cts_snapshot();native_before=frozen_native_snapshot()
        def mutation_guard():
            owner_guard();require(primary_snapshot()==before,'Primary HEAD/index/status/protected bytes changed before mutation')
            require(lifecycle_snapshot()==ledgers,'Protected lifecycle/receipt bytes changed before mutation')
            require(source_details()==frozen,'Frozen source changed');bfc_tested_primary_gate(admission_sha)
            require(cts_snapshot()==cts_before,'Pending CTS4e8 worktree changed')
            require(frozen_native_snapshot()==native_before,'Frozen unversioned native322c changed')
        save('isolated_version_before.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'primary':before,'protected_ledgers':ledgers,'BFC_actual_tested_primary_precondition':bfc,'pending_CTS_before':cts_before,'frozen_BEC_native_before':native_before})
        mutation_guard();DEST.parent.mkdir(exist_ok=True)
        save('isolated_version_operation_intent.json',{'operation':'git worktree add --detach; copy frozen9; add exact9; ordinary detached commit',
          'worktree':str(DEST),'actual_parent_required':BASE,'source_reference_only':SOURCE_REFERENCE,'remote_operations':False,
          'pending_CTS_commit':CTS_COMMIT,'branch_relationship':'BEC and pending CTS are siblings of48fc; no mainline fast-forward or deployment is authorized',
          'source_preparation':ref(OLD/'preparation.json'),'source_files':frozen,'BFC_actual_tested_primary_precondition':bfc})
        mutation_guard();git(REPO,'worktree','add','--detach',str(DEST),BASE)
        require(not git(DEST,'status','--porcelain=v1','--untracked-files=all').strip(),'Fresh worktree is dirty')
        for n,h in frozen.items():
            p=(DEST/n).resolve();require(p.is_relative_to(DEST.resolve()) and not p.exists(),'Unsafe/existing isolated target');p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as stream:stream.write((OLD/'staged_repository'/n).read_bytes())
            require(sha(p)==h,'Copy differs from frozen source')
        require(not git(DEST,'check-attr','-a','--',*sorted(frozen)).strip(),'Source attributes require review')
        mutation_guard();git(DEST,'add','--',*sorted(frozen))
        require(sorted(git(DEST,'diff','--cached','--name-status').decode().splitlines())==sorted('A\t'+n for n in frozen),'Staged diff is not exact9A')
        require({n:hashlib.sha256(git(DEST,'show',':'+n)).hexdigest() for n in frozen}==frozen,'Staged bytes differ')
        mutation_guard();commit_output=git(DEST,'commit','-m','Add BEC cross-level bipartite edge token composition (native pending)').decode('utf-8',errors='replace')
        commit=git(DEST,'rev-parse','HEAD').decode().strip();require(re.fullmatch(r'[0-9a-f]{40}',commit),'Invalid commit SHA')
        require(git(DEST,'rev-list','--parents','-n','1',commit).decode().split()==[commit,BASE],'BEC is not exact single child of tested actual primary48fc')
        require(not git(DEST,'status','--porcelain=v1','--untracked-files=all').strip(),'Committed isolated worktree is not clean')
        blobs={n:hashlib.sha256(git(DEST,'show',commit+':'+n)).hexdigest() for n in frozen};require(blobs==frozen,'Committed blobs differ')
        require(sorted(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines())==sorted('A\t'+n for n in frozen),'BEC commit contains changes beyond exact9 additions')
        after=primary_snapshot();require(after==before,'Primary changed');require(lifecycle_snapshot()==ledgers,'Protected lifecycle changed')
        require(cts_snapshot()==cts_before,'Pending CTS4e8 worktree changed after source save')
        require(frozen_native_snapshot()==native_before,'Frozen BEC native changed after source save')
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_BEC_SOURCE_COMMIT_ONLY_NATIVE_UNEXECUTED',
          'candidate_id':CID,'experiment_id':EXP,'code_commit':commit,'parent_commit':BASE,'source_reference_only':SOURCE_REFERENCE,
          'worktree':str(DEST),'source_preparation':ref(OLD/'preparation.json'),'frozen_source_files':frozen,'committed_blob_sha256':blobs,
          'primary_Cluster_HEAD':PRIMARY,'primary_HEAD_index_status_28_protected_bytes_unchanged':True,
          'protected_ledgers_unchanged':{n:True for n in ledgers},'BFC_actual_tested_primary_precondition':bfc,
          'pending_CTS_worktree_unchanged':True,'pending_CTS_commit':CTS_COMMIT,'pending_CTS_before':cts_before,
          'frozen_BEC_native_unversioned_and_unchanged':True,'frozen_native_before':native_before,
          'branch_relationship':'This BEC source is a sibling of pendingCTS4e8, both single children of48fc; neither is assumed to fast-forward the other.',
          'native_resources_transport_queue_or_launch':'NOT_RUN','remote_operations':False,'native_draft_execution_binding':None,
          'local_scope':'Only frozen BEC9 added to a separate detached worktree; no primary/runtime/queue/process/auth/schedule changes.',
          'future_boundary':'This source version does not promote primary/runtime or enable frozen disabled native preparation. If actual main changes, create a new compatible source version and perform native tests against that exact version; do not relabel old raw results or assume siblings can ff. A separately reviewed version-bound fresh native package/lease and actual authorized idle GPU remain required. All BEC native/resources/efficacy are unmeasured.',
          'commit_output':commit_output,'material_concerns':[]}
        save('isolated_source_version.json',result);print(json.dumps({'status':result['status'],'code_commit':commit,'parent':BASE,'native':'NOT_RUN'}))
    finally:lock.close()

def main(argv=None):
    parser=argparse.ArgumentParser();parser.add_argument('--execute-root',action='store_true');parser.add_argument('--bfc-admission-sha');args=parser.parse_args(argv)
    if not args.execute_root:
        print('DRAFT_DISABLED_NO_GIT_WORKTREE_OR_SOURCE_WRITE');return 0
    require(DRAFT_EXECUTION_ENABLED,'Draft is execution-disabled; root must independently review/materialize a separate explicit copy')
    require(isinstance(args.bfc_admission_sha,str) and re.fullmatch(r'[0-9a-f]{64}',args.bfc_admission_sha),'Actual formal BFC admission SHA required')
    execute(args.bfc_admission_sha);return 0
if __name__=='__main__':raise SystemExit(main())
