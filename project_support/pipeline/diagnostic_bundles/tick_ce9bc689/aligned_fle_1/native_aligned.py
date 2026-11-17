"""Extend observational raw capture only; preserve original computation."""
import ast
from native_runtime import STAGE

tree=ast.parse((STAGE/'trace_template.py').read_text())
changed={'record':0,'mode':0}
class Instrument(ast.NodeTransformer):
    def visit_FunctionDef(self,node):
        self.generic_visit(node)
        if node.name=='record':
            node.body.insert(0,ast.parse("save_raw = save_raw or label.startswith(('unet.conv.2','unet.u.blocks.block0'))").body[0])
            changed['record']+=1
        return node
    def visit_Expr(self,node):
        self.generic_visit(node)
        if isinstance(node.value,ast.Call) and isinstance(node.value.func,ast.Attribute):
            f=node.value.func
            if isinstance(f.value,ast.Name) and f.value.id=='model' and f.attr=='train':
                changed['mode']+=1
                return [node,*ast.parse("r['norm_eval'] = model.norm_eval\nr['first_block_norm_training'] = model.unet.u.blocks[0].conv_branch[0].training").body]
        return node
tree=Instrument().visit(tree)
assert changed=={'record':1,'mode':1}
ast.fix_missing_locations(tree)
exec(compile(tree,str(STAGE/'trace_template.py'),'exec'),globals())
