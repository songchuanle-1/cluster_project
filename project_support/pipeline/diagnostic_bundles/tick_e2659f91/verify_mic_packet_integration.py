"""Root software integration check only: frozen source, coupled draft bindings, actual default-NOP."""
from pathlib import Path
from datetime import datetime,timezone
import sys,json,subprocess,os
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent
def main():
 if sys.argv[1:]!=['--execute-root']:print('DEFAULT_NOP');return
 guard();b=u.read(HERE/'protected_assets_before.json');u.protect(b)
 np=HERE/'mic_native_prepare/preparation.json';op=HERE/'mic_operational_prepare/preparation.json'
 assert sha(np)=='c88738fb8658c98a7c78c3ea7c0d436c3fe9486a8db23f06220557d0ec2651c3'
 assert sha(op)=='402705d7fe3762862a7556ea0dd748875ca46ef356807bf95269713ab709bf5c'
 n=u.read(np);o=u.read(op);v=u.read(HERE/'mic_version_prepare/isolated_source_version.json')
 for path,prep in [(np,n),(op,o)]:
  for name,h in prep['prepared_file_hashes'].items():
   f=(path.parent/name).resolve();assert f.is_relative_to(path.parent.resolve()) and sha(f)==h
   if f.suffix=='.py':compile(f.read_bytes(),str(f),'exec')
 assert n['source_files']==v['frozen_source_files'] and n['code_commit']==o['code_commit']==v['code_commit']=='041b63579888f2143cb9f3a5216ec4cff4ee8046'
 assert n['source_parent_commit']==o['source_parent_commit']==v['parent_commit']==b['head']
 assert o['native_preparation']==u.ref(np) and o['native_manifest_template']==n['manifest_template'] and o['native_protocol']==n['native_protocol']
 assert n['draft_execution_disabled'] is o['draft_execution_disabled'] is True and n['operational_ready'] is o['operational_ready'] is False
 m=u.read(ROOT/n['manifest_template']['path']);fields=['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit']
 assert {k for k,val in m.items() if val is None}==set(fields) and m['draft_execution_disabled'] is True
 assert m['code_commit']==v['code_commit'] and m['runtime_expected_commit']==b['head']
 assert u.read(ROOT/n['static_validation']['path'])['status']=='PASS_SOFTWARE_ONLY_NOT_NATIVE'
 cli=ROOT/o['root_launcher']['path'];command=[sys.executable,'-B','-X','utf8',str(cli)]
 guard();run=subprocess.run(command,capture_output=True,text=True,encoding='utf8',timeout=25,env=os.environ.copy())
 result={'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'command':command,'returncode':run.returncode,'stdout':run.stdout,'stderr':run.stderr,'native_preparation':u.ref(np),'operational_preparation':u.ref(op),'source_version':u.ref(HERE/'mic_version_prepare/isolated_source_version.json'),'scope':'Source/version/native draft/adapter cross-integration and actual default-NOP only; no Torch/model/SSH/GPU/native TRAIN/resources/efficacy.','passed':False}
 if run.returncode==0:
  value=json.loads(run.stdout);assert value['status']=='DEFAULT_NOP_NO_ENTRY_OR_TRANSPORT' and value['code_commit']==v['code_commit'] and value['native_executed'] is value['active_binding_created'] is False
  result['passed']=True
 u.protect(b);u.save(HERE/'mic_root_packet_integration_result.json',result)
 assert result['passed'],run.stderr
 print(json.dumps({'status':'ROOT_SOFTWARE_INTEGRATION_PASSED_NATIVE_NOT_RUN','evidence':u.ref(HERE/'mic_root_packet_integration_result.json')}))
if __name__=='__main__':main()
