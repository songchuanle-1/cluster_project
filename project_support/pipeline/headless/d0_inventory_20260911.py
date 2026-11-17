"""CPU-only diagnostic asset inventory and prediction-blind scene split."""
from collections import Counter, defaultdict
from datetime import datetime
import hashlib
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path("D:/project/cluster_project")
OUT = ROOT / "pipeline/reports/d0_inventory_20260911-0316"
REMOTE = "/data/songcl/Project/Cluster_project/Cluster_checkpoints"
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
SSH = ["ssh", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10", "songcl@192.168.1.137"]


def run(args):
    return subprocess.run(args, check=True, capture_output=True, text=True,
                          encoding="utf-8", timeout=90).stdout


def main():
    OUT.mkdir(exist_ok=True)
    source = "/home/songcl/data/data/scanrefer/ScanRefer_val_new.json"
    local = OUT / "ScanRefer_val_new.json"
    if not local.exists():
        run(["scp", "-o", "BatchMode=yes", "-o", "ConnectTimeout=10",
             f"songcl@192.168.1.137:{source}", str(local)])
    digest = hashlib.sha256(local.read_bytes()).hexdigest()
    assert run(SSH + [f"sha256sum {shlex.quote(source)}"]).split()[0] == digest
    data = json.loads(local.read_text(encoding="utf-8"))
    keys = [(r["scene_id"], str(r["object_id"]), str(r["ann_id"])) for r in data]
    assert len(keys) == len(set(keys))
    grouped = defaultdict(list)
    for r in data:
        grouped[r["scene_id"]].append(r)
    def order(value):
        return hashlib.sha256(("cluster-d0-v1|" + value).encode()).hexdigest()
    scenes = sorted(grouped, key=order)
    physical_scenes = sorted({s.rsplit("_", 1)[0] for s in scenes}, key=order)
    diagnostic_groups = set(physical_scenes[::2])
    diagnostic = {s for s in scenes if s.rsplit("_", 1)[0] in diagnostic_groups}
    samples = []
    for scene in sorted(grouped):
        records = sorted(grouped[scene],
                         key=lambda r: order("|".join((scene, str(r["object_id"]), str(r["ann_id"])))))
        chosen = records[:4] if scene in diagnostic else records
        for r in chosen:
            samples.append(dict(scene_id=scene, object_id=str(r["object_id"]),
                                ann_id=str(r["ann_id"]), object_name=r["object_name"],
                                physical_scene=scene.rsplit("_", 1)[0],
                                subset="diagnostic" if scene in diagnostic else "reserved_evaluation"))
    manifest = dict(created_at=datetime.now().isoformat(), source=source, source_sha256=digest,
                    population_records=len(data), population_scenes=len(scenes),
                    diagnostic_scenes=len(diagnostic), reserved_scenes=len(scenes)-len(diagnostic),
                    physical_scene_count=len(physical_scenes),
                    diagnostic_physical_scenes=len(diagnostic_groups),
                    rule="v2: Sort physical scene prefixes by SHA256(cluster-d0-v1|prefix); "
                         "even positions diagnostic, all scans of each prefix stay together. "
                         "Take first4 hash-ordered descriptions per diagnostic scene; reserve all "
                         "descriptions in remaining scenes. No prediction/metric selection.",
                    limitation="Reserved evaluation is prospective only; this validation set was "
                               "previously used for training selection, not an untouched test set. "
                               "Equal scene sampling is not population-weighted prevalence.",
                    sample_counts=dict(Counter(s["subset"] for s in samples)), samples=samples)
    destination = OUT / "sample_manifest_v2.json"
    if destination.exists():
        existing = json.loads(destination.read_text())
        assert existing["samples"] == samples and existing["source_sha256"] == digest
    else:
        destination.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    evidence = {}
    for name, folder in (("champion", BASE + "/20260815_101011"),
                         ("baseline_candidate", "model_base1/20260627_174353")):
        path = REMOTE + "/" + folder
        evidence[name] = run(SSH + [f"find {shlex.quote(path)} -maxdepth 4 -type f -printf '%p %s\\n'"])
    evidence["scene_files"] = run(SSH + [
        "find /home/songcl/data/data/scannetv2/val -maxdepth 1 -name '*_refer.pth' -printf '%f\\n'"])
    present = set(line.removesuffix("_refer.pth") for line in evidence["scene_files"].splitlines())
    evidence["missing_scenes"] = sorted(set(scenes) - present)
    evidence["source_sha256"] = digest
    evidence["manifest_sha256"] = hashlib.sha256(destination.read_bytes()).hexdigest()
    evidence["selected_mask_exports_found"] = False
    evidence["checkpoint_identity_verified"] = False
    evidence["candidate_bank_export_available"] = False
    evidence["missing_prerequisites"] = [
        "Verify checkpoint metadata and historical config/model identity; baseline folder contains model_base2.yaml.",
        "Checkpoint existence and size are verified, not tensor integrity or matched inference.",
        "M95 predict_by_feat selects one candidate and discards full bank from returned predictions.",
        "Need an isolated evaluation-only collector of candidate logits, selected index, superpoints and GT.",
        "No GPU inference, error labels, oracle measurement or novelty verification performed by this inventory."
    ]
    (OUT / "inventory.json").write_text(json.dumps(evidence, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in manifest.items() if k != "samples"}, indent=2))
    print("Missing scene files:", evidence["missing_scenes"])
    print("Manifest SHA256:", evidence["manifest_sha256"])


if __name__ == "__main__":
    main()
