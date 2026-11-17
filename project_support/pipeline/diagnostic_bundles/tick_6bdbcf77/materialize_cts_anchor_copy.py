"""Root-reviewed one-flag copy for static CTS catalog anchoring only."""
from pathlib import Path
import hashlib,json
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();source=HERE/'cts_anchor_prepare/anchor_cts_packet.py'
    assert sha(source)=='ebc4a66c62de1842a8d8e20db066f855151010d13783d79489a5e20183f981f9'
    review=HERE/'cts_operational_final_review.json'
    assert sha(review)=='0fc1425f083ea48299e25de7fe5dca188d09c7a705611b2944403720d18acc74'
    assert json.loads(review.read_text('utf8'))['material_concerns']==[]
    data=source.read_bytes();assert data.count(b'DRAFT_EXECUTION_ENABLED=False')==1
    target=HERE/'cts_anchor_execute';target.mkdir(exist_ok=False)
    p=target/'anchor_cts_packet.py'
    with p.open('xb') as f:f.write(data.replace(b'DRAFT_EXECUTION_ENABLED=False',b'DRAFT_EXECUTION_ENABLED=True'))
    out={'source_sha256':sha(source),'execution_copy_sha256':sha(p),
         'exact_only_change':'DRAFT_EXECUTION_ENABLED=False -> True',
         'root_independent_review':'Reviewed actual source: fixed6owner/hash/originaldeadline, frozen51cbc/42map/native14/worker03329/61proof, real4e8vs48fc, MDC0fc142 review anchors, primary28status+bytes/index/13ledgers, exactBFC0/BCR1/M206pause, canonicalprojectlock, exclusiveintent/catalog/result and atomicCTS-only ledger mutation. No native/source/GPU/queue action.',
         'actual_static_anchor_execution':'NOT_RUN','native_resources':'NOT_RUN'}
    with (target/'execution_preparation.json').open('x',encoding='utf8') as f:json.dump(out,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(out))
if __name__=='__main__':main()
