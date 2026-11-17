"""Execute the preregistered shared-prefix controls and actual native probes."""
import argparse
import ast
import copy
from datetime import datetime,timezone
import json
import subprocess
from run import BUNDLE,PRIOR,TOKEN,guard,tick,Instrument

class Install(ast.NodeTransformer):
    def __init__(self):self.count=0
    def visit_Assign(self,node):
        self.generic_visit(node)
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='train':
            return node
        return node
    def visit_Expr(self,node):
        self.generic_visit(node)
        if self.count==0 and isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and node.value.func.attr=='zero_grad':
            self.count+=1
            return [node]+ast.parse("helper={}\nexec(compile(REMATERIALIZATION_SOURCE,'<shared-prefix-revision2>','exec'),helper)\ninstalled_prefix_modules=helper['install_prefix_rematerialization'](model.dec)\nassert len(installed_prefix_modules)==10\n").body
        return node

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('name',choices=['revision2_controls','revision2_baseline','revision2_canonical'])
    parser.add_argument('--timeout',type=int,default=360)
    args=parser.parse_args()
    owner=guard()
    candidate=next(c for c in tick.load(BUNDLE.parent.parent/'research_work.json')['candidates'] if c['id']=='m95-hierarchical-mask-feature-path-audit')
    assert len(candidate['revision_history'])==2 and candidate['revision_history'][-1]['result']=='pending'
    name=args.name
    attempt=BUNDLE/(name+'_attempt.json')
    assert not attempt.exists()
    condition='canonical' if name.endswith('canonical') else 'baseline'
    source=BUNDLE/'native_memory_frozen.py'
    tree=ast.parse(source.read_text(encoding='utf-8'))
    if name=='revision2_controls':
        outer=[node for node in tree.body if isinstance(node,ast.Try)]
        assert len(outer)==1
        cut=[i for i,node in enumerate(outer[0].body) if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='retained' for t in node.targets)]
        assert len(cut)==1
        outer[0].body=outer[0].body[:cut[0]]+ast.parse((BUNDLE/'revision2_controls.py').read_text(encoding='utf-8')).body
    else:
        install=Install()
        tree=install.visit(tree)
        assert install.count==1
        instrument=Instrument()
        tree=instrument.visit(tree)
        assert instrument.insertions==instrument.result_insertions==1
    payload=ast.unparse(ast.fix_missing_locations(tree))
    compile(payload,'<revision2-native>','exec')
    timeout=min(args.timeout,int((datetime.fromisoformat(owner['deadline_at'])-datetime.now(timezone.utc)).total_seconds())-120)
    assert timeout>30
    prefix='import signal\nsignal.alarm('+str(timeout-15)+')\n'
    prefix+='FOREGROUND_TOKEN='+repr(TOKEN)+'\nFOREGROUND_DEADLINE='+repr(owner['deadline_at'])+'\nMEMORY_CONDITION='+repr(condition)+'\n'
    helper=BUNDLE/'rematerialization.py'
    prefix+='REMATERIALIZATION_SOURCE='+repr(helper.read_text(encoding='utf-8'))+'\n'
    if condition=='canonical':prefix+='CANONICAL_SOURCE='+repr((PRIOR/'canonical_readout.py').read_text(encoding='utf-8'))+'\n'
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=prefix+payload,
        text=True,encoding='utf-8',capture_output=True,timeout=timeout)
    guard()
    tick.save(attempt,{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'runner_sha256':tick.digest(BUNDLE/'run_revision2.py'),'helper_sha256':tick.digest(helper),
        'source_sha256':tick.digest(source),'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1
        tick.save(BUNDLE/(name+'_result.json'),{'token':TOKEN,'attempt_sha256':tick.digest(attempt),**rows[0]})
        print(json.dumps({key:value for key,value in rows[0].items() if key not in ('records','module_trace')},ensure_ascii=False))
    else:print(process.stdout[-7000:])
    print(process.stderr[-5000:])
    print('returncode='+str(process.returncode))
    raise SystemExit(process.returncode)

if __name__=='__main__':main()
