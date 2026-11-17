"""Observe actual mask targets/assignments in the unchanged paired protocol."""
import ast
from native_runtime import STAGE

generator = ast.parse((STAGE / 'pair_template.py').read_text())
assert isinstance(generator.body[-1], ast.Expr)
assert ast.unparse(generator.body[-1].value).startswith('exec(compile(tree,')
generator.body.pop()
namespace = {}
exec(compile(generator, str(STAGE / 'pair_template.py'), 'exec'), namespace)
tree = namespace['tree']
changes = {name: 0 for name in ('observe', 'native', 'suffix', 'baseline',
                               'identity', 'condition', 'check', 'name')}


def statements(source):
    return ast.parse(source).body


class Match(ast.NodeTransformer):
    def visit_Assign(self, node):
        self.generic_visit(node)
        if len(node.targets) != 1:
            return node
        target = ast.unparse(node.targets[0])
        if target == 'flags':
            changes['observe'] += 1
            extra = """match_trace=[]
original_loss_masks=model.criterion.loss_masks
def observed_loss_masks(pred_masks,pred_scores,targets,indices,num_boxes):
    match_trace.append(fingerprint(torch,([target.get('masks') for target in targets],indices,num_boxes)))
    return original_loss_masks(pred_masks,pred_scores,targets,indices,num_boxes)
model.criterion.loss_masks=observed_loss_masks
"""
            return [node, *statements(extra)]
        if target == '(loss, components)':
            changes['suffix'] += 1
            return [node, *statements("held['last_match_signature']=list(match_trace)\nmatch_trace.clear()")]
        if target == '(normal, base_loss, base_components)':
            changes['baseline'] += 1
            return [node, *statements("r['baseline_match_signature']=held['last_match_signature']\nassert r['baseline_match_signature']==r['native_match_signature'],'Native/baseline mask matching differs'")]
        if target == '(identity, identity_loss, _)':
            changes['identity'] += 1
            return [node, *statements("r['identity_matching_identical']=held['last_match_signature']==r['baseline_match_signature']\nassert r['identity_matching_identical'],'Identity mask matching differs'")]
        if target == 'condition':
            changes['condition'] += 1
            return [node, *statements("condition['mask_matching_identical']=held['last_match_signature']==r['baseline_match_signature']\ncondition['mask_match_signature']=held['last_match_signature']")]
        if target == "record['conditions'][label + '__' + field_mode]":
            changes['check'] += 1
            return [node, *statements("assert condition['mask_matching_identical'],'Changed-condition mask matching differs'")]
        return node

    def visit_AugAssign(self, node):
        self.generic_visit(node)
        if ast.unparse(node.target) == "r['native_forwards']":
            changes['native'] += 1
            return [node, *statements("r['native_match_signature']=list(match_trace)\nmatch_trace.clear()")]
        return node

    def visit_Constant(self, node):
        if node.value == 'native_paired_field_result.json':
            changes['name'] += 1
            return ast.Constant('native_matched_pair_result.json')
        return node


tree = Match().visit(tree)
assert changes == {name: 1 for name in changes}, changes
ast.fix_missing_locations(tree)
exec(compile(tree, str(STAGE / 'task_template.py'), 'exec'), globals())
