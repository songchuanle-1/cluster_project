"""Explicit root orchestration of externally anchored, unchanged PSBR adapter."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
import sys

ROOT=Path('D:/project/cluster_project')
HERE=Path(__file__).resolve().parent
TOKEN='dfb6440d1b69401da8e932239883e613'

def sha(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
def read(path):return json.loads(Path(path).read_text(encoding='utf-8'))
def ref(path):return {'path':Path(path).relative_to(ROOT).as_posix(),'sha256':sha(path)}
def save_new(path,data):
    with Path(path).open('x',encoding='utf-8') as stream:json.dump(data,stream,ensure_ascii=False,indent=2);stream.write('\n')

def main():
    owner=read(ROOT/'pipeline/headless/.foreground.lockdir/owner.json')
    assert owner['token']==TOKEN and owner['thread_id']==os.environ['CODEX_THREAD_ID']=='01a159c5-29ab-7a22-ba7f-e79174757253'
    assert datetime.now(timezone.utc)<datetime.fromisoformat(owner['deadline_at'])
    assert sha(ROOT/'pipeline/headless/.tick_context.json')==owner['context_sha256']
    assert sha(ROOT/'pipeline/headless/.tick_context_state.next.json')==owner['pending_sha256']
    c=next(c for c in read(ROOT/'pipeline/research_work.json')['candidates'] if c['id']=='hierarchy-parent-segmented-bidirectional-token-state')
    assert c['code_commit']=='74fcd21df0af9a971792038ffe251af1ffea2604'
    expected={
      ('worker_preparation','preparation'):'1e1de105f34ce4f6f87fe862bf35ee2c7c0bf26bf7404b0550559534a0e7472e',
      ('worker_preparation','worker'):'05ab6ac1f72f804bf9799e6b6a95127057d330d13302686740cb1acb94343385',
      ('worker_preparation','runtime'):'b6698c77ef9956c2d7381fb99164cdbf1d1f4905c13f59d04c6b9778e2bf8e67',
      ('worker_preparation','manifest_template'):'f90e2662cb188b838ff7e6d6b60179529a983d91a32cb06187262aee70267263',
      ('execution_adapter','preparation'):'9d6c98a4c406d052c5ae1d420053103b0ec08bf71fb0ce5c32de88dd49b5bb4b',
      ('execution_adapter','release'):'b17d424e493bcd49e1858bc6fc4b897d6fab5970a25240cea143e826f40e20d7',
      ('execution_adapter','adapter'):'c8aee02bc75986972b28b43e30b5333ca2ef30b75bdfc622ec5192e9b195b3a3',
      ('execution_adapter','remote_ops'):'9ea6f90d6027b83e92da24dcf0fd85cca548cb9b0aab726d9dd3ace52d1907cd',
    }
    anchors=[]
    for (section,key),value in expected.items():
        item=c[section][key];path=(ROOT/item['path']).resolve()
        assert path.is_relative_to(ROOT.resolve()) and item['sha256']==value==sha(path)
        anchors.append(item)
    prep_path=ROOT/c['worker_preparation']['preparation']['path'];prep=read(prep_path)
    for name,value in prep['prepared_file_hashes'].items():assert sha(prep_path.parent/name)==value
    for section,key in [('execution_adapter','independent_review'),('execution_adapter','independent_tests'),('execution_adapter','result_boundary_review')]:
        item=c[section][key];assert sha(ROOT/item['path'])==item['sha256'];anchors.append(item)
    adapter_path=ROOT/c['execution_adapter']['adapter']['path']
    operation=sys.argv[1]
    if operation=='prepare_stage':
        save_new(HERE/'psbr_current_external_anchor_check.json',{
            'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'external_anchors':anchors,
            'candidate_code_commit':c['code_commit'],'frozen_prepared_files_all_verified':True,
            'source_changes':False,'native_or_scientific_PASS':False})
    spec=importlib.util.spec_from_file_location('psbr_root_current_'+TOKEN,adapter_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter()
    if operation=='prepare_stage':
        binding=adapter.prepare(0)
        print(json.dumps({'phase':'prepare','token':binding['owner']['token'],'physical_gpu':binding['physical_gpu'],'runtime_code_commit':binding['runtime_code_commit'],'binding':ref(HERE/'psbr_execution/execution_binding.json')},ensure_ascii=False),flush=True)
        staged=adapter.stage()
        print(json.dumps({'phase':'stage','certainty':staged.get('certainty'),'verified':staged.get('verified'),'record':ref(HERE/'psbr_execution/stage_execution.json')},ensure_ascii=False),flush=True)
    elif operation=='run':
        mode,target=sys.argv[2:4]
        result=adapter.run(mode,target)
        print(json.dumps({'phase':'run','mode':mode,'target':target,'certainty':result.get('certainty'),
                          'returncode':result.get('returncode'),'execution_completed':result.get('result',{}).get('execution_completed'),
                          'record':ref(HERE/'psbr_execution'/(mode+'_'+target+'_execution.json'))},ensure_ascii=False),flush=True)
    else:raise ValueError('Unsupported explicit operation')

if __name__=='__main__':main()
