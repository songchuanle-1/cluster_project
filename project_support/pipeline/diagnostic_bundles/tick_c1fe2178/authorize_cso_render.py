"""Create a render-only receipt after actual collect and independent review."""
from pathlib import Path
from datetime import datetime, timezone
import argparse,base64,hashlib,json,os
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
def read(p): return json.loads(p.read_text(encoding='utf-8-sig'))
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    p=argparse.ArgumentParser();p.add_argument('--execute-root',action='store_true');a=p.parse_args()
    if not a.execute_root: print('{"status":"DEFAULT_NOP"}');return
    owner=read(HERE/'current_owner_binding.json');live=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert {k:live[k] for k in owner}==owner and owner['thread_id']==os.environ['CODEX_THREAD_ID']
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    collected=HERE/'cso_setup_execution_v2/collect_actual.json';reviewed=HERE/'peer_review/cso_collect_v2_actual_independent_review.json'
    d=read(collected);o=d['observation'];r=read(reviewed)
    assert d['owner']==owner and d['certainty']=='terminal' and d['ssh_returncode']==o['returncode']==0
    assert o['result'] is not None
    raw=base64.b64decode(o['remote_result_bytes_base64'],validate=True)
    assert hashlib.sha256(raw).hexdigest()==o['remote_result_sha256']
    assert json.loads(raw)==o['result']
    assert r['owner']==owner and r['passed'] is True and r['material_concerns']==[]
    assert r['reviewer_thread_id'] not in (owner['thread_id'],'/root','/root/cso_readiness','/root/cso_native_ops')
    assert r['collect_actual_sha256']==sha(collected) and r['actual_observation_sha256']==o['remote_result_sha256']
    assert r['source_commit']=='5413102c57b526035f3920b5e7a81f3b58ad764d'
    admission=ROOT/'pipeline/admissions/M236-CSO.json'
    receipt=dict(decision='ALLOW_PRODUCTION_PATH_RENDER',owner=owner,source_commit=r['source_commit'],
        recorded_at=datetime.now(timezone.utc).isoformat(),actual_observation_sha256=o['remote_result_sha256'],
        admission_receipt_sha256=sha(admission),independent_observation_review_sha256=sha(reviewed),
        training_launch_authorized=False,render_only=True,
        producer_sha256=sha(Path(__file__)),prior_failed_producer_preserved=True)
    dest=HERE/'cso_render_activation_v2.actual.json'
    with dest.open('x',encoding='utf8') as f: json.dump(receipt,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(dict(path=str(dest),sha256=sha(dest),decision=receipt['decision'],training_launch_authorized=False)))
if __name__=='__main__': main()
