"""Private activation from real APF source/packet and four-result peer; no public action."""
from pathlib import Path
from datetime import datetime,timezone
import argparse,json,os
from anchor import ROOT,EXPECTED,guard,sha
import record_utils as u
HERE=Path(__file__).resolve().parent;ORIGIN=HERE/'apf_admission_prepare';DEST=HERE/'apf_admission_execute';OP=HERE/'apf_compatible_prepare'
COMMIT='d0e2f95712ed16446907706fbf6a65d34996a9ad';BASE='6282263d805c1741234f97afc981a05aca2ad6e3'
FILES=('apf_evidence.py','summarize_apf_actual.py','fast_forward_tested_apf.py','admit_apf_queue.py','dispatch_apf_once.py','source_bindings.json','evidence_bindings.json')

def main():
 ap=argparse.ArgumentParser();ap.add_argument('--execute-root',action='store_true');ap.add_argument('--peer-sha256');args=ap.parse_args()
 if not args.execute_root:print('DEFAULT_READ_ONLY_NO_ACTIVATION');return
 guard();assert sha(ORIGIN/'preparation.json')=='7997545f29136bad4bfcce65f20057b9eb35d7bcd3ebed88c670987a0e02ef73'
 prep=u.read(ORIGIN/'preparation.json')
 for n,h in prep['prepared_file_hashes'].items():assert sha(ORIGIN/n)==h
 source_review=HERE/'apf_root_admission_preparation_independent_review.json';assert sha(source_review)=='49aad28e1f5bc916799350e73d741a5b67035261297948c3d72efdfd1de859f0' and u.read(source_review)['material_concerns']==[]
 peer=HERE/'apf_actual_independent_review.json';assert sha(peer)==args.peer_sha256
 actual=u.read(peer);assert actual['status']=='FOUR_ACTUAL_APF_NATIVE_AND_RESOURCE_RESULT_SEMANTICS_INDEPENDENTLY_VALIDATED' and actual['candidate_id']==u.APF and actual['code_commit']==COMMIT and actual['material_concerns']==[]
 assert len(actual['raw_results'])==4 and {(x['mode'],x['target']) for x in actual['raw_results']}=={(m,t) for m in ('smoke','resources') for t in ('champion','candidate')}
 for r in actual['raw_results']:
  p=(ROOT/r['execution_path']).resolve();assert p.parent==HERE/'apf_execution' and sha(p)==r['execution_sha256']
  env=u.read(p);assert env['certainty']=='terminal' and env['returncode']==0 and env['result']['execution_completed'] is True and env['result']['code_commit']==COMMIT and env['identity']['request_id']==r['request_id'] and env['result_sha256']==r['result_sha256']
 version=OP/'version_prepare/isolated_source_version.json';v=u.read(version);assert v['code_commit']==COMMIT and v['parent_commit']==BASE and v['diff_exact9A']
 native=OP/'native/preparation.json';n=u.read(native);assert n['source_commit']==COMMIT and n['source_parent_commit']==BASE and n['source_files']==v['frozen_source_files']
 payload={name:(ORIGIN/name).read_bytes() for name in FILES};old={name:sha(ORIGIN/name) for name in FILES}
 assert payload['apf_evidence.py'].count(b'DRAFT_EXECUTION_DISABLED=True')==1
 payload['apf_evidence.py']=payload['apf_evidence.py'].replace(b'DRAFT_EXECUTION_DISABLED=True',b'DRAFT_EXECUTION_DISABLED=False')
 bind=u.read(ORIGIN/'source_bindings.json');assert bind['code_commit'] is None and bind['parent_commit']==BASE
 bind.update(code_commit=COMMIT,native_preparation=u.ref(native),manifest_template=u.ref(OP/'native/manifest_template.json'),source_version=u.ref(version))
 assert u.read(ORIGIN/'evidence_bindings.json')=={'independent_review':None}
 payload['source_bindings.json']=(json.dumps(bind,indent=2)+'\n').encode('utf8')
 payload['evidence_bindings.json']=(json.dumps({'independent_review':u.ref(peer)},indent=2)+'\n').encode('utf8')
 for name,data in payload.items():
  if name.endswith('.py'):compile(data,str(DEST/name),'exec')
 assert not DEST.exists() and not any((HERE/n).exists() for n in ('apf_root_activation_intent.json','apf_root_activation_result.json'))
 u.save(HERE/'apf_root_activation_intent.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'original_preparation':u.ref(ORIGIN/'preparation.json'),'actual_peer':u.ref(peer),'source_version':u.ref(version),'original_file_hashes':old,'scope':'Private exact-copy only. Only disabled flag and actual source/native/peer references differ; no summary/source/Git/ledger/remote/queue operation.'})
 guard();DEST.mkdir()
 for name,data in payload.items():
  guard()
  with (DEST/name).open('xb') as f:f.write(data);f.flush();os.fsync(f.fileno())
 assert all(sha(DEST/name)==old[name] for name in FILES if name not in ('apf_evidence.py','source_bindings.json','evidence_bindings.json'))
 u.save(HERE/'apf_root_activation_result.json',{'owner':EXPECTED,'recorded_at':datetime.now(timezone.utc).isoformat(),'actual_peer':u.ref(peer),'activated_file_hashes':{n:sha(DEST/n) for n in FILES},'unchanged_executable_bytes_except_explicit_flag':True,'no_public_or_Git_remote_native_action':True})
 print('Real APF evidence-bound private helpers activated; no public action performed.')
if __name__=='__main__':main()
