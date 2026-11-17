"""Root-only read-only occupation proof; no queue, candidate or remote mutation."""
from pathlib import Path
from datetime import datetime, timezone
import json, os, shlex, subprocess, sys
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u

HERE = Path(__file__).resolve().parent
CIDS = ['hierarchy-wedge-factor-incidence-composition', 'hierarchy-nonlinear-lifting-analysis-synthesis']

def main():
    guard()
    assert sys.dont_write_bytecode
    sys.path.insert(0, 'C:/Users/chuanle song/.codex/skills/songcl_research_pipeline')
    import pipeline_monitor as mon
    import gpu_occupation
    lock = mon.acquire_lock(str(ROOT)); assert lock is not None
    try:
        guard()
        work_sha = sha(ROOT/'pipeline/research_work.json')
        queue_hashes = {n:sha(ROOT/'pipeline'/n) for n in ('queue.json','running.json')}
        rawpath = HERE/'source_reserve_gpu_occupation_raw.json'
        proofpath = HERE/'source_reserve_gpu_occupation.json'
        resultpath = HERE/'source_reserve_gpu_occupation_validation.json'
        assert not any(p.exists() for p in (rawpath, proofpath, resultpath))
        commands = dict(hostname=['hostname'], gpu=['nvidia-smi', '--query-gpu=index,uuid,utilization.gpu,memory.used,memory.total', '--format=csv,noheader,nounits'], compute=['nvidia-smi', '--query-compute-apps=gpu_uuid,pid', '--format=csv,noheader,nounits'])
        program = "import json,subprocess,os\nos.environ['PYTHONDONTWRITEBYTECODE']='1'\ncommands="+repr(commands)+"\nqueries={}\nfor key,command in commands.items():\n r=subprocess.run(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,universal_newlines=True,timeout=20)\n queries[key]=dict(rc=r.returncode,stdout=r.stdout,stderr=r.stderr,command=command)\n if key=='hostname':\n  assert r.returncode==0 and r.stdout.strip()=='dl04-MS-7E06', 'Pinned server identity mismatch'\nprint(json.dumps(queries))\n"
        args=['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8','songcl@192.168.1.115','export PYTHONDONTWRITEBYTECODE=1 && /usr/bin/python3 -B -c '+shlex.quote(program)]
        guard()
        result=subprocess.run(args,capture_output=True,text=True,encoding='utf-8',timeout=75)
        guard()
        assert result.returncode==0, result.stderr
        queries=json.loads(result.stdout)
        assert all(q['rc']==0 for q in queries.values())
        assert queries['hostname']['stdout'].strip()=='dl04-MS-7E06'
        u.save(rawpath,queries)
        observed=datetime.now(timezone.utc).isoformat()
        proof=dict(schema_version=1,kind='exclusive_gpu_occupation',complete=True,read_only=True,project=ROOT.name,token=EXPECTED['token'],snapshot_generated_at=EXPECTED['generated_at'],snapshot_sha256=EXPECTED['context_sha256'],servers_sha256=sha(ROOT/'SERVERS.yaml'),observed_at=observed,candidate_ids=CIDS,scope=dict(server='server-4',host='192.168.1.115',user='songcl',allowed_gpus=[0,1],max_tasks_per_gpu=1),queries=queries,command='python -B pipeline/diagnostic_bundles/tick_85772373/observe_source_reserve_resources.py',actual_ssh_argv=args,raw_log=u.ref(rawpath),scope_note='Standalone source-reserve observation; uses canonical raw parser/validated_state, not canonical blocked-stage collect and never edits a candidate stage.')
        u.save(proofpath,proof)
        context=u.read(ROOT/'pipeline/headless/.tick_context.json')
        server=next(s for s in context['queue']['servers'] if s['name']=='server-4')
        queue=mon.load_queue(str(ROOT))
        states=[]
        for cid in CIDS:
            candidate=dict(id=cid,required_server='server-4',occupation_evidence=u.ref(proofpath),evidence=[u.ref(proofpath),u.ref(rawpath)])
            state=gpu_occupation.validated_state(ROOT,context,candidate,server,queue)
            assert state['inventory'][0]['uuid']=='GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c'
            assert state['inventory'][1]['uuid']=='GPU-7f82edb9-f620-8045-caea-a75232265cd1'
            assert 3786531 in state['compute_pids'][state['inventory'][0]['uuid']]
            assert 3696093 in state['compute_pids'][state['inventory'][1]['uuid']]
            assert state['busy_gpu_ids']==[0,1] and not state['idle_gpu_ids'], 'Availability changed; keep evidence and investigate, never infer a launch.'
            states.append(dict(candidate_id=cid,state=state))
        assert sha(ROOT/'pipeline/research_work.json')==work_sha
        assert {n:sha(ROOT/'pipeline'/n) for n in queue_hashes}==queue_hashes
        u.save(resultpath,dict(owner=EXPECTED,observed_at=observed,occupation_evidence=u.ref(proofpath),raw_evidence=u.ref(rawpath),states=states,work_and_queue_unchanged=True,no_compute_signal_queue_source_or_remote_write=True))
        print(json.dumps(dict(observed_at=observed,busy_gpu_ids=[0,1],idle_gpu_ids=[],validation=u.ref(resultpath))))
    finally:
        lock.close()

if __name__=='__main__': main()
