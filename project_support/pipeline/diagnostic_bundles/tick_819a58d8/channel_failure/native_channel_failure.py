"""Single prespecified failure measurement; keep original strict gate."""
import ast
from native_runtime import STAGE
tree=ast.parse((STAGE/'channel_template.py').read_text())
counts={'batch':0,'readout':0,'gate':0,'record':0,'status':0,'name':0}
class Probe(ast.NodeTransformer):
    def visit_For(self,node):
        self.generic_visit(node)
        if isinstance(node.target,ast.Name) and node.target.id=='b':
            node.iter=ast.parse('range(1)',mode='eval').body
            counts['batch']+=1
        elif isinstance(node.target,ast.Name) and node.target.id=='index':
            node.iter=ast.parse('(valid-1,)',mode='eval').body
            counts['readout']+=1
        return node
    def visit_Assert(self,node):
        self.generic_visit(node)
        if 'remote_null' in ast.unparse(node.test):
            counts['gate']+=1
            return ast.parse("r['strict_null_gate_passed'] = record['conditions']['remote_null']['message_max_absolute_change'] <= 1e-6").body[0]
        return node
    def visit_Assign(self,node):
        self.generic_visit(node)
        if any(isinstance(t,ast.Name) and t.id=='record' for t in node.targets):
            counts['record']+=1
            extra="""cx=x.detach().clone()
cx[b,remote]=cx[b,remote]+directions[0]
actual_point_change=(cx[b,remote]-x[b,remote]).detach().cpu().double()
native_mean_shift=(cx.mean(1)[b]-x.mean(1)[b]).detach().cpu().double()
exact_mean_shift=actual_point_change/x.shape[1]
record['float32_cast_centered_null_residual']=float((centered@directions[0].detach().cpu().double()).abs().max())
record['centered_actual_mean_shift_max']=float((centered@native_mean_shift).abs().max())
record['centered_exact_point_change_over_N_max']=float((centered@exact_mean_shift).abs().max())
record['mean_reduction_rounding_linf']=float((native_mean_shift-exact_mean_shift).abs().max())
del cx
"""
            return [node,*ast.parse(extra).body]
        return node
    def visit_Call(self,node):
        self.generic_visit(node)
        if isinstance(node.func,ast.Attribute) and isinstance(node.func.value,ast.Name) and node.func.value.id=='r' and node.func.attr=='update':
            for k in node.keywords:
                if k.arg=='passed' and isinstance(k.value,ast.Constant) and k.value.value is True:
                    counts['status']+=1
                    k.value=ast.parse("r['strict_null_gate_passed']",mode='eval').body
        return node
    def visit_Constant(self,node):
        if node.value=='native_channel_null_result.json':
            counts['name']+=1
            return ast.Constant('native_channel_failure_result.json')
        return node
tree=Probe().visit(tree)
assert counts=={'batch':1,'readout':1,'gate':1,'record':1,'status':1,'name':1},counts
ast.fix_missing_locations(tree)
exec(compile(tree,str(STAGE/'channel_template.py'),'exec'),globals())
