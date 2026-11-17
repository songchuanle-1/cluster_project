"""Single canonical dispatch after observed GPU0 context disappeared."""
import json
import prepare_and_queue as op
from prepare_and_queue import ROOT,P,OUT,ID,NEW_ROOT,now,load,save,guard,mon,strict_ssh

guard(); lock=mon.acquire_lock(str(ROOT)); assert lock is not None
previous=mon.ssh
try:
    guard(); q=load(P/'queue.json'); task=next(t for t in q['gpu_queues']['server-4'] if t['id']==ID)
    assert task['status']=='waiting' and not task.get('dispatch_hold') and not task.get('pid') and task['resume_authorized'] is True
    assert load(OUT/'final_gpu0_observation.json')['data']['contexts_gpu0']==''
    if (OUT/'transport_calls.json').exists(): op.CALLS=load(OUT/'transport_calls.json')
    assert not any(c.get('launch_request') for c in op.CALLS),'Launch already requested; reconcile, never replay'
    server=mon.load_servers(str(ROOT))['server-4']; assert server['remote_code_root']==NEW_ROOT and server['allowed_gpus']==[0]
    save(OUT/'single_launch_intent.json',dict(recorded_at=now(),id=ID,checkpoint=task['resume_from'],code_commit=task['code_commit'],
        remote_code_root=NEW_ROOT,physical_gpu=0,reason='Previous canonical attempt did not launch because GPU0 occupied. New real observation has no context; one original native launch allowed.'))
    mon.ssh=strict_ssh; events=[]
    mon._process_queue(q,'server-4',server['host'],server['user'],str(ROOT),set(),{'0'},events,max_tasks_per_gpu=1,allow_external_overlay=False,remote_code_root=NEW_ROOT,current_tasks=0)
    current=next(t for t in load(P/'queue.json')['gpu_queues']['server-4'] if t['id']==ID)
    result=dict(recorded_at=now(),task_after=current,events=events,running_after=load(P/'running.json'),
        launch_request_count=sum(bool(c.get('launch_request')) for c in op.CALLS),
        verified_native_progress=current.get('status')=='running' and current.get('launch_verified') is True)
    save(OUT/'launch_dispatch_result.json',result)
    print(json.dumps(dict(status=current['status'],pid=current.get('pid'),log=current.get('log'),launch_verified=current.get('launch_verified'),dispatch_hold=current.get('dispatch_hold'),launch_request_count=result['launch_request_count']),ensure_ascii=False),flush=True)
finally: mon.ssh=previous; lock.close()
