"""Static consistency and provenance checks; no remote/owner execution."""
import ast
import hashlib
import json
from pathlib import Path
import sys
import adapter

OUT=Path(__file__).resolve().parent
source=adapter.Adapter(origin=OUT)
release=source._release_details()
prep,template=source._frozen_details()
for path in OUT.rglob('*.py'):
    ast.parse(path.read_bytes(),filename=str(path));compile(path.read_bytes(),str(path),'exec')
for name in ['execution_binding.json','native_manifest.json','execution_lease.json','stage_request.json']:
    assert not list(OUT.rglob(name)),name
assert release['formatter_implemented'] is False and release['admission_implemented'] is False
assert release['native_execution']=='NOT_RUN' and release['remote_execution']=='NOT_RUN'
assert 'torch' not in sys.modules
print(json.dumps({'status':'STATIC_CONSISTENCY_PASS_NOT_NATIVE_ADMISSION',
    'adapter_sha256':release['source_hashes']['adapter.py'],
    'remote_ops_sha256':release['source_hashes']['remote_ops.py'],
    'frozen_preparation_unchanged':True,'production_active_bindings_created':False,
    'ssh_executed':False,'native_executed':False,'formatter_implemented':False,
    'external_review_anchor_still_required':True},sort_keys=True))
