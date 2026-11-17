"""Bind only current owner guard; reuse unchanged readonly observer/guard helpers."""
from pathlib import Path
import hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PREVIOUS=HERE.parent/'tick_f86d1cfa'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
    expected={'token':'b5dc39b4780a44c6855520bc22692b65','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
        'generated_at':'2026-10-25T22:11:14.827798+00:00','deadline_at':'2026-10-25T23:11:14.827798+00:00',
        'context_sha256':'7082c7c328d7e20f4ca107f32cd4df7929ffff12427ff0883774f2ec2f217f98',
        'pending_sha256':'63ff0e9d20d0877f4a3b4d8a790e1881fac5db412656a9fc83e755eb104f18cf'}
    assert {k:owner.get(k) for k in expected}==expected and os.environ.get('CODEX_THREAD_ID')==expected['thread_id']
    source=PREVIOUS/'anchor_bfc_packet.py';data=source.read_bytes()
    changes={b'f86d1cfaf966476db888f6ba553b74d1':expected['token'].encode(),
        b'2026-10-25T20:07:28.056644+00:00':expected['generated_at'].encode(),
        b'2026-10-25T21:07:28.056644+00:00':expected['deadline_at'].encode(),
        b'c6809cf39c22a0ea25df9822dc0718aeb66a246830deff9f377c010f6361f557':expected['context_sha256'].encode(),
        b'c823df5297a5bcfcbf28bc3c730977a3e87ebbea7b2050eee6482fc1f22f505e':expected['pending_sha256'].encode()}
    for old,new in changes.items():
        assert data.count(old)==1;data=data.replace(old,new)
    with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
    from anchor_bfc_packet import guard
    guard();items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(source),'current_sha256':sha(HERE/'anchor_bfc_packet.py'),
        'change':'Only current token/generated/deadline/context/pending constants; actual thread identity and all authorization/goal/resource guards unchanged.'}]
    for name in ['observe_active_runs.py','check_cts_actual_guard.py','verify_protected_assets_v3.py']:
        source=PREVIOUS/name
        with (HERE/name).open('xb') as f:f.write(source.read_bytes())
        items.append({'file':name,'source_sha256':sha(source),'current_sha256':sha(HERE/name),'change':'Exact bytes; current guard and current output directory resolve from current __file__.'})
    with (HERE/'readonly_helper_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
    print(json.dumps({'current_owner_guard':True,'readonly_helpers':3,'native':'NOT_RUN'}))
if __name__=='__main__':main()
