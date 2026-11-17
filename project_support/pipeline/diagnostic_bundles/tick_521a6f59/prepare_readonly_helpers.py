"""Rebind readonly current foreground guard, never old execution leases."""
from pathlib import Path
import hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'tick_b5dc39b4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
    expected={'token':'521a6f59f2a74a69b41144aa6a8b6153','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
        'generated_at':'2026-10-26T00:11:01.066237+00:00','deadline_at':'2026-10-26T01:11:01.066237+00:00',
        'context_sha256':'0a031307be98484490bf98bff04e5d5a69c55a6438259ed529b85ef0d120b8a4',
        'pending_sha256':'88733c0d6724be1bb7369cdbbfb7a679e5f4fb957dd9a20a8e4a76362ca76d35'}
    assert {k:owner.get(k) for k in expected}==expected and os.environ.get('CODEX_THREAD_ID')==expected['thread_id']
    p=OLD/'anchor_bfc_packet.py';data=p.read_bytes()
    changes={b'b5dc39b4780a44c6855520bc22692b65':expected['token'].encode(),
        b'2026-10-25T22:11:14.827798+00:00':expected['generated_at'].encode(),
        b'2026-10-25T23:11:14.827798+00:00':expected['deadline_at'].encode(),
        b'7082c7c328d7e20f4ca107f32cd4df7929ffff12427ff0883774f2ec2f217f98':expected['context_sha256'].encode(),
        b'63ff0e9d20d0877f4a3b4d8a790e1881fac5db412656a9fc83e755eb104f18cf':expected['pending_sha256'].encode()}
    for before,after in changes.items():
        assert data.count(before)==1;data=data.replace(before,after)
    with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
    from anchor_bfc_packet import guard
    guard();items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(p),'current_sha256':sha(HERE/'anchor_bfc_packet.py'),
        'change':'Only five current owner/snapshot constants; actual thread/goal/grants/server/deadline validation unchanged.'}]
    for n in ['observe_active_runs.py','check_cts_actual_guard.py','verify_protected_assets_v3.py']:
        with (HERE/n).open('xb') as f:f.write((OLD/n).read_bytes())
        items.append({'file':n,'source_sha256':sha(OLD/n),'current_sha256':sha(HERE/n),'change':'Exact byte copy; current owner guard and output directory resolve locally. No unique-context claim.'})
    with (HERE/'readonly_helper_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
    print(json.dumps({'current_owner_guard':True,'readonly_helpers':3,'native':'NOT_RUN'}))
if __name__=='__main__':main()
