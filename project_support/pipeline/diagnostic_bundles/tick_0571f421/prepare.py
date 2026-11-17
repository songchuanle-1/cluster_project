"""Static isolation checks and frozen resource/asset manifest, no GPU allocation."""
import ast
from datetime import datetime, timezone
import json
from pathlib import Path
import yaml
from ops import CODE, ROOT, OUT, NAME, PARENT, STAGE, REMOTE_ROOT, CID, guard, save, evidence, remote, tick

owner = guard()
package = CODE / "framework/model/Quard_model" / NAME
parent = package.with_name(PARENT)
config = CODE / "configs/Quard/ctf_hcg_csort_fle_r1" / (NAME + ".yaml")
parent_config = CODE / "configs/Quard/ctf_hcg_csort" / (PARENT + ".yaml")
a = yaml.safe_load(config.read_text(encoding="utf-8"))
b = yaml.safe_load(parent_config.read_text(encoding="utf-8"))
assert a["model"]["dec"].pop("cluster_mode") == "fle_csort"
assert b["model"]["dec"].pop("cluster_mode") == "ctf_hcg_csort"
assert a == b, "Nonstructural config change"
files = sorted(package.glob("*.py"))
assert len(files) == 8 and len(list(CODE.glob("configs/**/" + NAME + ".yaml"))) == 1
for path in files:
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module:
            assert not ("Quard_model.model_" in node.module or node.module.startswith("model_base"))
same = ["__init__.py", "network.py", "backbone.py", "loss.py", "sample_model.py"]
assert all(tick.digest(package / name) == tick.digest(parent / name) for name in same)
source_hashes = {path.name: tick.digest(path) for path in files}
save("static_independence.json", {"observed_at": datetime.now(timezone.utc).isoformat(), "passed": True,
    "physical_python_files": len(files), "unique_basename": True, "cross_variant_imports": False,
    "only_config_change": "model.dec.cluster_mode", "unchanged_parent_files": same,
    "source_hashes": source_hashes, "config_sha256": tick.digest(config), "training_started": False})
program = r'''
import datetime,fcntl,hashlib,json,pathlib,socket,subprocess
assert socket.gethostname()=="dl04-MS-7E06"
root=pathlib.Path("/data/songcl/Project/Cluster_project/Cluster_m201_bps_f8457d3b")
row=subprocess.check_output(["nvidia-smi","-i","0","--query-gpu=index,uuid,memory.used,memory.free,utilization.gpu","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
assert [c.strip() for c in row.split(",")][:2]==["0","GPU-958e741a-e5cf-127e-ffe8-9b984e1f404c"]
contexts=subprocess.check_output(["nvidia-smi","-i","0","--query-compute-apps=pid,used_memory","--format=csv,noheader,nounits"],universal_newlines=True,timeout=10).strip()
locks={}
for kind in ("training","diagnostic","exclusive"):
    with open("/tmp/cluster_project_gpu0_"+kind+".lock","rb") as handle:
        try:fcntl.flock(handle,fcntl.LOCK_EX|fcntl.LOCK_NB)
        except BlockingIOError:locks[kind]="held"
        else:locks[kind]="acquired_and_released"
paths=sorted(root.parent.glob("pipeline/*/frozen_m95.pth"))
assert paths,"No frozen M95 diagnostic asset"
checkpoint=None
for path in paths:
    h=hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda:f.read(8*1024*1024),b""):h.update(chunk)
    if h.hexdigest()=="fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e":checkpoint=str(path);break
assert checkpoint,"Trusted M95 snapshot unavailable"
parent="model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
sources={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in (root/"framework/model/Quard_model"/parent).glob("*.py")}
annotation=pathlib.Path("/home/songcl/data/data/scanrefer/ScanRefer_train_new.json")
print(json.dumps({"observed_at":datetime.datetime.now(datetime.timezone.utc).isoformat(),"hostname":socket.gethostname(),"gpu":row,"contexts":contexts,"locks":locks,"checkpoint":checkpoint,"checkpoint_sha256":"fe5e4a5fbd878175e2789a2fa0481e962ea3f83ba0a6515301aa4cf57197127e","parent_source_hashes":sources,"annotation_sha256":hashlib.sha256(annotation.read_bytes()).hexdigest(),"dataset_source_sha256":hashlib.sha256((root/"framework/dataset/scannetv2.py").read_bytes()).hexdigest(),"cuda_initialized":False}))
'''
probe = remote(program, 120)
save("asset_resource_precheck.json", probe)
assert not probe["contexts"] and all(v == "acquired_and_released" for v in probe["locks"].values())
assert probe["parent_source_hashes"] == {p.name: tick.digest(p) for p in parent.glob("*.py")}
prior = tick.load(ROOT / "pipeline/diagnostic_bundles/tick_99e0a813/fine_audit_manifest.json")
manifest = {"token": owner["token"], "deadline_at": owner["deadline_at"], "root": REMOTE_ROOT,
    "stage": STAGE, "name": NAME, "parent": PARENT, "source_hashes": source_hashes,
    "config_sha256": tick.digest(config), "checkpoint": probe["checkpoint"],
    "checkpoint_sha256": probe["checkpoint_sha256"], "parent_source_hashes": probe["parent_source_hashes"],
    "hds_source_hashes": prior["source_hashes"], "annotation_sha256": probe["annotation_sha256"],
    "dataset_source_sha256": probe["dataset_source_sha256"], "train_groups": [0,60,101,124],
    "native_pairs": [[0,60],[101,124]], "tolerance": 1e-6, "optimizer_steps": 0}
save("manifest.json", manifest)
work = tick.load(ROOT / "pipeline/research_work.json")
candidate = next(c for c in work["candidates"] if c["id"] == CID)
candidate.update(stage="validation", next_action="Execute preregistered independent FLE CPU contracts and full native matched controls/backward on two TRAIN batch2 pairs; then full same-protocol baseline/champion/candidate resources. No admission yet.")
candidate["evidence"].extend(evidence(OUT / n) for n in ("integration_prereg.md","static_independence.json","asset_resource_precheck.json","manifest.json"))
candidate["evidence"].extend(evidence(p) for p in files)
candidate["evidence"].append(evidence(config))
guard(); tick.save(ROOT / "pipeline/research_work.json", work)
print(json.dumps({"static_pass": True, "gpu": probe["gpu"], "locks": probe["locks"], "checkpoint": probe["checkpoint"], "native_groups": manifest["train_groups"], "admissions": 0}))
