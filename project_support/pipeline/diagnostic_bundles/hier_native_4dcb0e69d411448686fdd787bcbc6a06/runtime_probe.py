"""Read-only runtime/API evidence, with CUDA explicitly hidden."""
from datetime import datetime,timezone
import json
import os
import subprocess
os.environ.update(CUDA_VISIBLE_DEVICES='',PYTHONDONTWRITEBYTECODE='1')
assert subprocess.check_output(['hostname'],text=True,timeout=5).strip()=='sysu311-MS-7C59'
import torch
assert not torch.cuda.is_initialized()
print('HIER_NATIVE_RESULT='+json.dumps({'observed_at':datetime.now(timezone.utc).isoformat(),
    'torch':torch.__version__,'functional_sdpa_available':hasattr(torch.nn.functional,'scaled_dot_product_attention'),
    'cuda_initialized':False,'scope':'API capability only; not a scientific rejection or gate promotion.'}))
