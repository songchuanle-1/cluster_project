"""Root-only local formatter for actual BFC status/reconcile console evidence.

Never calls an adapter, SSH, subprocess, GPU, native model or shared mutation.
Default validates only. --execute-root exclusively writes two new diagnostics.
"""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import hashlib
import json
import os

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
CID='hierarchy-parent-butterfly-token-composition'
COMMIT='48fc302c3c02ffef0b241be3593c386b6b65a72e'
UUIDS={0:'GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c',1:'GPU-7f82edb9-f620-8045-caea-a75232265cd1'}
THREAD='01a159c5-29ab-7a22-ba7f-e79174757253'
PAIRS=[('smoke','champion'),('smoke','candidate'),('resources','champion'),('resources','candidate')]


def need(value,message):
    if not value:raise ValueError(message)


def read(path):
    def reject(value):raise ValueError('Nonstandard JSON number: '+value)
    return json.loads(Path(path).read_text(encoding='utf-8-sig'),parse_constant=reject)


def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def ref(path):
    path=Path(path).resolve();need(path.is_relative_to(ROOT),'Evidence outside project')
    return {'path':path.relative_to(ROOT).as_posix(),'sha256':sha(path)}


def linux_json_sha(value):
    return hashlib.sha256(json.dumps(value,indent=2,allow_nan=False).encode('utf-8')).hexdigest()


def remote_state(remote,binding):
    need(remote['stage']==binding['stage'] and remote['exists'] is True and remote['read_only'] is True,'Wrong/missing original remote stage')
    need(remote['native_manifest_sha256']==binding['native_manifest_sha256'] and remote['binding_token']==binding['owner']['token'],'Remote original manifest/token mismatch')
    need(remote['workers']==[],'Actual remote stage still has workers')
    need(isinstance(remote['compute_contexts'],str) and not remote['compute_contexts'].strip(),'Actual selected GPU contexts are not empty')
    inventory=remote['gpu_inventory'];need(isinstance(inventory,str),'Missing actual selected GPU inventory')
    rows=[line for line in inventory.splitlines() if line.strip()]
    need(len(rows)==1 and [x.strip() for x in rows[0].split(',')][:2]==[str(binding['physical_gpu']),UUIDS[binding['physical_gpu']]] and remote['gpu_identity_matches'] is True,'Wrong actual physicalselected GPU UUID inventory')


def match_original(item,request,envelope):
    identity=envelope['identity']
    need(item['request']==request and item['request_sha256']==linux_json_sha(request) and item['identity_matches'] is True,'Original remote/local request differs')
    for flag in ('started_identity_matches','started_command_matches','completed_identity_matches','completed_command_matches','completed_result_identity_matches','result_identity_matches'):
        need(item[flag] is True,'Actual remote identity/command/result observation failed: '+flag)
    need(item['completed']==envelope and item['completed_sha256']==linux_json_sha(envelope),'Original complete remote/local terminal envelope differs')
    need(item['result']==envelope['result'] and item['result_sha256']==envelope['result_sha256']==linux_json_sha(envelope['result']),'Original complete remote/local result or serialization hash differs')
    start=item['started']
    need(start['identity']==identity and start['command']==envelope['command'] and start['pid']==envelope['pid'],'Original started identity/command/PID differs')
    need(start['process_identity']==envelope['original_process_identity'],'Original PID/start-ticks observation differs')
    need(item['original_pid_still_same'] is False,'Original worker process remains same; reconcile instead')
    need(envelope['certainty']=='terminal' and type(envelope['returncode']) is int and envelope['returncode']==0 and envelope['result']['execution_completed'] is True,'Original native request did not actually finish rc0/completed')


def validate(tick,execution):
    tick=Path(tick).resolve();execution=Path(execution).resolve()
    need(tick.is_relative_to(ROOT/'pipeline/diagnostic_bundles') and execution.parent==tick,'Unexpected diagnostic/execution location')
    binding=read(execution/'execution_binding.json');status_path=tick/'status_after_four_console.json';status=read(status_path)
    need(binding['candidate_id']==CID and binding['code_commit']==COMMIT and type(binding['physical_gpu']) is int and binding['physical_gpu'] in UUIDS and binding['gpu_uuid']==UUIDS[binding['physical_gpu']],'Foreign BFC/selected GPU binding')
    need(binding['stage']=='/data/songcl/Project/Cluster_project/pipeline/bfc_'+binding['owner']['token'][:8]+'_gpu'+str(binding['physical_gpu']),'Foreign selected GPU stage prefix')
    need(status['binding']==binding and status['binding_is_current'] is True and status['current_owner_token']==binding['owner']['token'],'Status is not from the original current binding')
    need(sha(execution/'native_manifest.json')==binding['native_manifest_sha256'] and sha(execution/'execution_lease.json')==binding['execution_lease_sha256'],'Original manifest/lease bytes changed')
    remote=status['remote'];remote_state(remote,binding)
    run_items=[x for x in remote['requests'] if x.get('request',{}).get('operation')=='run']
    need(len(run_items)==4,'Unexpected extra or missing original stage run requests')
    records=[];reconcile_refs=[];request_ids=[]
    for mode,target in PAIRS:
        arm=mode+'_'+target;request=read(execution/(arm+'_request.json'));envelope=read(execution/(arm+'_execution.json'));identity=envelope['identity']
        expected={'project':'cluster_project','candidate_id':CID,'code_commit':COMMIT,'stage':binding['stage'],'token':binding['owner']['token'],'request_id':request['request_id'],'operation':'run','physical_gpu':binding['physical_gpu'],'gpu_uuid':binding['gpu_uuid'],'native_manifest_sha256':binding['native_manifest_sha256']}
        need(identity==expected and request==dict(expected,mode=mode,target=target),'Original immutable request/envelope identity mismatch')
        raw=envelope['result'];need((raw['mode'],raw['target'],raw['candidate_id'],raw['code_commit'],raw['physical_gpu'],raw['gpu_uuid'])==(mode,target,CID,COMMIT,binding['physical_gpu'],binding['gpu_uuid']),'Original raw mode/target/source/GPU differs')
        matches=[x for x in run_items if x['request']['request_id']==request['request_id']];need(len(matches)==1,'Status original request ambiguous/missing')
        match_original(matches[0],request,envelope)
        reconcile_path=tick/('reconcile_'+arm+'_console.json');reconcile=read(reconcile_path);remote_state(reconcile,binding)
        selected=[x for x in reconcile['requests'] if x.get('request',{}).get('request_id')==request['request_id']]
        need(len(selected)==1 and len(reconcile['requests'])==1,'Filtered reconcile did not select exactly the original request')
        match_original(selected[0],request,envelope)
        request_ids.append(request['request_id']);reconcile_refs.append(ref(reconcile_path))
        records.append({'mode':mode,'target':target,'request_id':request['request_id'],'pid':envelope['pid'],'start_ticks':envelope['original_process_identity']['start_ticks'],'certainty':envelope['certainty'],'returncode':envelope['returncode'],'remote_result_sha256':envelope['result_sha256'],'local_execution':ref(execution/(arm+'_execution.json')),'original_process_still_same':False,'identity_and_full_result_objects_match':True,'actual_reconcile_evidence':ref(reconcile_path)})
    need(len(set(request_ids))==4,'Original native request IDs are not unique')
    return status_path,binding,records,reconcile_refs


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--tick-dir',default=str(HERE));parser.add_argument('--execution-dir');parser.add_argument('--execute-root',action='store_true');args=parser.parse_args()
    tick=Path(args.tick_dir).resolve();execution=Path(args.execution_dir).resolve() if args.execution_dir else tick/'bfc_execution'
    status_path,binding,records,reconcile_refs=validate(tick,execution)
    if not args.execute_root:
        print(json.dumps({'status':'ACTUAL_INPUTS_VALIDATED_NO_DIAGNOSTICS_WRITTEN','original_requests':len(records),'physical_gpu':binding['physical_gpu']}));return
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    keys={'token','thread_id','generated_at','deadline_at','context_sha256','pending_sha256'}
    need(set(binding['owner'])==keys and binding['owner']=={k:owner[k] for k in keys} and owner['thread_id']==os.environ.get('CODEX_THREAD_ID')==THREAD,'Actual exact owning root environment/six-field binding required; never override thread identity')
    need(datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at']),'Actual original deadline expired')
    need(sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256'] and sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256'],'Actual owner context/pending changed')
    output_status=tick/'bfc_status_after_four.json';output_history=tick/'bfc_native_operation_history.json'
    need(not output_status.exists() and not output_history.exists(),'Existing output requires read-only reconciliation; never overwrite/replay')
    # Every input was validated before either new output is created.
    with output_status.open('xb') as stream:stream.write(status_path.read_bytes())
    result={'recorded_at':datetime.now(timezone.utc).isoformat(),'token':binding['owner']['token'],'candidate_id':CID,'code_commit':COMMIT,'physical_gpu':binding['physical_gpu'],'gpu_uuid':binding['gpu_uuid'],'same_original_requests_reconciled_read_only':records,'workers_after':[],'selected_gpu_contexts_after':[],'status_evidence':ref(output_status),'original_status_console':ref(status_path),'reconcile_console_evidence':reconcile_refs,'no_additional_run_requests_in_saved_original_stage':True,'blind_relaunch_performed_by_this_helper':False,'signals_sent_by_this_helper':False,'lease_extended_or_mutated_by_this_helper':False,'other_physical_GPU':'NOT_QUERIED_NOT_USED_BY_THIS_HELPER','helper':ref(Path(__file__)),'scope':'Only actual root-produced status and four filtered reconcile console JSON files were consumed and matched to original local full request/terminal/result objects and Linux serialization hashes. Empty workers/selected GPU contexts come from those real remote observations, never from local PID absence. One saved reconcile per arm is recorded; total historical CLI invocation count is not inferred from files. This is operational history, not native scientific PASS, admission or a future idle/lease grant.'}
    with output_history.open('x',encoding='utf-8') as stream:json.dump(result,stream,ensure_ascii=False,indent=2,allow_nan=False);stream.write('\n')
    print(json.dumps({'status':'ACTUAL_OPERATION_HISTORY_FORMATTED','requests':len(records),'status_sha256':sha(output_status),'history_sha256':sha(output_history),'native_PASS_or_admission_created':False}))


if __name__=='__main__':main()
