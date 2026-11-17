"""Exception-only operand capture; original radius function remains unchanged."""
from datetime import datetime, timezone
import json
from pathlib import Path
import runpy
import numpy as np
import neighbor_content

root = Path(__file__).resolve().parent
original = neighbor_content.matched_radius
calls = 0

def capture(donor, recipient):
    global calls
    calls += 1
    try:
        return original(donor, recipient)
    except BaseException as error:
        destination = root / 'failed_norm_operands.npz'
        assert not destination.exists()
        np.savez_compressed(destination, donor=donor.detach().cpu().numpy(),
                            recipient=recipient.detach().cpu().numpy())
        with (root / 'failed_norm_context.json').open('x') as stream:
            json.dump({'observed_at': datetime.now(timezone.utc).isoformat(),
                       'call_index': calls, 'shape': list(donor.shape), 'dtype': str(donor.dtype),
                       'device': str(donor.device), 'error_type': type(error).__name__, 'error': str(error),
                       'arithmetic_unchanged': True, 'exception_reraised': True}, stream, indent=2)
        raise

neighbor_content.matched_radius = capture
try:
    runpy.run_path(str(root / 'native_diagnostic.py'), run_name='__main__')
finally:
    neighbor_content.matched_radius = original
