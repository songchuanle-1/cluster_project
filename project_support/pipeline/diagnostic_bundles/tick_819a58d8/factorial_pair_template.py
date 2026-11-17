"""Both fixed sender/receiver scopes within ONE native captured prefix."""
import ast
from native_runtime import STAGE
tree = ast.parse((STAGE / 'task_template.py').read_text())
counts = {name: 0 for name in ('loop', 'record', 'sender', 'receiver', 'delta', 'condition', 'surrogate', 'failures', 'name', 'scope')}

def expression(source):
    return ast.parse(source, mode='eval').body

class Paired(ast.NodeTransformer):

    def visit_For(self, node):
        self.generic_visit(node)
        if isinstance(node.target, ast.Tuple) and [ast.unparse(v) for v in node.target.elts] == ['label', 'direction']:
            counts['loop'] += 1
            prefix = ast.parse("receiver_ids = torch.tensor([index], device=x.device, dtype=torch.long) if field_mode.endswith('receiver_one') else (coarse == coarse[index]).nonzero().flatten()\nsender_ids = torch.tensor([remote], device=x.device, dtype=torch.long) if field_mode.startswith('sender_one') else (coarse != coarse[index]).nonzero().flatten()").body
            node.body = [ast.For(target=ast.Name(id='field_mode', ctx=ast.Store()), iter=expression("('sender_one__receiver_one', 'sender_all__receiver_one', 'sender_one__receiver_all', 'sender_all__receiver_all')"), body=[*prefix, *node.body], orelse=[])]
        return node

    def visit_Assign(self, node):
        self.generic_visit(node)
        if len(node.targets) != 1:
            return node
        target = ast.unparse(node.targets[0])
        if target == 'record':
            counts['record'] += 1
            node.value.keys.append(ast.Constant('coarse_cluster'))
            node.value.values.append(expression('int(coarse[index].cpu())'))
        elif target == 'px[b, remote]':
            counts['sender'] += 1
            return ast.parse('px[b,sender_ids]=px[b,sender_ids]+direction.to(px)').body[0]
        elif target == 'isolated[b, index]':
            counts['receiver'] += 1
            return ast.parse('isolated[b,receiver_ids]=message[b,receiver_ids]').body[0]
        elif target == 'delta':
            counts['delta'] += 1
            node.value = expression('(isolated[b,receiver_ids]-base[b,receiver_ids]).detach()')
        elif target == "record['conditions'][label]":
            counts['condition'] += 1
            node.targets[0] = expression("record['conditions'][label+'__'+field_mode]")
            node.targets[0].ctx = ast.Store()
        return node

    def visit_Dict(self, node):
        self.generic_visit(node)
        for index, key in enumerate(node.keys):
            if isinstance(key, ast.Constant) and key.value == 'native_cotangent_linear_surrogate':
                counts['surrogate'] += 1
                node.values[index] = expression('float((native_gradient[b,receiver_ids].double()*delta.double()).sum().cpu())')
                for key, value in [('field_mode', 'field_mode'), ('receiver_count', 'int(receiver_ids.numel())'), ('sender_count', 'int(sender_ids.numel())'), ('padded_points', 'int(x.shape[1])')]:
                    node.keys.append(ast.Constant(key))
                    node.values.append(expression(value))
                break
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        for keyword in node.keywords:
            if keyword.arg == 'original_null_failures':
                counts['failures'] += 1
                keyword.value = expression("sum(c.get('original_strict_1e_minus6_message_gate') is False for row in r['records'] for c in row['conditions'].values())")
        return node

    def visit_Constant(self, node):
        if node.value == 'native_task_suffix_result.json':
            counts['name'] += 1
            return ast.Constant('native_paired_field_result.json')
        if node.value == 'Conditional message diagnostic, not efficacy or admission':
            counts['scope'] += 1
            return ast.Constant('Factorial sender/receiver conditional scopes on ONE native prefix with actual matching observed;not efficacy/admission')
        return node
tree = Paired().visit(tree)
assert counts == {name: 1 for name in counts}, counts
ast.fix_missing_locations(tree)
exec(compile(tree, str(STAGE / 'task_template.py'), 'exec'), globals())
