"""Explicit root orchestration of externally anchored, unchanged HRC adapter."""
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
    c=next(c for c in read(ROOT/'pipeline/research_work.json')['candidates'] if c['id']=='hierarchy-bottom-up-refined-token-composition')
    assert c['code_commit']=='74fcd21df0af9a971792038ffe251af1ffea2604'
    expected={
      ('worker_preparation','preparation'):'87ef65ab7ac065688879bc0587a26ef1704d001a8190086ba55b2d005f6ae8e1',
      ('worker_preparation','worker'):'37782c1ae1ea9cb2f7bb77d59c7b8aff926438fbac827106f94d8c8fa396ef01',
      ('worker_preparation','runtime'):'cd71a8be1a91988931ee147aadd86a4f9d0e10f23f938c49df2ecbdfc46f3943',
      ('worker_preparation','manifest_template'):'41ed6ca1e60b61eaaa0a379c930e457eb7b09d5d9abaebc59143867864346bec',
      ('execution_adapter','preparation'):'f2ed5b65c0d673ec1ef38ed67fc52905aac9e6a1c1cdfd8b0145ac0978e8395a',
      ('execution_adapter','release'):'7aa68337a4aa653e4bc55d0fff2c4e0a1fa84ac3fda7d968732ddd1bf93c1b23',
      ('execution_adapter','adapter'):'e061cb634d167dc71c641908113522e47995bcae532dde29c936153dbf9f1eda',
      ('execution_adapter','remote_ops'):'78e5035e55b4e580912049d729d2888b7f5b4604231fa7d054cdf1ce0db62c6b',
    }
    anchors=[]
    for (section,key),value in expected.items():
        item=c[section][key];path=(ROOT/item['path']).resolve()
        assert path.is_relative_to(ROOT.resolve()) and item['sha256']==value==sha(path)
        anchors.append(item)
    prep_path=ROOT/c['worker_preparation']['preparation']['path'];prep=read(prep_path)
    for name,value in prep['prepared_file_hashes'].items():assert sha(prep_path.parent/name)==value
    for section,key in [('execution_adapter','root_review'),('execution_adapter','independent_tests'),('execution_adapter','final_activation_review')]:
        item=c[section][key];assert sha(ROOT/item['path'])==item['sha256'];anchors.append(item)
    adapter_path=ROOT/c['execution_adapter']['adapter']['path']
    operation=sys.argv[1]
    if operation=='prepare_stage':
        save_new(HERE/'hrc_current_external_anchor_check.json',{
            'recorded_at':datetime.now(timezone.utc).isoformat(),'token':TOKEN,'external_anchors':anchors,
            'candidate_code_commit':c['code_commit'],'frozen_prepared_files_all_verified':True,
            'source_changes':False,'native_or_scientific_PASS':False})
    spec=importlib.util.spec_from_file_location('hrc_root_current_'+TOKEN,adapter_path)
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    adapter=module.Adapter()
    if operation=='prepare_stage':
        binding=adapter.prepare(0)
        print(json.dumps({'phase':'prepare','token':binding['owner']['token'],'physical_gpu':binding['physical_gpu'],'runtime_code_commit':binding['runtime_code_commit'],'binding':ref(HERE/'hrc_execution/execution_binding.json')},ensure_ascii=False),flush=True)
        staged=adapter.stage()
        print(json.dumps({'phase':'stage','certainty':staged.get('certainty'),'verified':staged.get('verified'),'record':ref(HERE/'hrc_execution/stage_execution.json')},ensure_ascii=False),flush=True)
    elif operation=='run':
        mode,target=sys.argv[2:4]
        result=adapter.run(mode,target)
        print(json.dumps({'phase':'run','mode':mode,'target':target,'certainty':result.get('certainty'),
                          'returncode':result.get('returncode'),'execution_completed':result.get('result',{}).get('execution_completed'),
                          'record':ref(HERE/'hrc_execution'/(mode+'_'+target+'_execution.json'))},ensure_ascii=False),flush=True)
    else:raise ValueError('Unsupported explicit operation')

if __name__=='__main__':main()
