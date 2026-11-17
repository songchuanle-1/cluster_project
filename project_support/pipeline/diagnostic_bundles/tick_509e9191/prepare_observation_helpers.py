"""Current readonly owner/observation rebinding, without native or model actions."""
from pathlib import Path
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_f15b261f'
EXPECTED={'token':'509e919168b1426b8ebfab88075116e2','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253',
 'generated_at':'2026-10-26T04:11:37.612490+00:00','deadline_at':'2026-10-26T05:11:37.612490+00:00',
 'context_sha256':'44050aa4a1004dbe8124ae02fe45f7b6ce0d748696c62f42491cf00cdf25c8a7',
 'pending_sha256':'813ed2630fe189a4d0a6e84d9aaacdd26b1a8896d724535e95ab7eaebc4dd4f8'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 owner=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'))
 assert {k:owner.get(k) for k in EXPECTED}==EXPECTED and os.environ.get('CODEX_THREAD_ID')==EXPECTED['thread_id']
 changes={'f15b261f91d845788f9187e85e699762':EXPECTED['token'],
 '2026-10-26T02:10:42.571429+00:00':EXPECTED['generated_at'],
 '2026-10-26T03:10:42.571429+00:00':EXPECTED['deadline_at'],
 'f4b9ce27ba27cd3e609a0301028b1b3bf4133a4967ae8e607fd76fd006ee6de0':EXPECTED['context_sha256'],
 '30f54a572a22fed635cafb12581bd8f71f36113f90859e8bd1d0d23e7c209846':EXPECTED['pending_sha256']}
 data=(OLD/'anchor_bfc_packet.py').read_bytes()
 for before,after in changes.items():
  assert data.count(before.encode())==1;data=data.replace(before.encode(),after.encode())
 ast.parse(data)
 with (HERE/'anchor_bfc_packet.py').open('xb') as f:f.write(data)
 from anchor_bfc_packet import guard
 guard();items=[{'file':'anchor_bfc_packet.py','source_sha256':sha(OLD/'anchor_bfc_packet.py'),'current_sha256':sha(HERE/'anchor_bfc_packet.py'),'change':'Only five actual current owner/snapshot constants. Same identity/policy/deadline guard.'}]
 for name in ['observe_active_runs.py','verify_protected_assets_v3.py']:
  data=(OLD/name).read_bytes();ast.parse(data)
  with (HERE/name).open('xb') as f:f.write(data)
  items.append({'file':name,'source_sha256':sha(OLD/name),'current_sha256':sha(HERE/name),'change':'Exact byte copy. Readonly snapshot/observation only; no uniqueness inference.'})
 with (HERE/'readonly_helper_provenance.json').open('x',encoding='utf8') as f:json.dump(items,f,indent=2);f.write('\n')
 print(json.dumps({'current_owner_guard':True,'readonly_helpers':2,'native_resources':'NOT_RUN'}))
if __name__=='__main__':main()
