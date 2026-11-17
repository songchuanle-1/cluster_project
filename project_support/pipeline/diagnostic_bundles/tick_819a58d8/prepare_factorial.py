"""Mechanical AST expansion of two coupled scopes to a preregistered 2x2."""
import ast
from ops import guard, save, evidence, tick, OUT

guard(600)
source = OUT / 'native_paired_field.py'
tree = ast.parse(source.read_text(encoding='utf-8'))
changes = {'prefix': 0, 'scope_tuple': 0, 'description': 0}
scopes = ('sender_one__receiver_one', 'sender_all__receiver_one',
          'sender_one__receiver_all', 'sender_all__receiver_all')


class Scope(ast.NodeTransformer):
    def visit_Assign(self, node):
        self.generic_visit(node)
        if len(node.targets) == 1 and ast.unparse(node.targets[0]) == 'prefix':
            assert isinstance(node.value, ast.Attribute) and node.value.attr == 'body'
            text = node.value.value.args[0]
            inner = ast.parse(text.value)
            assert len(inner.body) == 2
            assert [ast.unparse(v.targets[0]) for v in inner.body] == ['receiver_ids', 'sender_ids']
            for assignment, predicate in zip(inner.body, (
                    "field_mode.endswith('receiver_one')",
                    "field_mode.startswith('sender_one')")):
                assert isinstance(assignment.value, ast.IfExp)
                assignment.value.test = ast.parse(predicate, mode='eval').body
            text.value = ast.unparse(inner)
            changes['prefix'] += 1
        return node

    def visit_Call(self, node):
        self.generic_visit(node)
        if isinstance(node.func, ast.Name) and node.func.id == 'expression' and node.args:
            value = node.args[0]
            if isinstance(value, ast.Constant) and value.value == "('single_point','coherent_field')":
                value.value = repr(scopes)
                changes['scope_tuple'] += 1
        return node

    def visit_Constant(self, node):
        if node.value == 'Paired single/coherent conditional channel scopes on ONE native prefix,not efficacy/admission':
            changes['description'] += 1
            return ast.Constant('Factorial sender/receiver conditional scopes on ONE native prefix with actual matching observed;not efficacy/admission')
        return node


tree = Scope().visit(tree)
assert changes == {name: 1 for name in changes}, changes
ast.fix_missing_locations(tree)
destination = OUT / 'factorial_pair_template.py'
with destination.open('x', encoding='utf-8') as stream:
    stream.write(ast.unparse(tree) + '\n')
save('factorial_codegen.json', {'source': evidence(source), 'result': evidence(destination),
     'preregistration': evidence(OUT / 'factorial_scope_prereg.md'),
     'changes': changes, 'scopes': scopes, 'model_or_threshold_changed': False})
print({'generated': True, 'sha256': tick.digest(destination)})
