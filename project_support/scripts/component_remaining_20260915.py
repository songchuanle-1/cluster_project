"""Complete predefined 16-batch diagnostic coverage without selecting outcomes."""
from pathlib import Path
import os

storage = Path(os.environ.get("COMPONENT_STORAGE", "/tmp"))
storage.mkdir(parents=True, exist_ok=True)

text = Path("/tmp/component_full_loss_20260915.py").read_text()
assert "if len(batches) == 2:" in text
(storage / "component_full_loss_remaining_20260915.py").write_text(
    text.replace("if len(batches) == 2:", "if len(batches) == 16:"))
parameter = Path("/tmp/component_parameter_step_20260915.py").read_text()
parameter = parameter.replace('Path("/tmp/component_full_loss_20260915.py")',
                              f'Path("{storage}/component_full_loss_remaining_20260915.py")')
parameter = parameter.replace('enumerate(env["batches"])', 'enumerate(env["batches"][4:16])')
(storage / "component_parameter_remaining_20260915.py").write_text(parameter)
worker = Path("/tmp/component_free_sampling_server4_20260915.py").read_text()
worker = worker.replace("/tmp/component_parameter_step_20260915.py",
                        str(storage / "component_parameter_remaining_20260915.py"))
worker = worker.replace("/tmp/component_free_sampling_server4_20260915",
                        str(storage / "component_remaining_20260915"))
worker = worker.replace("for batch_id in (0, 1):", "for batch_id in range(12):")
exec(compile(worker, __file__, "exec"), {"__name__": "__main__", "__file__": __file__})
