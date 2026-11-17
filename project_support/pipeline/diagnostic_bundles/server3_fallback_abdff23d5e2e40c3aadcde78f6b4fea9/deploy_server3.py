"""Materialize one isolated exact-commit checkout, never overwrite legacy code."""
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess

assert subprocess.check_output(['hostname'],universal_newlines=True,timeout=5).strip() == 'sysu311-MS-7C59'
STAGE = Path('/sdc1/songcl/Project/Cluster_project/pipeline/server3_fallback_abdff23d')
ROOT = Path('/sdc1/songcl/Project/Cluster_project/Cluster_hier_feature_abdff23d')
COMMIT = 'f8457d3b657e66306a7fce1afb3d81d8ab874669'
MODEL = 'model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort'


def sha(path):
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for part in iter(lambda: stream.read(8*1024*1024),b''):
            h.update(part)
    return h.hexdigest()


assert STAGE.is_dir() and (STAGE/'source.bundle').is_file()
assert sha(STAGE/'frozen_m95.pth') == 'fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e'
assert not ROOT.exists(), 'Existing checkouts must never be overwritten.'
subprocess.run(['git','clone',str(STAGE/'source.bundle'),str(ROOT)],check=True,timeout=240)
actual = subprocess.check_output(['git','-C',str(ROOT),'rev-parse','HEAD'],universal_newlines=True,timeout=8).strip()
assert actual == COMMIT
config = ROOT/'configs/Quard/ctf_hcg_csort'/(MODEL+'.yaml')
hierarchy = ROOT/'framework/model/Quard_model'/MODEL/'hier_postprocess.py'
assert sha(config) == 'a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a'
assert sha(hierarchy) == '7e1488f44a1690bb8b1c61fbf79e32971ddbb6a14412747ffbec1abed495347f'
print('SERVER3_DEPLOY_JSON='+json.dumps({'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'hostname':'sysu311-MS-7C59','root':str(ROOT),'commit':actual,
    'bundle_sha256':sha(STAGE/'source.bundle'),'checkpoint_sha256':sha(STAGE/'frozen_m95.pth'),
    'config_sha256':sha(config),'hierarchy_sha256':sha(hierarchy),
    'legacy_checkout_modified':False,'gpu_allocations':0,'new_training':False}))
