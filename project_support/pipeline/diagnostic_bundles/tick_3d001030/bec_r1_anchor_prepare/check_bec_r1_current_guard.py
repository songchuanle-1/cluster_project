"""Disabled current R1 NoTransport software guard; never queries hardware."""
import argparse,importlib.util,json,sys
from pathlib import Path
from datetime import datetime,timezone
import anchor_bec_r1_static as common
def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--execute-root',action='store_true');a=p.parse_args()
    if not a.execute_root:print('DRAFT_DISABLED: no adapter import or guard call');return
    common.need(common.ENABLE_ROOT_EXECUTION,'Root-reviewed sibling copy must be enabled')
    common.owner_guard();common.validate_refs()
    result_path=common.TICK/'bec_r1_actual_local_guard.json';common.need(not result_path.exists(),'Existing guard result is not overwritten')
    anchored=common.read(common.TICK/'bec_r1_static_anchor_result.json')
    common.need(anchored['owner']==common.OWNER and anchored['code_commit']==common.NEW and anchored['other140_candidates_unchanged'] is True,'Current real static anchor result required')
    before=common.registered_state();worksha=common.sha(common.ROOT/'pipeline/research_work.json')
    execution=common.TICK/'bec_r1_execution';common.need(not execution.exists(),'Unexpected active execution directory; reconcile, do not test/overwrite')
    events=[]
    def audit(event,args):
        if event in ('subprocess.Popen','os.system','os.fork','os.posix_spawn','socket.connect','socket.bind','socket.getaddrinfo'):
            events.append(event);raise AssertionError('Process/network forbidden by NoTransport guard')
    sys.addaudithook(audit)
    class NoTransport:
        def __init__(self):self.calls=[]
        def call(self,*args,**kwargs):self.calls.append([str(x) for x in args[:1]]);raise AssertionError('NoTransport')
    transport=NoTransport();path=common.OP/'adapter.py'
    spec=importlib.util.spec_from_file_location('actual_reviewed_BEC_R1_adapter',path);module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter(transport=transport,execution_dir=str(execution))
    outcomes={}
    for gpu in (0,1):
        try:adapter.prepare(gpu)
        except module.Refused as error:outcomes[str(gpu)]={'refused':True,'reason':str(error)}
        else:raise AssertionError('A NoTransport preparation unexpectedly succeeded')
    common.need(outcomes['0']['reason']=='Selected GPU has registered running task','GPU0 did not reach expected currentowner/R1/external-anchor registeredCTSbusy guard')
    common.need('Explicit physical GPU0' in outcomes['1']['reason'],'GPU1 was not rejected by current0-only predicate')
    common.need(not transport.calls and not events and 'torch' not in sys.modules,'Transport/process/network/Torch was touched')
    common.need(not execution.exists() and common.registered_state()==before and common.sha(common.ROOT/'pipeline/research_work.json')==worksha,'Guard mutated active materials or shared state')
    common.owner_guard()
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':common.OWNER,'candidate_id':common.CID,'code_commit':common.NEW,'outcomes':outcomes,'transport_calls':0,'process_network_audit_events':events,'Torch_imported':False,'active_execution_directory_created':False,'shared_state_unchanged':True,'native':'NOT_RUN','resources':'NOT_RUN','scope':'Actual metadata/currentowner/reviewed-packet/source-registration guard only. Registeredbusy is not independent hardware/process observation.','material_concerns':[]}
    common.save(result_path,result)
    print(json.dumps({'status':'ACTUAL_CURRENT_R1_GUARDS_REFUSED_BUSY0_AND_UNAUTHORIZED1_WITHOUT_TRANSPORT','result':common.ref(result_path)},ensure_ascii=False))
if __name__=='__main__':main()
