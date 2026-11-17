"""Current creation budget is zero; only the two due reserves may gain evidence."""
from pathlib import Path
import hashlib,json
from anchor_bfc_packet import guard
HERE=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
    guard();p=HERE/'verify_protected_assets_v2.py';s=p.read_text('utf8')
    old="permitted={'hierarchy-parent-cyclic-triadic-state-composition','hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}"
    new="permitted={'hierarchy-parent-cyclic-triadic-state-composition','hierarchy-cross-level-bipartite-edge-composition','hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}"
    old2="assert added<={'hierarchy-cross-level-bipartite-edge-composition'}"
    assert s.count(old)==s.count(old2)==1
    target=HERE/'verify_protected_assets_v3.py'
    with target.open('x',encoding='utf8') as f:f.write(s.replace(old,new).replace(old2,'assert not added'))
    with (HERE/'protection_checker_scope.json').open('x',encoding='utf8') as f:
        json.dump({'source_sha256':sha(p),'current_sha256':sha(target),'only_changes':['Allow existing BEC evidence with CTS and two original running observation links','Require zero new candidate IDs: snapshot creation_budget0'],'run':'NOT_YET'},f,indent=2);f.write('\n')
    print('CURRENT_AFTER_CHECKER_READY_CREATION_ZERO')
if __name__=='__main__':main()
