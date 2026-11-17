"""Exercise reviewed prepare guards against current registered GPU0 occupation."""
from pathlib import Path
from datetime import datetime, timezone
import importlib.util, json
from anchor import ROOT, EXPECTED, guard, sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def main():
    guard();baseline=u.read(HERE/'protected_assets_before.json')
    u.primary_protection(baseline);u.lifecycle_protection(baseline)
    catalogue=u.read(HERE/'packet_catalogue.json');assert catalogue['owner']==EXPECTED
    assert {c['id'] for c in catalogue['candidates']}=={u.HPC,u.APF}
    live=u.read(HERE/'cre_training_progress_observation.json')
    assert live['owner']==EXPECTED and live['returncode']==0
    assert live['observation']['identity_after']['pid']==118189
    assert live['observation']['runtime_commit']==u.SOURCE
    queue=u.read(ROOT/'pipeline/queue.json')
    current=next(t for t in queue['gpu_queues']['server-4'] if t['id']=='M217-CRE')
    assert current['status']=='running' and current['pid']==118189
    work_before=sha(ROOT/'pipeline/research_work.json')
    u.save(HERE/'current_resource_guard_intent.json',{
        'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'catalogue':u.ref(HERE/'packet_catalogue.json'),'program':u.ref(__file__),
        'scope':'Only explicit reviewed Adapter.prepare(0) with transport forbidden while original M217 owns GPU0. No native work, active binding or remote mutation.'})
    results=[]
    for c in catalogue['candidates']:
        u.check_refs(c['evidence'])
        op=ROOT/c['operational_preparation']['path'];op=op.parent
        assert not (HERE/c['execution_directory']).exists()
        spec=importlib.util.spec_from_file_location('current_'+c['short']+'_reviewed_adapter',op/'adapter.py')
        module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
        class NoTransport:
            def __init__(self):self.calls=[]
            def call(self,*args,**kwargs):
                self.calls.append([args,kwargs]);raise AssertionError('No transport permitted while original M217 occupies the registered slot')
        transport=NoTransport();adapter=module.Adapter(transport=transport)
        assert module.COMMIT==c['code_commit'] and module.CANDIDATE==c['id']
        try: adapter.prepare(0)
        except module.Refused as error:
            reason=str(error)
        else: raise AssertionError('Registered-busy prepare unexpectedly succeeded')
        assert 'registered running task' in reason or 'reserved by active' in reason,reason
        assert not transport.calls and not (HERE/c['execution_directory']).exists()
        assert sha(ROOT/'pipeline/research_work.json')==work_before
        u.primary_protection(baseline);u.lifecycle_protection(baseline)
        record={
            'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,
            'candidate_id':c['id'],'code_commit':c['code_commit'],
            'native_op_preparation':c['operational_preparation'],
            'adapter_release':u.ref(op/'adapter_release.json'),
            'actual_call':{'operation':'Adapter.prepare','physical_gpu':0,'result':'refused','reason':reason},
            'registered_GPU0_task':'M217-CRE','original_PID':118189,
            'transport_calls':0,'active_binding_manifest_lease_created':False,
            'native_or_resources_executed':False,
            'separately_dated_physical_observation':u.ref(HERE/'cre_training_progress_observation.json'),
            'scope':'Actual reviewed preparation guard reached current source/version/owner/external anchors and refused locally for registered occupation. Separate physical proof has its own timestamp; neither is a FLOPs, native TRAIN2 or future idle PASS.'}
        path=HERE/(c['short']+'_actual_current_guard.json');u.save(path,record)
        results.append({'candidate_id':c['id'],'guard':u.ref(path),'reason':reason})
    guard();u.save(HERE/'current_resource_guard_result.json',{
        'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,
        'results':results,'transport_calls':0,'new_native_or_resources_commands':0,
        'primary_source_staging_and_lifecycle_preserved':True})
    print(json.dumps({'guards':results,'transport_calls':0},ensure_ascii=False))
if __name__=='__main__':main()
