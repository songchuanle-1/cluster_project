"""Current owned tick: readonly source/ledger snapshot, no remote actions."""
from pathlib import Path
import hashlib,json,subprocess,sys
from datetime import datetime,timezone
from anchor_bfc_packet import guard

ROOT=Path('D:/project/cluster_project');HERE=Path(__file__).resolve().parent
PRIMARY=ROOT/'Cluster'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def git(*args):
    r=subprocess.run(['git','-C',str(PRIMARY),*args],capture_output=True,check=True)
    return r.stdout
def snapshot():
    guard()
    head=git('rev-parse','HEAD').decode().strip()
    assert head=='48fc302c3c02ffef0b241be3593c386b6b65a72e'
    assert git('diff','--cached','--name-only')==b''
    base=json.loads((ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json').read_text('utf8'))
    # Preserve baseline metadata in the snapshot without assuming its schema.
    status=git('status','--porcelain=v1','--untracked-files=all','-z')
    files={}
    parts=status.split(b'\0');i=0
    while i<len(parts) and parts[i]:
        row=parts[i].decode('utf8');i+=1
        kind=row[:2];rel=row[3:]
        p=PRIMARY/rel
        assert p.resolve().is_relative_to(PRIMARY.resolve())
        assert p.is_file(), 'Expected frozen protected files, not new directories'
        files[rel]=sha(p)
        if 'R' in kind or 'C' in kind:
            i+=1
    assert len(files)==28
    assert files=={item['path']:item['sha256'] for item in base['protected_existing_worktree']}
    names=['queue.json','running.json','experiments.csv','experiments/M206-CGCA.json',
           'experiments/M211-BTC.json','experiments/M212-BCR.json','experiments/M213-BFC.json',
           'admissions/M211-BTC.json','admissions/M212-BCR.json','admissions/M213-BFC.json']
    ledgers={n:sha(ROOT/'pipeline'/n) for n in names}
    work=json.loads((ROOT/'pipeline/research_work.json').read_text('utf8'))
    candidates={c['id']:hashlib.sha256(json.dumps(c,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()).hexdigest() for c in work['candidates']}
    return {'observed_at':datetime.now(timezone.utc).isoformat(),'head':head,
            'index_empty':True,'status_hex':status.hex(),'files':files,'protected_ledgers':ledgers,
            'candidate_digests':candidates,'historical_baseline_sha256':sha(ROOT/'pipeline/diagnostic_bundles/tick_16b87793/protected_worktree_before.json')}
def main():
    mode=sys.argv[1];assert mode in ['before','after']
    x=snapshot()
    if mode=='after':
        b=json.loads((HERE/'protected_assets_before.json').read_text('utf8'))
        assert all(b[k]==x[k] for k in ['head','index_empty','status_hex','files','protected_ledgers','historical_baseline_sha256'])
        permitted={'hierarchy-parent-cyclic-triadic-state-composition','hierarchy-parent-butterfly-token-composition','hierarchy-parent-bidirectional-complement-recurrence'}
        changed=[k for k,v in b['candidate_digests'].items() if x['candidate_digests'].get(k)!=v]
        assert set(changed)<=permitted
        added=set(x['candidate_digests'])-set(b['candidate_digests'])
        assert added<={'hierarchy-cross-level-bipartite-edge-composition'}
        assert set(b['candidate_digests'])<=set(x['candidate_digests'])
        x.update(changed_existing_candidates=changed,new_candidates=sorted(added),protected_assets_unchanged=True)
    out=HERE/('protected_assets_'+mode+'.json')
    with out.open('x',encoding='utf8') as f: json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'mode':mode,'protected_files':len(x['files']),'protected_ledgers':len(x['protected_ledgers']),'head':x['head'],'sha256':sha(out),'changed_existing_candidates':x.get('changed_existing_candidates',[]),'new_candidates':x.get('new_candidates',[])}))
if __name__=='__main__':main()
