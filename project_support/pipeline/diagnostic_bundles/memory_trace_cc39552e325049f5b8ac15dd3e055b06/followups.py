"""Source-bound independent cohort followup and paired standard resources."""
import argparse
import ast
from datetime import datetime,timezone
import json
import subprocess
from run import BUNDLE,ROOT,TOKEN,guard,tick,Instrument
from independent_native import NativePackage,NAME,REMOTE,inspect_source

class SecondPair(ast.NodeTransformer):
    def __init__(self):self.batch=0
    def visit_Assign(self,node):
        self.generic_visit(node)
        if any(isinstance(t,ast.Name) and t.id=='batch' for t in node.targets):
            self.batch+=1
            return ast.parse("all_batches=list(DataLoader(Subset(dataset,[0,60,101,124]),batch_size=2,shuffle=False,num_workers=0,collate_fn=dataset.collate_fn))\nbatch=all_batches[1]\n").body
        if any(isinstance(t,ast.Name) and t.id=='result' for t in node.targets) and isinstance(node.value,ast.Dict):
            for index,key in enumerate(node.value.keys):
                if isinstance(key,ast.Constant) and key.value=='train_groups':
                    node.value.values[index]=ast.parse('[101,124]',mode='eval').body
        return node
    def visit_Constant(self,node):
        if node.value=='scene0000_00':return ast.Constant('scene0003_00')
        if node.value=='scene0002_00':return ast.Constant('scene0004_00')
        return node
    def visit_Assert(self,node):
        self.generic_visit(node)
        text=ast.unparse(node.test)
        if 'ann_ids' in text:
            return ast.parse("assert batch['scan_ids']==['scene0003_00','scene0004_00'] and batch['ann_ids']==[0,1,2,3,36,37,38,39]").body[0]
        if 'batch_offsets' in text:
            return ast.parse("assert batch['batch_offsets'].tolist()==[0,406,1847]").body[0]
        return node

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('name',choices=['native_second_independent','profile_baseline','profile_independent'])
    parser.add_argument('--timeout',type=int,default=420)
    args=parser.parse_args()
    owner=guard()
    name=args.name
    attempt=BUNDLE/(name+'_attempt.json')
    assert not attempt.exists()
    independent=name!='profile_baseline'
    tree=ast.parse((BUNDLE/'native_memory_frozen.py').read_text(encoding='utf-8'))
    if independent:
        inspect_source()
        transform=NativePackage()
        tree=transform.visit(tree)
        assert transform.count==1
    if name.startswith('profile_'):
        outer=[node for node in tree.body if isinstance(node,ast.Try)]
        assert len(outer)==1
        cut=[i for i,node in enumerate(outer[0].body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='retained' for t in node.targets)]
        assert len(cut)==1
        outer[0].body=outer[0].body[:cut[0]]+ast.parse((BUNDLE/'profile_worker.py').read_text(encoding='utf-8')).body
    else:
        second=SecondPair()
        tree=second.visit(tree)
        assert second.batch==1
        instrument=Instrument()
        tree=instrument.visit(tree)
        assert instrument.insertions==instrument.result_insertions==1
    payload=ast.unparse(ast.fix_missing_locations(tree))
    compile(payload,'<independent-followup>','exec')
    timeout=min(args.timeout,int((datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds())-120)
    assert timeout>30
    prefix='import signal,importlib.util,sys\nfrom pathlib import Path\nsignal.alarm('+str(timeout-15)+')\n'
    prefix+='FOREGROUND_TOKEN='+repr(TOKEN)+'\nFOREGROUND_DEADLINE='+repr(owner['deadline_at'])+'\nMEMORY_CONDITION="canonical_independent"\nPROFILE_CONDITION='+repr(name)+'\n'
    if independent:
        upload=tick.load(BUNDLE/'independent_upload.json')
        assert all(tick.digest(ROOT/item['path'])==item['sha256'] for item in upload['local_files'])
        prefix+='SOURCE_MANIFEST='+repr(upload['manifest'])+'\nDIAGNOSTIC_ROOT='+repr(REMOTE)+'\nDIAGNOSTIC_PACKAGE='+repr(NAME)+'\n'
        prefix+="def load_diagnostic_package():\n import hashlib,importlib\n root=Path(DIAGNOSTIC_ROOT)\n for name,sha in SOURCE_MANIFEST.items():\n  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha\n importlib.import_module('framework.model.Quard_model')\n qualified='framework.model.Quard_model.'+DIAGNOSTIC_PACKAGE\n spec=importlib.util.spec_from_file_location(qualified,root/DIAGNOSTIC_PACKAGE/'__init__.py',submodule_search_locations=[str(root/DIAGNOSTIC_PACKAGE)])\n module=importlib.util.module_from_spec(spec)\n sys.modules[qualified]=module\n spec.loader.exec_module(module)\n return module\n"
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=prefix+payload,
        text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    guard()
    tick.save(attempt,{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'runner_sha256':tick.digest(BUNDLE/'followups.py'),'worker_sha256':tick.digest(BUNDLE/'profile_worker.py'),
        'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1
        tick.save(BUNDLE/(name+'_result.json'),{'token':TOKEN,'attempt_sha256':tick.digest(attempt),**rows[0]})
        compact={key:value for key,value in rows[0].items() if key not in ('module_trace','source_manifest','observations')}
        if 'profile' in compact:compact['profile']={k:v for k,v in compact['profile'].items() if k!='by_module'}
        print(json.dumps(compact,ensure_ascii=False))
    else:print(process.stdout[-6000:])
    print(process.stderr[-5000:])
    print('returncode='+str(process.returncode))
    raise SystemExit(process.returncode)

if __name__=='__main__':main()
