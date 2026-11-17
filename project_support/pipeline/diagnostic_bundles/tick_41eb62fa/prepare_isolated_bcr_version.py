"""Save frozen BCR source in a detached worktree without advancing dispatch HEAD."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import subprocess
import sys

ROOT=Path('D:/project/cluster_project')
REPO=ROOT/'Cluster'
HERE=Path(__file__).resolve().parent
DEST=ROOT/'pipeline/isolated_versions/bcr_41eb62fa'
OLD=ROOT/'pipeline/diagnostic_bundles/tick_41eb62fa/new_candidate_prepare'
BASE='00e2b18c6b8d568a64edb496e6979d766440883c'
PRIMARY='00e2b18c6b8d568a64edb496e6979d766440883c'
TOKEN='41eb62fa1d32436f859264a19b0d4049'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(repo,*args):
    env=os.environ.copy();env['GIT_OPTIONAL_LOCKS']='0';env['GIT_TERMINAL_PROMPT']='0';env['GIT_LFS_SKIP_SMUDGE']='1'
    result=subprocess.run(['git','-c','core.autocrlf=false','-c','submodule.recurse=false','-C',str(repo),*args],capture_output=True,timeout=90,env=env)
    assert result.returncode==0, result.stderr.decode('utf-8',errors='replace')
    return result.stdout
def save(name,data):
    with (HERE/name).open('x',encoding='utf-8') as stream:
        json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n');stream.flush();os.fsync(stream.fileno())
def primary_snapshot():
    status=git(REPO,'status','--porcelain=v1','-z','--untracked-files=all')
    rows=[row for row in status.split(b'\0') if row]
    assert len(rows)==28
    files={}
    for row in rows:
        assert b'R' not in row[:2] and b'C' not in row[:2]
        name=row[3:].decode('utf-8');p=(REPO/name).resolve()
        assert p.is_relative_to(REPO.resolve()) and p.is_file() and p.stat().st_size<=65536
        files[name]=sha(p)
    index=Path(git(REPO,'rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=REPO/index
    return {'HEAD':git(REPO,'rev-parse','HEAD').decode().strip(),'status_hex':status.hex(),
        'index_sha256':sha(index), 'protected_files':files}

def main():
    assert not DEST.exists() and not (HERE/'isolated_source_version.json').exists()
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    # Only ordinary default Git LFS definitions may be present; no network smudge.
    cfg=subprocess.run(['git','-C',str(REPO),'config','--get-regexp',r'^(core\.hooksPath|filter\..*)$'],capture_output=True,timeout=20)
    assert cfg.returncode in (0,1)
    configured=dict(row.split(' ',1) for row in cfg.stdout.decode().splitlines())
    standard_lfs={'filter.lfs.clean':'git-lfs clean -- %f','filter.lfs.smudge':'git-lfs smudge -- %f','filter.lfs.process':'git-lfs filter-process','filter.lfs.required':'true'}
    assert all(key in standard_lfs and value==standard_lfs[key] for key,value in configured.items()), 'Nonstandard Git hook/filter needs review'
    hooks=Path(git(REPO,'rev-parse','--git-path','hooks').decode().strip())
    if not hooks.is_absolute():hooks=REPO/hooks
    assert not hooks.exists() or not any(p.is_file() and not p.name.endswith('.sample') for p in hooks.iterdir()), 'Active Git hooks need review'
    assert sha(OLD/'preparation.json')=='faf3494d13c5026b21e1d235dab311cc4f9a9d88b9653c4726a5ccbdc8958615'
    frozen={name.removeprefix('staged_repository/'):value for name,value in read(OLD/'preparation.json')['prepared_file_hashes'].items() if name.startswith('staged_repository/')};assert len(frozen)==9
    for name,expected in frozen.items():
        assert sha(OLD/'staged_repository'/name)==expected
        assert not git(REPO,'ls-tree',BASE,'--',name)
    policy=read(ROOT/'pipeline/closure_policy.json');grant=policy['experiment_first']['authorization']
    assert policy['experiment_first']['enabled'] and sha(ROOT/grant['path'])==grant['sha256']
    sys.path.insert(0,str(SKILL));import pipeline_monitor as monitor
    lock=monitor.acquire_lock(str(ROOT));assert lock is not None
    try:
        before=primary_snapshot();assert before['HEAD']==PRIMARY
        assert not git(REPO,'diff','--cached','--name-only').strip()
        protected_names=['queue.json','running.json','research_work.json','experiments/M210-PSNC.json','experiments/M211-BTC.json',
            'experiments/M206-CGCA.json','experiments/M207-HAP.json','admissions/M210-PSNC.json','admissions/M211-BTC.json']
        ledgers={name:sha(ROOT/'pipeline'/name) for name in protected_names}
        save('isolated_version_before.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'primary':before,'protected_ledgers':ledgers})
        DEST.parent.mkdir(exist_ok=True)
        save('isolated_version_operation_intent.json',{'operation':'git worktree add --detach; copy frozen9; add exact9; ordinary detached commit',
            'worktree':str(DEST),'base':BASE,'autocrlf_per_command':False,'recurse_submodules':False,'remote_operations':False,
            'source_preparation':{'path':str(OLD/'preparation.json'),'sha256':sha(OLD/'preparation.json')},'source_files':frozen})
        git(REPO,'worktree','add','--detach',str(DEST),BASE)
        assert not git(DEST,'status','--porcelain=v1','--untracked-files=all').strip()
        for name,expected in frozen.items():
            p=DEST/name;assert not p.exists();p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as stream:stream.write((OLD/'staged_repository'/name).read_bytes())
            assert sha(p)==expected
        assert not git(DEST,'check-attr','-a','--',*sorted(frozen)).strip(), 'Source attributes require review'
        git(DEST,'add','--',*sorted(frozen))
        staged=git(DEST,'diff','--cached','--name-status').decode().splitlines()
        assert sorted(staged)==sorted('A\t'+name for name in frozen)
        assert {name:hashlib.sha256(git(DEST,'show',':'+name)).hexdigest() for name in frozen}==frozen
        commit_output=git(DEST,'commit','-m','Add BCR strict-exclusive bidirectional complement recurrence (native pending)').decode('utf-8',errors='replace')
        commit=git(DEST,'rev-parse','HEAD').decode().strip()
        assert git(DEST,'rev-list','--parents','-n','1',commit).decode().split()==[commit,BASE]
        assert not git(DEST,'status','--porcelain=v1','--untracked-files=all').strip()
        blobs={name:hashlib.sha256(git(DEST,'show',commit+':'+name)).hexdigest() for name in frozen}
        assert blobs==frozen
        assert sorted(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines())==sorted('A\t'+name for name in frozen)
        after=primary_snapshot();assert after==before
        assert {name:sha(ROOT/'pipeline'/name) for name in protected_names}==ledgers
        result={'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_SOURCE_COMMIT_ONLY_NATIVE_UNEXECUTED',
            'candidate_id':'hierarchy-parent-bidirectional-complement-recurrence','experiment_id':'M212-BCR',
            'code_commit':commit,'parent_commit':BASE,'worktree':str(DEST),'frozen_source_files':frozen,'committed_blob_sha256':blobs,
            'primary_Cluster_HEAD':PRIMARY,'primary_HEAD_index_status_28_protected_bytes_unchanged':True,
            'protected_ledgers_unchanged':{name:sha(ROOT/'pipeline'/name)==expected for name,expected in ledgers.items()},
            'native_resources_transport_queue_or_launch':'NOT_RUN','remote_operations':False,'native_draft_execution_binding':None,
            'local_scope':'Only frozen9 added to a separate detached worktree; worktreeHEAD retains recoverable commit. No active checkout changed.',
            'future_boundary':'Source commit is a single child of current BTC00e; keep primary and active remote BTC HEAD00e unchanged. This version records static-tested source only. Actual original-YAML native TRAIN2 with recurrent-state weight-half gradient/update coverage and matched resources remain NOT_RUN.',
            'commit_output':commit_output,'material_concerns':[]}
        save('isolated_source_version.json',result)
        print(json.dumps({'status':result['status'],'code_commit':commit,'worktree':str(DEST),'files':9,
            'primary_HEAD_unchanged':after['HEAD']==PRIMARY,'frozen_blob_hashes_match':True,'native':'NOT_RUN'},ensure_ascii=False))
    finally:lock.close()

if __name__=='__main__':main()
