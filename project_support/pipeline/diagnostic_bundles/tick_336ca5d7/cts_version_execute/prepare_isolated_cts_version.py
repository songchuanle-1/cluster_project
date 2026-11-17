"""Disabled CTS source-version save draft; no primary/runtime promotion or native run.

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
DEST=ROOT/'pipeline/isolated_versions/cts_336ca5d7'
OLD=ROOT/'pipeline/diagnostic_bundles/tick_3824d9c9/new_candidate_prepare'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
CID='hierarchy-parent-cyclic-triadic-state-composition'
EXP='M214-CTS'
MODEL='model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_cts'
CONFIG='configs/Quard/ctf_hcg_csort_cts/'+MODEL+'.yaml'
BASE='48fc302c3c02ffef0b241be3593c386b6b65a72e'
PRIMARY=BASE
SOURCE_REFERENCE='11a811618179ab1ddc0cee299194667413b7fdb9'
GOAL='0441fecda02231f3af9abac3ca3e6e8f1a7e8ebce19f1f35293fdda01d765c85'
SOURCE_PREP_SHA='bfab01a31a0fc7a0d679156d5e0e6fcfa987e56e5f3bb1bdf6bded9e2208f76e'
NATIVE_PROTOCOL_SHA='70363d43bdac998d346cf06c817389267cb69682242430dca8819dd29b0fefdc'
TOKEN='336ca5d7348b4018b7fd8b9e41f6eee3'
EXPECTED_OWNER={'token':TOKEN,'thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
 'generated_at':'2026-10-25T16:10:36.841364+00:00','deadline_at':'2026-10-25T17:10:36.841364+00:00',
 'context_sha256':'30f2661957418692d66e92e432fa530733fc831d576f1660088c0d3243b17d6d',
 'pending_sha256':'c067f731a4a50bb81ace2512f21bc8d5bca86b3191f198054d6d96cc47cc0701'}
DRAFT_EXECUTION_ENABLED=True
PROTECTED_BASELINE=ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json'
PROTECTED_BASELINE_SHA='deb2f6e1093be710fbbae886b4008c187b2e6b63d63276bfb47706b36b4be142'
REVIEWS=[('pipeline/diagnostic_bundles/tick_3824d9c9/cts_topology_review.json',
 '3de1e79f8d1e14d447185b1aff7fb6624c3cb450b1f42906f9bb2c888f7ede97'),
 ('pipeline/diagnostic_bundles/tick_3824d9c9/cts_integration_review.json',
 'dcb3f3d7833af34e891578f72b88cf0259549660fe1cc909ab3621f558c6549e')]
BFC_CID='hierarchy-parent-butterfly-token-composition'
BFC_CONFIG='configs/Quard/ctf_hcg_csort_bfc/model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_bfc.yaml'
BFC_SOURCE=ROOT/'pipeline/diagnostic_bundles/tick_ab7e46d4/new_candidate_prepare'
BFC_SOURCE_SHA='8512a69de3d5fcdd32523bbf966833485f3e17329235881de7aa0bd5adbe4501'
BFC_RECEIPT=ROOT/'pipeline/admissions/M213-BFC.json'
BFC_INDEPENDENT_STATUS='FOUR_ACTUAL_BFC_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED'
CURRENT_TICK='pipeline/diagnostic_bundles/tick_336ca5d7/'
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
    require(sha(OLD/'preparation.json')==SOURCE_PREP_SHA and sha(OLD/'native_protocol.md')==NATIVE_PROTOCOL_SHA,'Frozen CTS preparation/protocol changed')
    source=read(OLD/'preparation.json')
    require((source['candidate_id'],source['experiment_id'])==(CID,EXP),'CTS source identity differs')
    require(source['code_commit'] is None and source['source_commit'] is None and source['future_version_parent'] is None,'Do not rewrite/reuse a versioned source packet')
    require(source['base_reference_commit']==SOURCE_REFERENCE and source['source_file_count']==9,'Wrong historical source reference/count')
    for name,h in source['prepared_file_hashes'].items():
        p=(OLD/name).resolve();require(p.is_relative_to(OLD.resolve()) and sha(p)==h,'Frozen CTS prepared file differs')
    for name,h in REVIEWS:
        p=ROOT/name;require(sha(p)==h,'CTS independent review changed');review=read(p)
        require(review['candidate_id']==CID and review['material_concerns']==[] and review['preparation']==ref(OLD/'preparation.json'),'CTS independent review binding differs')
    frozen={name.removeprefix('staged_repository/'):h for name,h in source['prepared_file_hashes'].items() if name.startswith('staged_repository/')}
    names={'__init__.py','backbone.py','dec.py','hier_postprocess.py','loss.py','middle_triad.py','network.py','sample_model.py'}
    require(set(frozen)=={'framework/model/Quard_model/'+MODEL+'/'+n for n in names}|{CONFIG},'Only exact CTS8+nativeYAML allowed')
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
    require(sha(BFC_RECEIPT)==admission_sha,'Formal BFC receipt changed/missing')
    receipt=read(BFC_RECEIPT)
    require((receipt['id'],receipt['candidate_id'],receipt['code_commit'],receipt['config'],receipt['goal_sha256'])==('M213-BFC',BFC_CID,BASE,BFC_CONFIG,GOAL),'Formal tested BFC receipt identity differs')
    created=datetime.fromisoformat(receipt['created_at']);require(created.tzinfo is not None and datetime.fromisoformat(EXPECTED_OWNER['generated_at'])<=created<=datetime.now(timezone.utc),'BFC receipt is not from this foreground tick')
    independent_path=artifact(receipt['independent_review']);require(receipt['independent_review']['path'].startswith(CURRENT_TICK),'BFC review belongs to a different tick')
    independent=read(independent_path)
    require(independent['status']==BFC_INDEPENDENT_STATUS and independent['material_concerns']==[],'Actual BFC native/resource independent review not passed')
    require((independent['candidate_id'],independent['code_commit'],independent['goal_sha256'])==(BFC_CID,BASE,GOAL),'Actual BFC review identity differs')
    raws=independent['raw_results'];require(len(raws)==4 and {(x['mode'],x['target']) for x in raws}==PAIRS,'Exactly four actual BFC arms required')
    for row in raws:
        require(row['execution_path'].startswith(CURRENT_TICK+'bfc_execution/'),'Do not relabel old raw results')
        artifact({'path':row['execution_path'],'sha256':row['execution_sha256']})
    queue=read(ROOT/'pipeline/queue.json');matches=[t for tasks in queue['gpu_queues'].values() for t in tasks if t.get('id')=='M213-BFC']
    require(len(matches)<=1,'Ambiguous BFC queue identity')
    task=matches[0] if matches else read(ROOT/'pipeline/experiments/M213-BFC.json')
    require(task.get('code_commit')==BASE and task.get('admission_receipt')==BFC_RECEIPT.relative_to(ROOT).as_posix(),'BFC task/receipt identity differs')
    if not matches:require(task.get('status') in ('done_complete','done_earlystop') and task.get('launch_verified') is True,'Missing current admitted BFC task')
    sys.path.insert(0,str(SKILL));import closure
    closure.admission(str(ROOT),task,completed=not bool(matches))
    require(git(REPO,'rev-parse','HEAD').decode().strip()==BASE,'Actual primary is not tested48fc; refuse to guess parent')
    require(git(REPO,'rev-list','--parents','-n','1',BASE).decode().split()==[BASE,SOURCE_REFERENCE],'Tested BFC parent/commit differs')
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

def execute(admission_sha):
    owner_guard();frozen=source_details();require(not DEST.exists() and DEST.resolve().is_relative_to(ROOT.resolve()),'Worktree exists/escapes project')
    require(not (HERE/'isolated_source_version.json').exists() and not (HERE/'isolated_version_operation_intent.json').exists(),'Previous attempt needs exact reconciliation; do not replay')
    policy=read(ROOT/'pipeline/closure_policy.json');grant=policy['experiment_first']['authorization']
    require(policy['enabled'] is True and policy['experiment_first']['enabled'] is True and sha(ROOT/grant['path'])==grant['sha256'],'Current source preparation authorization differs')
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));require(lock is not None,'Canonical project lock busy')
    try:
        bfc=bfc_tested_primary_gate(admission_sha);git_hooks_filters_guard();before=primary_snapshot();require(before['HEAD']==PRIMARY,'Primary HEAD differs')
        require(not(set(frozen)&set(before['protected_files'])),'CTS paths overlap protected worktree')
        for n,h in frozen.items():require(not git(REPO,'ls-tree',BASE,'--',n),'CTS target already tracked');require(not (REPO/n).exists(),'CTS target exists in primary; never overwrite')
        ledgers={n:sha(ROOT/'pipeline'/n) for n in PROTECTED_LEDGER_NAMES}
        def mutation_guard():
            owner_guard();require(primary_snapshot()==before,'Primary HEAD/index/status/protected bytes changed before mutation')
            require({n:sha(ROOT/'pipeline'/n) for n in PROTECTED_LEDGER_NAMES}==ledgers,'Protected lifecycle/receipt bytes changed before mutation')
            require(source_details()==frozen,'Frozen source changed');bfc_tested_primary_gate(admission_sha)
        save('isolated_version_before.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'primary':before,'protected_ledgers':ledgers,'BFC_actual_tested_primary_precondition':bfc})
        mutation_guard();DEST.parent.mkdir(exist_ok=True)
        save('isolated_version_operation_intent.json',{'operation':'git worktree add --detach; copy frozen9; add exact9; ordinary detached commit',
          'worktree':str(DEST),'actual_parent_required':BASE,'source_reference_only':SOURCE_REFERENCE,'remote_operations':False,
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
        mutation_guard();commit_output=git(DEST,'commit','-m','Add CTS cyclic triadic token composition (native pending)').decode('utf-8',errors='replace')
        commit=git(DEST,'rev-parse','HEAD').decode().strip();require(re.fullmatch(r'[0-9a-f]{40}',commit),'Invalid commit SHA')
        require(git(DEST,'rev-list','--parents','-n','1',commit).decode().split()==[commit,BASE],'CTS is not exact single child of tested actual primary48fc')
        require(not git(DEST,'status','--porcelain=v1','--untracked-files=all').strip(),'Committed isolated worktree is not clean')
        blobs={n:hashlib.sha256(git(DEST,'show',commit+':'+n)).hexdigest() for n in frozen};require(blobs==frozen,'Committed blobs differ')
        require(sorted(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines())==sorted('A\t'+n for n in frozen),'CTS commit contains changes beyond exact9 additions')
        after=primary_snapshot();require(after==before,'Primary changed');require({n:sha(ROOT/'pipeline'/n) for n in PROTECTED_LEDGER_NAMES}==ledgers,'Protected lifecycle changed')
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_CTS_SOURCE_COMMIT_ONLY_NATIVE_UNEXECUTED',
          'candidate_id':CID,'experiment_id':EXP,'code_commit':commit,'parent_commit':BASE,'source_reference_only':SOURCE_REFERENCE,
          'worktree':str(DEST),'source_preparation':ref(OLD/'preparation.json'),'frozen_source_files':frozen,'committed_blob_sha256':blobs,
          'primary_Cluster_HEAD':PRIMARY,'primary_HEAD_index_status_28_protected_bytes_unchanged':True,
          'protected_ledgers_unchanged':{n:True for n in ledgers},'BFC_actual_tested_primary_precondition':bfc,
          'native_resources_transport_queue_or_launch':'NOT_RUN','remote_operations':False,'native_draft_execution_binding':None,
          'local_scope':'Only frozen CTS9 added to a separate detached worktree; no primary/runtime/queue/process/auth/schedule changes.',
          'future_boundary':'This source version does not promote primary/runtime or enable frozen disabled native preparation. A separately reviewed version-bound fresh native package/lease and actual authorized idle GPU remain required. All native/resources/efficacy are unmeasured.',
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
