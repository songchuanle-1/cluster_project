"""Root activates reviewed consumers in a fresh private directory, never source edits."""
from pathlib import Path
from datetime import datetime, timezone
import json, sys, hashlib
from anchor import ROOT, EXPECTED, guard, sha

HERE=Path(__file__).resolve().parent

def main():
    if sys.argv[1:]!=['--execute-root']:
        print('DEFAULT_NOP'); return
    guard()
    source=HERE/'lft_admission_prepare'
    active=HERE/'lft_admission_active'
    prep=source/'preparation.json'
    assert sha(prep)=='7d5fde6e5df4250e3cc8334f7143bce467d5d6733cc48a4ffc6975ea05620406'
    peers={
        'lft_admission_preparation_independent_review.json':'55063d90dfac22dccb79cb252620b857fc10049b6a0a330323edf04c67da9f34',
        'lft_actual_independent_review.json':'db71fff31d11327dad01a281166a2d92d78235740f9195747f4ca4ff22f24305'}
    for name,h in peers.items():
        assert sha(HERE/name)==h
        value=json.loads((HERE/name).read_text('utf8'))
        assert value['material_concerns']==[]
    preparation=json.loads(prep.read_text('utf8'))
    assert preparation['owner']==EXPECTED and preparation['draft_execution_disabled'] is True
    for name,h in preparation['prepared_file_hashes'].items():
        assert sha(source/name)==h, name
    names=['lft_evidence.py','summarize_lft_actual.py','fast_forward_tested_lft.py','admit_lft_queue.py','dispatch_lft_once.py','source_bindings.json','evidence_bindings.json']
    contents={name:(source/name).read_bytes() for name in names}
    assert contents['lft_evidence.py'].count(b'DRAFT_EXECUTION_DISABLED=True')==1
    contents['lft_evidence.py']=contents['lft_evidence.py'].replace(b'DRAFT_EXECUTION_DISABLED=True',b'DRAFT_EXECUTION_DISABLED=False')
    peer=json.loads((HERE/'lft_actual_independent_review.json').read_text('utf8'))
    bindings=json.loads(contents['evidence_bindings.json'])
    bindings['independent_review']={'path':(HERE/'lft_actual_independent_review.json').relative_to(ROOT).as_posix(),'sha256':peers['lft_actual_independent_review.json']}
    bindings['actual_raw_results']=[{'path':r['execution_path'],'sha256':r['execution_sha256']} for r in peer['raw_results']]
    for item in bindings['actual_raw_results']:
        assert sha(ROOT/item['path'])==item['sha256']
    bindings['scope']='Root-only active consumer copy, actual frozen four-arm peer and result SHA bound. No model/protocol/gate changes.'
    contents['evidence_bindings.json']=(json.dumps(bindings,ensure_ascii=False,indent=2)+'\n').encode('utf8')
    for name,data in contents.items():
        if name.endswith('.py'): compile(data,str(active/name),'exec')
    guard(); active.mkdir(exist_ok=False)
    for name,data in contents.items():
        guard()
        with (active/name).open('xb') as f: f.write(data)
    manifest={'recorded_at':datetime.now(timezone.utc).isoformat(),'owner':EXPECTED,'source_preparation':{'path':prep.relative_to(ROOT).as_posix(),'sha256':sha(prep)},'reviews':[{'path':(HERE/n).relative_to(ROOT).as_posix(),'sha256':h} for n,h in peers.items()],'active_hashes':{n:sha(active/n) for n in names},'code_delta':'One DRAFT execution switch only in copied lft_evidence.py; actual evidence references populated separately.','model_protocol_or_gate_changes':False}
    guard()
    with (HERE/'lft_consumer_activation.json').open('x',encoding='utf8') as f:json.dump(manifest,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'status':'ACTUAL_PEER_BOUND_ROOT_CONSUMERS_ACTIVE','manifest_sha256':sha(HERE/'lft_consumer_activation.json'),'active_directory':str(active)}))

if __name__=='__main__': main()
