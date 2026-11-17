"""Add only a native cotangent hook and conditional isolated BN control."""
import ast
import bn_probe
from native_runtime import STAGE

tree=ast.parse((STAGE/'trace_template.py').read_text())
counts={'attach':0,'measure':0}
class Probe(ast.NodeTransformer):
    def visit_Expr(self,node):
        self.generic_visit(node)
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute):
            f=node.value.func
            if isinstance(f.value,ast.Name) and f.value.id=='model' and f.attr=='train':
                counts['attach']+=1
                return [node,*ast.parse('bn_probe.attach(torch,model)').body]
        return node
    def visit_AugAssign(self,node):
        self.generic_visit(node)
        if isinstance(node.target,ast.Subscript) and isinstance(node.target.slice,ast.Constant) and node.target.slice.value=='native_backwards':
            counts['measure']+=1
            return [node,*ast.parse("probe_result=bn_probe.measure(torch,model)\nr.update({k:probe_result[k] for k in ('operator_forwards','operator_vjps','zero_vjps')})").body]
        return node
tree=Probe().visit(tree)
assert counts=={'attach':1,'measure':1}
ast.fix_missing_locations(tree)
exec(compile(tree,str(STAGE/'trace_template.py'),'exec'),globals())
