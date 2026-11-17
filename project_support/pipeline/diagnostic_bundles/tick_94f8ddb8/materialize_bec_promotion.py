"""Exact four reviewed helpers, single enable flag in a new execution sibling."""
from pathlib import Path
import ast,hashlib,json
from run_next_bec_arm import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 guard();src=HERE/'bec_promotion_prepare';dst=HERE/'bec_promotion_execute'
 assert sha(src/'preparation.json')=='1b834fbd1fe1fda534fe5982bc01e2f26e3d4e5992d2888ebb44c314c7dbe376'
 assert sha(HERE/'bec_r1_actual_four_result_independent_review.json')=='46c47d4983a31205d710be5889e7e9e812bd4d3649865edef60c5f046b4c0a36'
 assert sha(HERE/'bec_r1_actual_four_result_review.json')=='89099675a78da788f8186968102de364901859110f68ad8cd7bb45065ee798e0'
 expected={'promotion_common.py':'58a02986c0797474ef4c46c3f2a696c490a3e37513ab1e19ce0c05be0ee734aa','fast_forward_tested_bec.py':'9840b71d1ebdb4eab7eb88365e2d15808ef46521a46c94dcdca9750ebe1ba316','admit_bec_queue.py':'20c0e8fbea96014903fd08c463af4f4024e5d111db2060f02fcc080f2136ebc0','dispatch_bec.py':'072a3cb7777674a54e0c781b19e6b1bf8e21c9dd6baa158793f155eed24d6870'}
 assert all(sha(src/n)==h for n,h in expected.items());assert not dst.exists();dst.mkdir()
 items=[]
 for n,h in expected.items():
  before=(src/n).read_bytes();after=before
  if n=='promotion_common.py':
   assert before.count(b'DRAFT_EXECUTION_ENABLED = False')==1
   after=before.replace(b'DRAFT_EXECUTION_ENABLED = False',b'DRAFT_EXECUTION_ENABLED = True')
   assert after.replace(b'DRAFT_EXECUTION_ENABLED = True',b'DRAFT_EXECUTION_ENABLED = False')==before
  ast.parse(after)
  with (dst/n).open('xb') as f:f.write(after)
  items.append({'file':n,'prepared_sha256':h,'execution_sha256':sha(dst/n),'difference':'Single enable flag' if before!=after else 'Byte exact'})
 with (dst/'materialization.json').open('x',encoding='utf8') as f:json.dump({'owner_token':'94f8ddb8a6e049c48c8e6237f4c737e8','four_sources':items,'only_common_enable_flag_changed':True,'operation_executed':False},f,indent=2)
 guard();print(json.dumps({'status':'REVIEWED_SINGLE_FLAG_EXECUTION_COPY_READY','path':str(dst)}))
if __name__=='__main__':main()
