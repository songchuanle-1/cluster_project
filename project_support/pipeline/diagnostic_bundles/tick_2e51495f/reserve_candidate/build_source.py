"""Prepare one isolated NSD source; never touch the Cluster worktree or index."""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import os
import subprocess

ROOT = Path("D:/project/cluster_project")
MAIN = ROOT / "Cluster"
HERE = Path(__file__).resolve().parent
PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"
PSC = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
OLD = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_psc"
NEW = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort_nsd"
TARGET = HERE / "source"
assert not TARGET.exists()
assert subprocess.check_output(["git", "-C", str(MAIN), "rev-parse", "HEAD"], text=True).strip() == PARENT
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == "2e51495f07244023946fc53eec6e6d98"
assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])


def show(relative):
    return subprocess.check_output(["git", "-C", str(MAIN), "show", PSC + ":" + relative])


model_prefix = "framework/model/Quard_model/"
old_prefix = model_prefix + OLD + "/"
new_prefix = model_prefix + NEW + "/"
sources = {}
for name in ("__init__.py", "backbone.py", "dec.py", "hier_postprocess.py",
             "loss.py", "network.py", "sample_model.py"):
    raw = show(old_prefix + name)
    if name == "hier_postprocess.py":
        text = raw.decode("utf8")
        text = text.replace(
            "from .position_scatter import HierarchicalPositionFeatureScatter",
            "from .spatial_dirichlet import HierarchicalSpatialDirichlet")
        text = text.replace("HierarchicalPositionFeatureScatter", "HierarchicalSpatialDirichlet")
        text = text.replace("position_feature_scatter", "spatial_dirichlet")
        text = text.replace("'PSC requires the original three hierarchy scales'",
                            "'NSD requires the original three hierarchy scales'")
        raw = text.encode("utf8")
    sources[new_prefix + name] = raw
sources[new_prefix + "spatial_dirichlet.py"] = (HERE / "spatial_dirichlet_core.py").read_bytes()
old_yaml = "configs/Quard/ctf_hcg_csort_psc/" + OLD + ".yaml"
new_yaml = "configs/Quard/ctf_hcg_csort_nsd/" + NEW + ".yaml"
sources[new_yaml] = show(old_yaml)
for relative, raw in sources.items():
    path = TARGET / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("xb") as stream:
        stream.write(raw)
    if path.suffix == ".py":
        compile(raw, str(path), "exec")
result = {
    "recorded_at": datetime.now(timezone.utc).isoformat(),
    "candidate_id": "hierarchy-native-spatial-dirichlet-composition",
    "proposed_experiment_id": "M232-NSD",
    "source_parent_commit": PARENT,
    "source_template_commit": PSC,
    "source_files_exact9": {path: hashlib.sha256(raw).hexdigest() for path, raw in sources.items()},
    "source_file_count": len(sources), "model_file_count": 8,
    "config": new_yaml, "model_folder": new_prefix.rstrip("/"),
    "isolation": "Only source under this diagnostic bundle; no main/index/commit/queue/remote change.",
    "native": "NOT_RUN", "resources": "NOT_RUN", "Torch_autograd": "NOT_RUN",
}
with (HERE / "source_preparation.json").open("x", encoding="utf8") as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
    stream.write("\n")
print(json.dumps(result, ensure_ascii=False))
