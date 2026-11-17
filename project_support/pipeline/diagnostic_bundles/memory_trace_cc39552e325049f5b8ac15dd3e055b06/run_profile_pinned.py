"""Same frozen profile runner with project-local pinned profiler imports only."""
import ast
import json
import sys
from run import BUNDLE,guard,tick

guard()
setup=tick.load(BUNDLE/'profiler_dependencies.json')
assert setup['result']['import_passed']
source=BUNDLE/'followups.py'
dependency=setup['result']['target']
checks=setup['result']['critical_file_sha256']

class Pin(ast.NodeTransformer):
    def __init__(self):self.names=0;self.prefixes=0
    def visit_Constant(self,node):
        rename={'profile_baseline':'profile_counted_baseline','profile_independent':'profile_counted_independent'}
        if isinstance(node.value,str) and node.value in rename:
            self.names+=1
            return ast.Constant(rename[node.value])
        return node
    def visit_Assign(self,node):
        self.generic_visit(node)
        if any(isinstance(t,ast.Name) and t.id=='prefix' for t in node.targets):
            self.prefixes+=1
            extra='import hashlib\nprofiler_root=Path('+repr(dependency)+')\n'
            extra+='for name,sha in '+repr(checks)+'.items():\n assert hashlib.sha256((profiler_root/name).read_bytes()).hexdigest()==sha\n'
            extra+='sys.path.insert(0,str(profiler_root))\n'
            return [node]+ast.parse('prefix+='+repr(extra)).body
        return node

transform=Pin()
tree=transform.visit(ast.parse(source.read_text(encoding='utf-8')))
assert transform.names==3 and transform.prefixes==1
generated=ast.unparse(ast.fix_missing_locations(tree))
name=sys.argv[1]
assert name in ('profile_counted_baseline','profile_counted_independent')
generated_path=BUNDLE/(name+'_generated.py')
assert not generated_path.exists()
generated_path.write_text(generated,encoding='utf-8')
namespace={'__name__':'frozen_pinned_resource_runner','__file__':str(generated_path)}
exec(compile(generated,str(generated_path),'exec'),namespace)
try:
    namespace['main']()
except SystemExit:
    path=BUNDLE/(name+'_attempt.json')
    if path.exists():
        attempt=tick.load(path)
        attempt.update(pinned_wrapper_sha256=tick.digest(BUNDLE/'run_profile_pinned.py'),
            generated_runner_sha256=tick.digest(generated_path),
            profiler_setup_sha256=tick.digest(BUNDLE/'profiler_dependencies.json'))
        tick.save(path,attempt)
        result_path=BUNDLE/(name+'_result.json')
        if result_path.exists():
            result=tick.load(result_path)
            result['attempt_sha256']=tick.digest(path)
            tick.save(result_path,result)
    raise
