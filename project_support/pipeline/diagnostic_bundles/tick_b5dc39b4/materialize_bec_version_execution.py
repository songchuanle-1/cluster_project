"""Root-reviewed one-flag copy for local BEC source version save only."""
from pathlib import Path
import hashlib,json
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();source=HERE/'bec_version_prepare/prepare_isolated_bec_version.py';prep_path=source.parent/'preparation.json'
    assert sha(source)=='ee60a50e4ee91d47b224114aa0c5c66fcafc727a0d600160ffb8f533d2dc447a'
    assert sha(prep_path)=='dc19cba8ac24dfab5c4d0ce914a84ff895a0ccb7b7aedbd911c57df85be8ff39'
    prep=json.loads(prep_path.read_text('utf8'))
    for n,h in prep['prepared_file_hashes'].items():
        p=(source.parent/n).resolve();assert p.is_relative_to(source.parent.resolve()) and sha(p)==h
    review_path=HERE/'bec_source_version_helper_review.json'
    assert sha(review_path)=='2c17587db00d1c8f377726e41f45eca387439c7ad709e318843fd3f5eac9adf8'
    review=json.loads(review_path.read_text('utf8'));assert review['material_concerns']==[]
    assert review['anchors']['preparation']['sha256']==sha(prep_path) and review['anchors']['helper']['sha256']==sha(source)
    data=source.read_bytes();assert data.count(b'DRAFT_EXECUTION_ENABLED=False')==1
    target=HERE/'bec_version_execute';target.mkdir(exist_ok=False)
    p=target/source.name
    with p.open('xb') as f:f.write(data.replace(b'DRAFT_EXECUTION_ENABLED=False',b'DRAFT_EXECUTION_ENABLED=True'))
    result={'source_sha256':sha(source),'execution_copy_sha256':sha(p),'only_change':'DRAFT_EXECUTION_ENABLED=False -> True',
        'root_review':'Actual full helper source reviewed: current owner/deadline/context/goal/standingauth/canonical lock, tested48fcBFC/receipt/fourarm lineage; exact2d06 nine additions in fresh detached worktree only; primary28/index/HEAD and13+4 lifecycle records protected; CTS4e8 and oldnative322c protected before each mutation and after commit; exclusive journal/no replay; sibling relationship/no ff assumption. No remote/native/GPU/process/scheduler operation.',
        'static_helper_review_sha256':sha(review_path),'actual_Git_source_save':'NOT_RUN','native_resources':'NOT_RUN'}
    with (target/'execution_preparation.json').open('x',encoding='utf8') as f:json.dump(result,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps(result))
if __name__=='__main__':main()
