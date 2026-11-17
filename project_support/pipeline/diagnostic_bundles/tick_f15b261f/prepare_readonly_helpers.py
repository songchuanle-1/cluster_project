"""Bind readonly observation helpers to this foreground lease; no GPU execution."""
from pathlib import Path
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
OLD=HERE.parent/'tick_521a6f59'
EXPECTED={'token':'f15b261f91d845788f9187e85e699762','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
 'generated_at':'2026-10-26T02:10:42.571429+00:00','deadline_at':'2026-10-26T03:10:42.571429+00:00',
 'context_sha256':'f4b9ce27ba27cd3e609a0301028b1b3bf4133a4967ae8e607fd76fd006ee6de0',
 'pending_sha256':'30f54a572a22fed635cafb12581bd8f71f36113f90859e8bd1d0d23e7c209846'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
 assert {k:owner.get(k) for k in EXPECTED}==EXPECTED and os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 changes={'521a6f59f2a74a69b41144aa6a8b6153':EXPECTED['token'],
 '2026-10-26T00:11:01.066237+00:00':EXPECTED['generated_at'],
 '2026-10-26T01:11:01.066237+00:00':EXPECTED['deadline_at'],
 '0a031307be98484490bf98bff04e5d5a69c55a6438259ed529b85ef0d120b8a4':EXPECTED['context_sha256'],
 '88733c0d6724be1bb7369cdbbfb7a679e5f4fb957dd9a20a8e4a76362ca76d35':EXPECTED['pending_sha256']}
 data=(OLD/'anchor_bfc_packet.py').read_bytes()
 for before,after in changes.items():
  assert data.count(before.encode())==1;data=data.replace(before.encode(),after.encode())
 ast.parse(data)
 with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
 from anchor_bfc_packet import guard
 guard();items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(OLD/'anchor_bfc_packet.py'),'current_sha256':sha(HERE/'anchor_bfc_packet.py'),'change':'Only five current owner/snapshot constants; same actual identity/policy/assets/deadline guard.'}]
 for n in ['observe_active_runs.py','check_cts_actual_guard.py','check_bec_actual_guard.py','verify_protected_assets_v3.py']:
  data=(OLD/n).read_bytes();change='Exact byte copy; current guard and new private output directory resolve locally.'
  if n=='check_bec_actual_guard.py':
   before=b"PACKET=HERE/'bec_operational_prepare'";after=b"PACKET=HERE.parent/'tick_521a6f59/bec_operational_prepare'"
   assert data.count(before)==1;data=data.replace(before,after);change='Only packet path points to previous frozen BEC catalog; no worker/protocol/software-suite changes.'
  ast.parse(data)
  with (HERE/n).open('xb') as f:f.write(data)
  items.append({'file':n,'source_sha256':sha(OLD/n),'current_sha256':sha(HERE/n),'change':change})
 with (HERE/'readonly_helper_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 print(json.dumps({'current_owner_guard':True,'readonly_helpers':4,'native_resources':'NOT_RUN'}))
if __name__=='__main__':main()
