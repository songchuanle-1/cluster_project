"""Private exact DCE helper activation only after actual four-result peer."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;ORIGIN=HERE/'dce_admission_prepare';DEST=HERE/'dce_admission_execute';NATIVE=HERE/'dce_native_prepare'
COMMIT='5c0c211c8ecc9479ecb34dbb8118a95f4b20e391';BASE=u.SOURCE
FILES=('dce_evidence.py','summarize_dce_actual.py','fast_forward_tested_dce.py','admit_dce_queue.py','dispatch_dce_once.py','source_bindings.json','evidence_bindings.json')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer-sha256');a=ap.parse_args()
 if not a.execute_root:print('DEFAULT_READ_ONLY_NO_ACTIVATION');return
 guard();assert sha(ORIGIN/'preparation.json')=='4694f66a67ebceb8ed0b6a55424a8f51b3be79e97787fe39f71d0e14057bd0eb'
 p=u.read(ORIGIN/'preparation.json')
 for n,h in p['prepared_file_hashes'].items():assert sha(ORIGIN/n)==h
 review=HERE/'dce_root_admission_preparation_independent_review.json';assert sha(review)=='7c06da3b638d51dfb75942e3a47f26e3e3caf2281384580dc115bce29a9b9abb' and u.read(review)['material_concerns']==[]
 peer=HERE/'dce_actual_independent_review.json';assert sha(peer)==a.peer_sha256
 actual=u.read(peer);assert actual['status']=='FOUR_ACTUAL_DCE_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED' and actual['candidate_id']=='hierarchy-directed-cavity-edge-composition' and actual['code_commit']==COMMIT and actual['material_concerns']==[]
 assert len(actual['raw_results'])==4 and {(x['mode'],x['target']) for x in actual['raw_results']}=={(m,t) for m in ('smoke','resources') for t in ('champion','candidate')}
 for r in actual['raw_results']:
  f=(ROOT/r['execution_path']).resolve();assert f.parent==HERE/'dce_execution' and sha(f)==r['execution_sha256']
  e=u.read(f);assert e['certainty']=='terminal' and e['returncode']==0 and e['result']['execution_completed'] is True and e['result']['code_commit']==COMMIT and e['identity']['request_id']==r['request_id'] and e['result_sha256']==r['result_sha256']
 version=HERE/'dce_version_prepare/isolated_source_version.json';v=u.read(version);assert v['code_commit']==COMMIT and v['parent_commit']==BASE and v['diff_exact9A']
 native=NATIVE/'preparation.json';n=u.read(native);assert n['source_commit']==COMMIT and n['source_parent_commit']==BASE and n['source_files']==v['frozen_source_files']
 payload={name:(ORIGIN/name).read_bytes() for name in FILES};old={name:sha(ORIGIN/name) for name in FILES}
 assert payload['dce_evidence.py'].count(b'DRAFT_EXECUTION_DISABLED=True')==1
 payload['dce_evidence.py']=payload['dce_evidence.py'].replace(b'DRAFT_EXECUTION_DISABLED=True',b'DRAFT_EXECUTION_DISABLED=False')
 bind=u.read(ORIGIN/'source_bindings.json');assert bind['code_commit']==COMMIT and bind['parent_commit']==BASE and bind['native_preparation'] is None and bind['manifest_template'] is None
 bind.update(native_preparation=u.ref(native),manifest_template=u.ref(NATIVE/'manifest_template.json'),source_version=u.ref(version))
 assert u.read(ORIGIN/'evidence_bindings.json')=={'independent_review':None}
 payload['source_bindings.json']=(json.dumps(bind,indent=2)+'\n').encode('utf8');payload['evidence_bindings.json']=(json.dumps({'independent_review':u.ref(peer)},indent=2)+'\n').encode('utf8')
 for name,data in payload.items():
  if name.endswith('.py'):compile(data,str(DEST/name),'exec')
 assert not DEST.exists() and not any((HERE/n).exists() for n in ('dce_root_activation_intent.json','dce_root_activation_result.json'))
 u.save(HERE/'dce_root_activation_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'original_preparation':u.ref(ORIGIN/'preparation.json'),'actual_peer':u.ref(peer),'source_version':u.ref(version),'original_file_hashes':old,'scope':'Private bytecopy; only common disabled flag and actual native/template/peer references change. No summaries/source/Git/ledger/remote/queue operation.'})
 guard();DEST.mkdir()
 for name,data in payload.items():
  guard()
  with (DEST/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert all(sha(DEST/name)==old[name] for name in FILES if name not in ('dce_evidence.py','source_bindings.json','evidence_bindings.json'))
 u.save(HERE/'dce_root_activation_result.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'actual_peer':u.ref(peer),'activated_file_hashes':{n:sha(DEST/n) for n in FILES},'unchanged_executable_bytes_except_explicit_flag':True,'no_public_or_Git_remote_native_action':True})
 print('Real four-result DCE evidence-bound private helpers activated; no public action.')
if __name__=='__main__':main()
