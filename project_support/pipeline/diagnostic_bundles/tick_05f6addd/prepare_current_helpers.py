"""New-owner binding only; unchanged BEC observer and protected14 snapshot."""
from pathlib import Path
from datetime import datetime,timezone
import ast,hashlib,json,os
ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent;OLD=HERE.parent/'tick_60d21b33'
CURRENT={'token':'05f6addd722d487fbdc663753af44b83','thread_id':'01a159c5-29ab-7a22-ba7f-e79174757253','generated_at':'2026-10-26T18:03:58.499009+00:00','deadline_at':'2026-10-26T19:03:58.499009+00:00','context_sha256':'d0147dba3ffb0d882678ef296d197719f646161fffa234016e1145d722057524','pending_sha256':'5f43cb9dc67b0af3ec3b86b4d2ff17e02acfe858c13edded8cc3df0ca2cc7c9a'}
BEFORE={'token':'60d21b3324c94445b26d2ecb24a3ba65','generated_at':'2026-10-26T16:09:41.027895+00:00','deadline_at':'2026-10-26T17:09:41.027895+00:00','context_sha256':'062a6fc0ddeba051336890fe88f3d2d0382d2036f7afc139f368da2568334c23','pending_sha256':'c3ef64975c4c76f8c4febbcdc09867e2c133dbd465aab18a834238cafcf98cb4'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 o=json.loads((ROOT/'pipeline/headless/.foreground.lockdir/owner.json').read_text('utf8'));assert {k:o.get(k) for k in CURRENT}==CURRENT and os.environ.get('CODEX_THREAD_ID')==CURRENT['thread_id'];assert datetime.now(timezone.utc)<datetime.fromisoformat(CURRENT['deadline_at'])
 records=[]
 for n in ['anchor_bfc_packet.py','verify_protected_assets.py','observe_bec_training_progress.py']:
  b=(OLD/n).read_bytes();before=b
  if n=='anchor_bfc_packet.py':
   for k,v in BEFORE.items():assert b.count(v.encode())==1;b=b.replace(v.encode(),CURRENT[k].encode())
  ast.parse(b)
  with (HERE/n).open('xb') as f:f.write(b)
  records.append({'file':n,'old_sha256':sha(OLD/n),'new_sha256':sha(HERE/n),'change':'Only current owner5' if before!=b else 'Byte exact'})
 with (HERE/'current_helpers_provenance.json').open('x',encoding='utf8') as f:json.dump(records,f,indent=2);f.write('\n')
 from anchor_bfc_packet import guard
 guard();print('CURRENT_ROOT_READONLY_HELPERS_READY')
if __name__=='__main__':main()
