"""Default NOP. Each explicit root operation executes at most one original request."""
from pathlib import Path
import argparse, hashlib, importlib.util, json, os, subprocess, sys
HERE=Path(__file__).resolve().parent
ROOT=Path('D:/project/cluster_project')
EXPECTED_RUNTIME='4457a46f9075f61e83340aa0f0af87d5bf4e986c'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_text(encoding='utf-8'))
def dump_x(p,v):
    with Path(p).open('x',encoding='utf-8') as f:json.dump(v,f,indent=2,allow_nan=False)
def snapshot(owner):
    baseline=read(ROOT/'pipeline/diagnostic_bundles'/('tick_'+owner['token'][:8])/'protected_assets_before.json')
    git=['C:/Program Files (x86)/Git/cmd/git.exe','--no-optional-locks','-c','core.fsmonitor=false','-C',str(ROOT/'Cluster')]
    def query(*args):return subprocess.check_output(git+list(args),env=dict(os.environ,GIT_OPTIONAL_LOCKS='0',GIT_TERMINAL_PROMPT='0'))
    assert query('rev-parse','HEAD').decode().strip()==EXPECTED_RUNTIME
    assert not query('diff','--cached','--name-only','-z')
    index=Path(query('rev-parse','--git-path','index').decode().strip())
    if not index.is_absolute():index=ROOT/'Cluster'/index
    return dict(primary=EXPECTED_RUNTIME,index=sha(index),status_hex=query('status','--porcelain=v1','--untracked-files=all','-z').hex(),user_files={n:sha(ROOT/'Cluster'/n) for n in baseline['files']},running_source_files={n:sha(ROOT/'Cluster'/n) for group in ('WFC_source_paths','LFT_source_paths') for n in baseline[group]},ledgers={n:sha(ROOT/'pipeline'/n) for n in baseline['protected_ledgers']},work=sha(ROOT/'pipeline/research_work.json'),memory=sha(ROOT/'pipeline/codex_memory.md'))
def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--execute-root',action='store_true')
    p.add_argument('--operation',choices=['probe','prepare','stage','run','status','reconcile'])
    p.add_argument('--mode',choices=['smoke','resources'])
    p.add_argument('--target',choices=['champion','candidate'])
    p.add_argument('--request-id');p.add_argument('--local-only',action='store_true')
    a=p.parse_args()
    if not a.execute_root:
        print(json.dumps(dict(status='DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT',candidate_id='hierarchy-ancestry-mobius-interaction-composition',code_commit='041b63579888f2143cb9f3a5216ec4cff4ee8046',selected_physical_gpu=1,active_binding_created=False,native_executed=False)));return
    assert a.operation is not None and sys.dont_write_bytecode
    spec=importlib.util.spec_from_file_location('mic_reviewed_adapter',HERE/'adapter.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter()
    mutation=a.operation in ('prepare','stage','run')
    remaining=1020 if a.operation=='run' else 420 if a.operation=='stage' else 360 if a.operation=='prepare' else 60
    current=adapter.guard(remaining,1,mutation=mutation)
    sys.path.insert(0,'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    lock=mon.acquire_lock(str(ROOT));assert lock is not None
    try:
        current=adapter.guard(remaining,1,mutation=mutation)
        before=snapshot(current['owner']);directory=adapter._directory(current)
        if mutation:
            adapter._local_idle(1)
            if a.operation=='run':assert (a.mode,a.target) in module.PAIRS
            name=a.operation+('_'+a.mode+'_'+a.target if a.operation=='run' else '')
            journal=ROOT/'pipeline/diagnostic_bundles'/('tick_'+current['owner']['token'][:8])/('mic_root_'+name+'_intent.json')
            assert not journal.exists(),'Original wrapper attempt exists; reconcile, never replay.'
            adapter.guard(remaining,1,mutation=True)
            dump_x(journal,dict(owner={k:current['owner'][k] for k in ('token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256')},operation=a.operation,mode=a.mode,target=a.target,protected_before=before))
        if a.operation in ('probe','prepare'):result=getattr(adapter,a.operation)(1)
        elif a.operation=='run':result=adapter.run(a.mode,a.target)
        elif a.operation=='status':result=adapter.status(remote=not a.local_only)
        elif a.operation=='reconcile':result=adapter.reconcile(a.request_id)
        else:result=adapter.stage()
        adapter.guard(0,1,mutation=False)
        assert snapshot(current['owner'])==before,'Shared/source protection changed; preserve evidence, no replay.'
        print(json.dumps(dict(operation=a.operation,result=result,protected_source_and_lifecycle_unchanged=True),indent=2,allow_nan=False))
    finally:lock.close()
if __name__=='__main__':main()
