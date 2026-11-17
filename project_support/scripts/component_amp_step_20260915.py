"""AMP robustness extension of the fixed shared-forward parameter diagnostic."""
import ast
from pathlib import Path

import torch


SOURCE = Path("/tmp/component_parameter_step_20260915.py")


class ExactShiftControl(ast.NodeTransformer):
    def visit_Assign(self, node):
        node = self.generic_visit(node)
        if any(isinstance(t, ast.Name) and t.id == "shifted" for t in node.targets):
            node.value = ast.Call(
                func=ast.Attribute(value=node.value, attr="float", ctx=ast.Load()),
                args=[], keywords=[])
        return node


setup = Path("/tmp/component_full_loss_20260915.py")
setup_tree = ast.fix_missing_locations(ExactShiftControl().visit(ast.parse(setup.read_text())))
Path("/tmp/component_amp_setup_20260915.py").write_text(ast.unparse(setup_tree))


class AmpDiagnostic(ast.NodeTransformer):
    def visit_Assign(self, node):
        node = self.generic_visit(node)
        if any(isinstance(t, ast.Name) and t.id == "source" for t in node.targets):
            node.value = ast.parse(
                'Path("/tmp/component_amp_setup_20260915.py")', mode="eval").body
        if any(isinstance(t, ast.Name) and t.id == "out" for t in node.targets):
            node.value = ast.parse(
                'Path("/tmp/component_amp_step_20260915-1915_retry")', mode="eval"
            ).body
        if (isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "model"):
            return ast.With(items=[ast.withitem(context_expr=ast.parse(
                'torch.autocast(device_type="cuda", dtype=torch.float16)',
                mode="eval").body)], body=[node])
        if any(isinstance(t, ast.Name) and t.id == "optimizer" for t in node.targets):
            return [node, *ast.parse(
                'scaler = torch.amp.GradScaler("cuda")\n'
                'scaler.scale(torch.ones((), device="cuda"))\n'
                'scale_before = scaler.get_scale()\n').body]
        if any(isinstance(t, ast.Name) and t.id == "norm" for t in node.targets):
            return [*ast.parse('scaler.unscale_(optimizer)').body, node]
        return node

    def visit_Expr(self, node):
        node = self.generic_visit(node)
        call = node.value
        if not isinstance(call, ast.Call):
            return node
        if isinstance(call.func, ast.Attribute) and call.func.attr == "backward":
            call.func.value = ast.parse(
                'torch.amp.GradScaler("cuda").scale(loss)', mode="eval"
            ).body
        if (isinstance(call.func, ast.Attribute) and call.func.attr == "step"
                and isinstance(call.func.value, ast.Name)
                and call.func.value.id == "optimizer"):
            return ast.parse(
                'scaler.step(optimizer)\n'
                'scaler.update()\n'
                'assert scaler.get_scale() >= scale_before, "AMP update skipped"\n'
            ).body
        if isinstance(call.func, ast.Name) and call.func.id == "model":
            return ast.With(items=[ast.withitem(context_expr=ast.parse(
                'torch.autocast(device_type="cuda", dtype=torch.float16)',
                mode="eval").body)], body=[node])
        return node

    def visit_Constant(self, node):
        if isinstance(node.value, str) and node.value.startswith("FP32 two fixed"):
            node.value = (
                "AMP float16 robustness on two fixed TRAIN batches, fresh AdamW "
                "with default GradScaler scaling/unscale/step/update and native "
                "groups/clipping. Production tools/train.py uses FP32, not AMP. "
                "Same-batch diagnostics only; not efficacy, novelty or admission."
            )
        return node


tree = ast.fix_missing_locations(AmpDiagnostic().visit(ast.parse(SOURCE.read_text())))
compiled = ast.unparse(tree)
Path("/tmp/component_amp_step_20260915-1915_expanded.py").write_text(compiled)
exec(compile(tree, str(SOURCE), "exec"), globals())
