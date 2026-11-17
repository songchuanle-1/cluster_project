"""Structured instrumentation of the frozen task-suffix diagnostic only."""
import ast
from native_runtime import STAGE

tree = ast.parse((STAGE / 'task_template.py').read_text())
counts = {name: 0 for name in ('receivers', 'record', 'senders', 'isolation',
                              'delta', 'surrogate', 'name', 'scope')}


def expression(source):
    return ast.parse(source, mode='eval').body


class Coherent(ast.NodeTransformer):
    def visit_For(self, node):
        self.generic_visit(node)
        if isinstance(node.target, ast.Name) and node.target.id == 'index':
            counts['receivers'] += 1
            node.body[:0] = ast.parse('receivers=(coarse==coarse[index]).nonzero().flatten()\nsenders=(coarse!=coarse[index]).nonzero().flatten()').body
        return node

    def visit_Assign(self, node):
        self.generic_visit(node)
        if len(node.targets) != 1:
            return node
        target = ast.unparse(node.targets[0])
        if target == 'record':
            counts['record'] += 1
            assert isinstance(node.value, ast.Dict)
            for key, value in [('coarse_cluster', 'int(coarse[index].cpu())'),
                               ('receiver_count', 'int(receivers.numel())'),
                               ('sender_count', 'int(senders.numel())'),
                               ('padded_points', 'int(x.shape[1])')]:
                node.value.keys.append(ast.Constant(key))
                node.value.values.append(expression(value))
        elif target == 'px[b, remote]':
            counts['senders'] += 1
            return ast.parse('px[b, senders] = px[b, senders] + direction.to(px)').body[0]
        elif target == 'isolated[b, index]':
            counts['isolation'] += 1
            return ast.parse('isolated[b, receivers] = message[b, receivers]').body[0]
        elif target == 'delta':
            counts['delta'] += 1
            node.value = expression('(isolated[b, receivers]-base[b, receivers]).detach()')
        return node

    def visit_Dict(self, node):
        self.generic_visit(node)
        for index, key in enumerate(node.keys):
            if isinstance(key, ast.Constant) and key.value == 'native_cotangent_linear_surrogate':
                counts['surrogate'] += 1
                node.values[index] = expression('float((native_gradient[b,receivers].double()*delta.double()).sum().cpu())')
        return node

    def visit_Constant(self, node):
        if node.value == 'native_task_suffix_result.json':
            counts['name'] += 1
            return ast.Constant('native_coherent_channel_result.json')
        if node.value == 'Conditional message diagnostic, not efficacy or admission':
            counts['scope'] += 1
            return ast.Constant('Coherent outside-coarse conditional channel diagnostic, not efficacy or admission')
        return node


tree = Coherent().visit(tree)
assert counts == {name: 1 for name in counts}, counts
ast.fix_missing_locations(tree)
exec(compile(tree, str(STAGE / 'task_template.py'), 'exec'), globals())
