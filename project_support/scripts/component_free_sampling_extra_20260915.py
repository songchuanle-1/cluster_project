"""Run the next two sequential TRAIN batches; no favorable-batch selection."""
import ast
from pathlib import Path

base = Path("/tmp/component_full_loss_20260915.py")
text = base.read_text()
assert "if len(batches) == 2:" in text
expanded = Path("/tmp/component_full_loss_extra_20260915.py")
expanded.write_text(text.replace("if len(batches) == 2:", "if len(batches) == 4:"))
parameter = Path("/tmp/component_parameter_step_20260915.py").read_text()
assert 'enumerate(env["batches"])' in parameter
parameter = parameter.replace('Path("/tmp/component_full_loss_20260915.py")',
                              'Path("/tmp/component_full_loss_extra_20260915.py")')
parameter = parameter.replace('enumerate(env["batches"])', 'enumerate(env["batches"][2:4])')
Path("/tmp/component_parameter_extra_20260915.py").write_text(parameter)
worker = Path("/tmp/component_free_sampling_server4_20260915.py").read_text()
worker = worker.replace("/tmp/component_parameter_step_20260915.py",
                        "/tmp/component_parameter_extra_20260915.py")
worker = worker.replace("/tmp/component_free_sampling_server4_20260915",
                        "/tmp/component_free_sampling_extra_20260915")
exec(compile(ast.parse(worker), __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
