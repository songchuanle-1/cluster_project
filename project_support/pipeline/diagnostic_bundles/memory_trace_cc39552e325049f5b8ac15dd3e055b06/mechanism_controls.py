"""Current independent readout, exact prefix, matched mechanism controls."""
import ast
from datetime import datetime,timezone
import json
import subprocess
from run import BUNDLE,PRIOR,ROOT,TOKEN,guard,tick
from independent_native import NAME,REMOTE,inspect_source

class Transform(ast.NodeTransformer):
    def __init__(self):self.modules=0;self.interventions=0;self.support=0
    def visit_Constant(self,node):
        if node.value=='m95':return ast.Constant('canonical')
        if node.value=='content':return ast.Constant('ancestor')
        return node
    def visit_FunctionDef(self,node):
        if node.name=='intervention':
            self.interventions+=1
            return ast.parse((BUNDLE/'mechanism_intervention.py').read_text(encoding='utf-8')).body[0]
        return self.generic_visit(node)
    def visit_If(self,node):
        if ast.unparse(node.test)=='pair == 0' and 'gradient_hook' in ast.unparse(node):return []
        return self.generic_visit(node)
    def visit_Assign(self,node):
        self.generic_visit(node)
        names={target.id for target in node.targets if isinstance(target,ast.Name)}
        if 'mod' in names and isinstance(node.value,ast.Call):
            self.modules+=1
            return ast.parse('mod=load_diagnostic_package()').body[0]
        if 'hierarchy' in names:
            return ast.parse("hierarchy=importlib.import_module('framework.model.Quard_model.'+DIAGNOSTIC_PACKAGE+'.hier_postprocess')").body[0]
        if 'result' in names and isinstance(node.value,ast.Dict):
            for index,key in enumerate(node.value.keys):
                if isinstance(key,ast.Constant) and key.value=='scope':
                    node.value.values[index]=ast.Constant('Current independent canonical versus matched uniform/ancestor supports on exact native prefix; diagnostic task response and branch coverage, not trained efficacy. Full native backwards are separate records.')
            node.value.keys.extend([ast.Constant('support_statistics'),ast.Constant('source_independent_model'),ast.Constant('source_package')])
            node.value.values.extend([ast.Name('support_statistics',ast.Load()),ast.Constant(True),ast.Constant(NAME)])
        return node
    def visit_Expr(self,node):
        self.generic_visit(node)
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute) and isinstance(node.value.func.value,ast.Name) and node.value.func.value.id=='originals' and node.value.func.attr=='append':
            self.support+=1
            return [node]+ast.parse("support_statistics.extend(describe_support(pair,frozen['cluster'][5]))").body
        return node

def main():
    owner=guard()
    inspect_source()
    assert tick.load(BUNDLE/'independent_native_result.json')['outcome']['passed_this_diagnostic']
    assert tick.load(BUNDLE/'native_second_independent_result.json')['outcome']['passed_this_diagnostic']
    attempt=BUNDLE/'mechanism_controls_attempt.json'
    assert not attempt.exists()
    source=PRIOR/'native_suffix_probe.py'
    transform=Transform()
    tree=transform.visit(ast.parse(source.read_text(encoding='utf-8')))
    assert transform.modules==transform.interventions==transform.support==1
    payload=ast.unparse(ast.fix_missing_locations(tree))
    prefix='import os,signal,importlib.util,sys\nos.environ["CUDA_VISIBLE_DEVICES"]="1"\nfrom pathlib import Path\nsignal.alarm(345)\n'
    prefix+='FOREGROUND_TOKEN='+repr(TOKEN)+'\nFOREGROUND_DEADLINE='+repr(owner['deadline_at'])+'\n'
    upload=tick.load(BUNDLE/'independent_upload.json')
    assert all(tick.digest(ROOT/item['path'])==item['sha256'] for item in upload['local_files'])
    prefix+='SOURCE_MANIFEST='+repr(upload['manifest'])+'\nDIAGNOSTIC_ROOT='+repr(REMOTE)+'\nDIAGNOSTIC_PACKAGE='+repr(NAME)+'\n'
    prefix+="def load_diagnostic_package():\n import hashlib,importlib\n root=Path(DIAGNOSTIC_ROOT)\n for name,sha in SOURCE_MANIFEST.items():\n  assert hashlib.sha256((root/name).read_bytes()).hexdigest()==sha\n importlib.import_module('framework.model.Quard_model')\n qualified='framework.model.Quard_model.'+DIAGNOSTIC_PACKAGE\n spec=importlib.util.spec_from_file_location(qualified,root/DIAGNOSTIC_PACKAGE/'__init__.py',submodule_search_locations=[str(root/DIAGNOSTIC_PACKAGE)])\n module=importlib.util.module_from_spec(spec)\n sys.modules[qualified]=module\n spec.loader.exec_module(module)\n return module\n"
    extra=ast.parse((BUNDLE/'mechanism_intervention.py').read_text(encoding='utf-8')).body[1]
    prefix+='CONTROL_CORE={}\nexec('+repr((PRIOR/'canonical_readout.py').read_text(encoding='utf-8'))+',CONTROL_CORE)\nsupport_statistics=[]\n'+ast.unparse(extra)+'\n'
    compile(prefix+payload,'<independent-mechanism-controls>','exec')
    process=subprocess.run(['ssh','-o','BatchMode=yes','-o','StrictHostKeyChecking=yes','-o','ConnectTimeout=8',
        'server-3','/home/songcl/.conda/envs/3d-stmn/bin/python','-B','-'],input=prefix+payload,
        text=True,encoding='utf-8',capture_output=True,timeout=360)
    guard()
    tick.save(attempt,{'token':TOKEN,'recorded_at':datetime.now(timezone.utc).isoformat(),
        'runner_sha256':tick.digest(BUNDLE/'mechanism_controls.py'),'control_sha256':tick.digest(BUNDLE/'mechanism_intervention.py'),
        'source_sha256':tick.digest(source),'returncode':process.returncode,'stdout':process.stdout,'stderr':process.stderr})
    rows=[json.loads(line.split('=',1)[1]) for line in process.stdout.splitlines() if line.startswith('HIER_NATIVE_RESULT=')]
    if rows:
        assert len(rows)==1
        tick.save(BUNDLE/'mechanism_controls_result.json',{'token':TOKEN,'attempt_sha256':tick.digest(attempt),**rows[0]})
        print(json.dumps({key:value for key,value in rows[0].items() if key not in ('records','original_captures','resources')},ensure_ascii=False))
    else:print(process.stdout[-6000:])
    print(process.stderr[-5000:])
    print('returncode='+str(process.returncode))
    raise SystemExit(process.returncode)

if __name__=='__main__':main()
