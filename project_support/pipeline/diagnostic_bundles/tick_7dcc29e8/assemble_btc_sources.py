"""Copy exact already-versioned BTC sources into an unexecuted native packet."""
from pathlib import Path
from datetime import datetime,timezone
import copy,hashlib,json,os,subprocess
ROOT=Path('D:/project/cluster_project'); HERE=Path(__file__).resolve().parent
DEST=HERE/'btc_operational_prepare/native'
COMMIT='00e2b18c6b8d568a64edb496e6979d766440883c'; PARENT='43dce016c1a1713c2a5dab7061810dc2efde8954'
CID='hierarchy-parent-binary-tree-complement-composition'; TOKEN='7dcc29e8844245ec87b6d58eee6ec966'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,x):
    with p.open('x',encoding='utf-8') as f:json.dump(x,f,ensure_ascii=False,indent=2);f.write('\n')
def git(*args):return subprocess.check_output(['git','-C',str(ROOT/'Cluster'),*args],text=True,encoding='utf-8').strip()
def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    original=ROOT/'pipeline/diagnostic_bundles/tick_2c25f38f/new_candidate_prepare/preparation.json'
    assert sha(original)=='c36b4d095ee3d48510a1064f699b2fe41be33569aaefb917d873a45c484d0814'
    prep=read(original); sources={p.removeprefix('staged_repository/'):h for p,h in prep['prepared_file_hashes'].items() if p.startswith('staged_repository/')}
    assert len(sources)==9 and git('rev-parse','HEAD')==PARENT and git('show','-s','--format=%P',COMMIT)==PARENT
    assert set(git('diff-tree','--no-commit-id','--name-status','-r',COMMIT).splitlines())=={'A\t'+p for p in sources}
    assert not git('diff','--cached','--name-only')
    dest_model=DEST/'candidate_model'; dest_model.mkdir(parents=True,exist_ok=True)
    hashes={}; config=None
    for name,expected in sources.items():
        src=original.parent/'staged_repository'/name
        blob=subprocess.check_output(['git','-C',str(ROOT/'Cluster'),'show',COMMIT+':'+name])
        assert sha(src)==expected and hashlib.sha256(blob).hexdigest()==expected and blob==src.read_bytes()
        if name.endswith('.yaml'):target=DEST/'candidate.yaml'; config=name
        else:target=dest_model/Path(name).name; hashes[target.name]=expected
        with target.open('xb') as f:f.write(blob)
    assert len(hashes)==8 and config is not None
    proof={'schema_version':1,'candidate_id':CID,'experiment_id':'M211-BTC','code_commit':COMMIT,'parent_commit':PARENT,
        'change_scope':'exact9added independent BTC files only; primary/runtime43 retained while PSNC trains',
        'source_files':sources,'candidate_source_hashes':hashes,'candidate_config_sha256':sources[config],
        'original_source_preparation_sha256':sha(original),'verified_at':datetime.now(timezone.utc).isoformat(),
        'verification':'Actual local Git00e parent/diff-tree/all9 git-show bytes checked against immutable source preparation; no source edits, Git mutation, remote work or execution.'}
    save(DEST/'source_version_binding.json',proof)
    old=ROOT/'pipeline/diagnostic_bundles/tick_42ce600b/psnc_operational_prepare/native/manifest_template.json'
    manifest=copy.deepcopy(read(old))
    manifest.update(candidate_id=CID,candidate_name=manifest['name']+'_btc',experiment_id='M211-BTC',code_commit=COMMIT,
        config=config,candidate_source_hashes=hashes,candidate_config_sha256=sources[config],
        protocol='Version-bound BTC original native TRAIN2 and unchanged resources; fresh owning guard/assets/binding/lease and idle authorizedGPU0 required. Offline preparation is not native PASS.',
        source_preparation_sha256=sha(original),source_version_commit=COMMIT,source_parent_commit=PARENT,
        source_version_binding_sha256=sha(DEST/'source_version_binding.json'),diagnostic_files={})
    assert all(manifest[k] is None for k in ['current_token','stage','tick_generated_at','deadline_at','physical_gpu','gpu_uuid','allowed_gpus','context_sha256','pending_sha256','runtime_code_commit'])
    save(HERE/'btc_manifest_skeleton.json',manifest)
    text='''# BTC native preparation scope\n\nExact existing BTC00e candidate sources and original native YAML. No source, seed, schedule, data or model update is authorized by this packet.\n\nFuture smoke uses original tools/train.py for two TRAIN steps, matched M95 input/initialization and actual inside/outside/leaf path, gradients and parameter updates. True supported n>=3 groups are needed for inside loss reachability. Missing coverage is not whole-mechanism falsification. No extra loss, backward or mechanism replacement.\n\nFuture resources retain the original fvcore handlers, bs1/lang1/warm20/repeat100 and full unsupported disclosure. Counted cost is not all actual work; pure training memory and efficacy remain unknown until measured.\n\nEverything here is unexecuted. No lease, active binding, GPU use, receipt, admission, queue item or launch is created by preparation. Future actual owner/context/deadline, authorization/assets/UUID/live idleGPU0 and three locks remain mandatory; no GPU1 use or disturbance of PSNC/M206.\n'''
    with (DEST/'README.md').open('x',encoding='utf-8') as f:f.write(text)
    save(HERE/'btc_source_packet_binding.json',{'recorded_at':datetime.now(timezone.utc).isoformat(),'source_commit':COMMIT,
        'runtime_primary_retained':git('rev-parse','HEAD'),'candidate_files':9,'source_version_binding_sha256':sha(DEST/'source_version_binding.json'),
        'manifest_is_skeleton_only':True,'worker_or_adapter_tested':False,'native_or_resources_executed':False,'active_binding_created':False})
    print(json.dumps({'source_files':9,'source_commit':COMMIT,'primary_HEAD':git('rev-parse','HEAD'),'binding_sha256':sha(DEST/'source_version_binding.json'),'execution':'NOT_RUN'}))
if __name__=='__main__':main()
