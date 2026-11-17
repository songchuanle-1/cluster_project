"""Use canonical terminal APIs for the exact verified run,without another monitor."""
from datetime import datetime,timezone
import csv,json
from ops import guard,save,run,evidence,ROOT,OUT,NAME
import foreground_tick as tick
import pipeline_monitor as pm
guard();result=tick.load(OUT/'exit_result.json')
assert result['disposition']=='done_earlystop' and result['earlystop_markers']==[['23','10','0.4885']]
assert not result['error_markers'] and not result['pid_alive']
destination=OUT/'M203_native_terminal.log';assert not destination.exists()
transfer=run(['scp','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','songcl@192.168.1.115:'+result['native_log'],str(destination)])
save('terminal_log_transfer.json',dict(returncode=transfer.returncode,stderr=transfer.stderr));assert transfer.returncode==0
assert tick.digest(destination)==result['native_log_sha256']
lock=pm.acquire_lock(str(ROOT));assert lock is not None,'Projectqueueowned;do not override'
try:
    guard();experiment=pm.load_experiment(str(ROOT),'M203-FLE');assert experiment['status']=='running'
    with (ROOT/'pipeline/experiments.csv').open(encoding='utf-8',newline='') as stream:
        assert not any(row.get('id')=='M203-FLE' for row in csv.DictReader(stream))
    queue=pm.load_queue(str(ROOT));task=next(t for t in queue['gpu_queues']['server-4'] if t.get('id')=='M203-FLE')
    previous_pull=pm.pull_log
    def exact_pulled_log(project_dir,host,user,remote_log,cfg_name,state,srv_name=''):
        assert project_dir==str(ROOT) and host=='192.168.1.115' and user=='songcl'
        assert remote_log==result['native_log'] and cfg_name==NAME and state=='done_earlystop' and srv_name=='server-4'
        assert tick.digest(destination)==result['native_log_sha256']
        return str(destination)
    pm.pull_log=exact_pulled_log;events=[]
    try:pm.finalize_task(str(ROOT),queue,'server-4','192.168.1.115','songcl',task,NAME,'done_earlystop',result['best_native_miou'],23,'0',result['native_log'],events)
    finally:pm.pull_log=previous_pull
    experiment=pm.load_experiment(str(ROOT),'M203-FLE')
    experiment.update(native_best_miou_exact=result['best_native_miou'],native_best_epoch=13,native_terminal_epoch=23,
        native_finished_at='2026-10-18T12:08:47.870+08:00',last_checkpoint_epoch=22,
        native_terminal_evidence=[evidence(OUT/'exit_result.json'),evidence(destination)],
        checkpoint_snapshots=result['checkpoint_metadata'])
    pm.save_experiment(str(ROOT),experiment)
    deathwatch=pm.load_deathwatch(str(ROOT));previous_dw=deathwatch.get('server-4',{}).pop(NAME,None)
    if previous_dw is not None:pm.save_deathwatch(str(ROOT),deathwatch)
    pm.daily_report(str(ROOT),events)
finally:lock.close()
save('terminal_reconciliation.json',{'observed_at':datetime.now(timezone.utc).isoformat(),'status':'done_earlystop',
    'native_epoch':23,'best_miou_exact':result['best_native_miou'],'events':events,'old_deathwatch':previous_dw,
    'scope':'Canonicalfinalize_taskAPIswithverifiedexactloginsteadbroadremote_pull;nomonitor,dispatch,restartorsourcechange'})
print(json.dumps({'reconciled':'M203-FLE','state':'done_earlystop','best_miou':result['best_native_miou'],'native_epoch':23,'events':events}))
