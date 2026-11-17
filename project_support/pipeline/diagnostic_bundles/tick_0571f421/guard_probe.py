"""Exercise the actual train.py import branch without CUDA allocation."""
import fcntl
import importlib
import importlib.util
import json
from pathlib import Path
import sys
from runtime import STAGE,ROOT,NAME,MANIFEST,sha,save,observe

source=json.loads((STAGE/"final_source.json").read_text())
for name,expected in source["source_hashes"].items():assert sha(STAGE/NAME/name)==expected
assert sha(STAGE/(NAME+".yaml"))==source["config_sha256"]
sys.path[:0]=[str(ROOT),str(ROOT/"framework/lib")]
from tools import train
import torch
assert not torch.cuda.is_initialized()
importlib.import_module("framework.model.Quard_model")
qualified="framework.model.Quard_model."+NAME
sys.argv=[str(ROOT/"tools/train.py"),str(STAGE/(NAME+".yaml")),"--gpu_ids","0","--num_gpus","1"]
spec=importlib.util.spec_from_file_location(qualified,STAGE/NAME/"__init__.py",submodule_search_locations=[str(STAGE/NAME)])
module=importlib.util.module_from_spec(spec);sys.modules[qualified]=module;spec.loader.exec_module(module)
guard=importlib.import_module(qualified+".startup_guard")
assert len(guard._handles)==3 and not torch.cuda.is_initialized()
assert __import__("os").environ["CUDA_VISIBLE_DEVICES"]==guard.UUID
held={}
try:
    for kind in ("training","diagnostic","exclusive"):
        with open("/tmp/cluster_project_gpu0_"+kind+".lock","rb") as handle:
            try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:held[kind]="exclusive_ownership_enforced"
            else:raise AssertionError("Guard did not retain lock")
finally:guard.release()
released={}
for kind in ("training","diagnostic","exclusive"):
    with open("/tmp/cluster_project_gpu0_"+kind+".lock","rb") as handle:
        fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB);released[kind]="acquired_and_released"
save("guard_probe_result.json",{"passed":True,"actual_train_py_import_branch":True,"held":held,"released":released,
    "cuda_initialized":torch.cuda.is_initialized(),"native_forward_or_backward":0,"source_hashes":source["source_hashes"],"after":observe()})
print("ACTUAL_TRAIN_IMPORT_GUARD_PASS")
