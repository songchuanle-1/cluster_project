"""One authorized, candidate-only local BEC R1 detached source save.

No SSH/GPU/native/shared-ledger or primary checkout/index mutation. Partial
journals or an existing destination require exact reconciliation, never replay.
"""
from pathlib import Path
from datetime import datetime,timezone
import hashlib,json,os,subprocess,sys

ROOT=Path('D:/project/cluster_project');PRIMARY=ROOT/'Cluster'
HERE=Path(__file__).resolve().parent
OUT=HERE/'bec_r1_version_operation'
DEST=ROOT/'pipeline/isolated_versions/bec_r1_45eb3b04'
PARENT='4e80006047d5cb3dcdfb9c1102e02c33f354a07d'
OLD_BASE='48fc302c3c02ffef0b241be3593c386b6b65a72e'
TOKEN='45eb3b045c6243518d56eade38d5cd17'
SKILL=Path('C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')

def read(p):return json.loads(Path(p).read_text(encoding='utf8'))
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def ref(p):return {'path':p.relative_to(ROOT).as_posix(),'sha256':sha(p)}
def save(name,value):
    with (OUT/name).open('x',encoding='utf8') as f:
        json.dump(value,f,indent=2,ensure_ascii=False,allow_nan=False);f.write('\n');f.flush();os.fsync(f.fileno())
def git(repo,*args):
    env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0',GIT_LFS_SKIP_SMUDGE='1')
    r=subprocess.run(['git','--no-optional-locks','-c','core.autocrlf=false','-c','core.eol=lf','-c','core.fsmonitor=false','-c','submodule.recurse=false','-C',str(repo),*args],capture_output=True,timeout=90,env=env)
    assert r.returncode==0,r.stderr.decode(errors='replace');return r.stdout
def owner_guard():
    o=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert o['token']==TOKEN and o['thread_id']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert read(ROOT/'pipeline/execution_mode.json')['mode']=='foreground'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(o['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==o['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==o['pending_sha256']
    return {k:o[k] for k in ['token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256']}
def snapshot():
    baseline=read(ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json')['protected_existing_worktree']
    assert len(baseline)==28
    raw=git(PRIMARY,'status','--porcelain=v1','-z','--untracked-files=all');rows=[x for x in raw.split(b'\0') if x]
    assert {(x[:2].decode(),x[3:].decode()) for x in rows}=={(x['status'],x['path']) for x in baseline}
    files={x['path']:sha(PRIMARY/x['path']) for x in baseline}
    assert files=={x['path']:x['sha256'] for x in baseline}
    assert git(PRIMARY,'diff','--cached','--name-only','-z')==b''
    index=Path(git(PRIMARY,'rev-parse','--git-path','index').decode().strip());index=index if index.is_absolute() else PRIMARY/index
    head=git(PRIMARY,'rev-parse','HEAD').decode().strip();assert head in (OLD_BASE,PARENT)
    names=['queue.json','running.json','research_work.json','experiments.csv',
      'experiments/M206-CGCA.json','experiments/M207-HAP.json','experiments/M210-PSNC.json','experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M213-BFC.json',
      'admissions/M210-PSNC.json','admissions/M211-BTC.json','admissions/M212-BCR.json','admissions/M213-BFC.json',
      'experiments/M214-CTS.json','admissions/M214-CTS.json','experiments/M215-BEC.json','admissions/M215-BEC.json']
    ledgers={n:{'exists':(ROOT/'pipeline'/n).is_file(),'sha256':sha(ROOT/'pipeline'/n) if (ROOT/'pipeline'/n).is_file() else None} for n in names}
    packets={}
    for folder in ['pipeline/diagnostic_bundles/tick_6bdbcf77/new_candidate_prepare','pipeline/diagnostic_bundles/tick_f86d1cfa/bec_native_prepare','pipeline/diagnostic_bundles/tick_521a6f59/bec_operational_prepare']:
        prep=ROOT/folder/'preparation.json';metadata=read(prep);mapping=metadata['prepared_file_hashes']
        assert all(sha(prep.parent/n)==h for n,h in mapping.items())
        packets[folder]={'preparation_sha256':sha(prep),'file_hashes':mapping}
    ctsproof=read(ROOT/'pipeline/diagnostic_bundles/tick_336ca5d7/cts_version_execute/isolated_source_version.json')
    ctsrepo=Path(ctsproof['worktree']);assert git(ctsrepo,'rev-parse','HEAD').decode().strip()==PARENT and not git(ctsrepo,'status','--porcelain=v1','-z','--untracked-files=all')
    ctsfiles=ctsproof['frozen_source_files'];assert len(ctsfiles)==9
    assert all(sha(ctsrepo/n)==h and hashlib.sha256(git(PRIMARY,'show',PARENT+':'+n)).hexdigest()==h for n,h in ctsfiles.items())
    return {'primary_HEAD':head,'primary_status_hex':raw.hex(),'primary_index_sha256':sha(index),'primary_index_empty':True,'protected28':files,'protected_ledgers':ledgers,'frozen_BEC_packets':packets,'CTS_source':{'HEAD':PARENT,'worktree':str(ctsrepo),'clean':True,'frozen_source_files':ctsfiles}}

def main():
    owner=owner_guard()
    assert not OUT.exists() and not DEST.exists(),'Existing journal/destination needs read-only reconciliation; do not replay'
    prep=HERE/'bec_r1_prepare/preparation.json';assert sha(prep)=='2ef488c483bf1fb5234dc9615069f7ec2a9232370d186ec4f92cb2bfb3212731'
    spec=read(prep);assert spec['revision']==1 and spec['code_commit'] is None and spec['future_parent_commit'] is None
    assert sha(HERE/'bec_revision1_preregistration.json')=='3fa782b8970de909a219cc090e2188983e1afeab1ac99cac43df07b4f1e5b527'
    cpu=read(HERE/'bec_r1_cpu_trace_evidence.json');assert cpu['result']['registered_prediction_supported_by_CPU_test'] is True
    files=spec['source_files'];assert len(files)==9
    assert all(sha(prep.parent/'staged_repository'/n)==h for n,h in files.items())
    assert git(PRIMARY,'rev-parse',PARENT+'^{commit}').decode().strip()==PARENT
    identity={k:git(PRIMARY,'config','--get',k).decode().strip() for k in ['user.name','user.email']};assert all(identity.values()),'Existing repository Git identity is required'
    config=subprocess.run(['git','-c','core.fsmonitor=false','-C',str(PRIMARY),'config','--get-regexp',r'^(core\.hooksPath|filter\..*)$'],capture_output=True,timeout=20)
    assert config.returncode in (0,1);configured=dict(x.split(' ',1) for x in config.stdout.decode().splitlines())
    allowed={'filter.lfs.clean':'git-lfs clean -- %f','filter.lfs.smudge':'git-lfs smudge -- %f','filter.lfs.process':'git-lfs filter-process','filter.lfs.required':'true'}
    assert all(k in allowed and allowed[k]==v for k,v in configured.items())
    hooks=Path(git(PRIMARY,'rev-parse','--git-path','hooks').decode().strip());hooks=hooks if hooks.is_absolute() else PRIMARY/hooks
    assert not hooks.exists() or not any(p.is_file() and not p.name.endswith('.sample') for p in hooks.iterdir())
    sys.path.insert(0,str(SKILL));import pipeline_monitor
    lock=pipeline_monitor.acquire_lock(str(ROOT))
    if lock is None:
        print(json.dumps({'status':'PENDING_CANONICAL_PROJECT_LOCK_BUSY','mutation_started':False}));return 2
    try:
        owner_guard();before=snapshot()
        assert all(not git(PRIMARY,'ls-tree',PARENT,'--',n) for n in files),'Parent already contains BEC target paths'
        assert all(not (PRIMARY/n).exists() for n in files),'Primary contains BEC targets; never overwrite'
        OUT.mkdir(exist_ok=False)
        save('before.json',before)
        save('intent.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':owner,'operation':'one detached candidate-only BEC R1 worktree and ordinary9A commit','worktree':str(DEST),'parent_required':PARENT,'primary_HEAD_observed':before['primary_HEAD'],'source_preparation':ref(prep),'preregistration':ref(HERE/'bec_revision1_preregistration.json'),'CPU_compatibility_evidence':ref(HERE/'bec_r1_cpu_trace_evidence.json'),'source_files':files,'no_replay_on_partial':True,'no_primary_ff_or_shared_state':True,'future_native_GPU_scope':'GPU0 only under latest human instruction; this local operation uses no GPU.'})
        def guard():
            owner_guard();assert snapshot()==before,'Protected state changed; stop without overwrite/reset/replay'
        guard();git(PRIMARY,'worktree','add','--detach',str(DEST),PARENT)
        assert not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all')
        for name,checksum in files.items():
            target=DEST/name;assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
            with target.open('xb') as out:out.write((prep.parent/'staged_repository'/name).read_bytes())
            assert sha(target)==checksum
        assert not git(DEST,'check-attr','-a','--',*sorted(files)).strip()
        guard();git(DEST,'add','--',*sorted(files))
        assert sorted(git(DEST,'diff','--cached','--name-status').decode().splitlines())==sorted('A\t'+n for n in files)
        assert {n:hashlib.sha256(git(DEST,'show',':'+n)).hexdigest() for n in files}==files
        guard();output=git(DEST,'commit','-m','Preserve BEC R1 index_fill scalar compatibility on tested CTS source').decode()
        commit=git(DEST,'rev-parse','HEAD').decode().strip()
        assert git(DEST,'rev-list','--parents','-n','1',commit).decode().split()==[commit,PARENT]
        assert sorted(git(DEST,'diff-tree','--no-commit-id','--name-status','-r',commit).decode().splitlines())==sorted('A\t'+n for n in files)
        blobs={n:hashlib.sha256(git(DEST,'show',commit+':'+n)).hexdigest() for n in files};assert blobs==files
        assert not git(DEST,'status','--porcelain=v1','-z','--untracked-files=all') and not git(DEST,'diff','--cached','--name-only','-z')
        guard();after=snapshot();assert after==before
        proof={'schema_version':1,'recorded_at':datetime.now(timezone.utc).isoformat(),'status':'ISOLATED_BEC_R1_COMPATIBLE_SOURCE_SAVED_NATIVE_UNEXECUTED','candidate_id':'hierarchy-cross-level-bipartite-edge-composition','experiment_id':'M215-BEC','revision':1,'failure_scope':'implementation','code_commit':commit,'parent_commit':PARENT,'original_BEC_sibling_source':'9b6782f44ca7f2c8ac35baea01dfd070314b5701','worktree':str(DEST),'source_preparation':ref(prep),'preregistration':ref(HERE/'bec_revision1_preregistration.json'),'CPU_compatibility_evidence':ref(HERE/'bec_r1_cpu_trace_evidence.json'),'frozen_source_files':files,'committed_blob_sha256':blobs,'single_parent':True,'exact_additions_count':9,'isolated_worktree_clean':True,'primary_HEAD_before':before['primary_HEAD'],'primary_HEAD_after':after['primary_HEAD'],'primary_HEAD_index_status28_bytes_unchanged':True,'protected_ledgers_unchanged':True,'frozen_BEC_packets_unchanged':True,'CTS_parent_source_worktree_unchanged':True,'before':ref(OUT/'before.json'),'intent':ref(OUT/'intent.json'),'commit_output':output,'native_TRAIN2':'NOT_RUN_ON_THIS_VERSION','resources':'NOT_RUN_ON_THIS_VERSION','primary_ff_shared_ledger_authorization_queue_or_remote_operation':False,'future_native_GPU_scope':'GPU0 only; historical GPU1 raw remains unchanged.','material_concerns':[]}
        save('isolated_source_version.json',proof)
        print(json.dumps({'status':proof['status'],'code_commit':commit,'parent_commit':PARENT,'proof_sha256':sha(OUT/'isolated_source_version.json'),'primary_unchanged':True}));return 0
    finally:lock.close()
if __name__=='__main__':raise SystemExit(main())
