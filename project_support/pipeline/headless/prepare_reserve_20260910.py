"""Snapshot all research inputs and mechanically copy three independent parents."""
import ast
import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path("D:/project/cluster_project")
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"
SUFFIXES = ("mqbc", "mqtd", "mqsd")


def main():
    goal = ROOT / "pipeline/goal.json"
    shutil.copyfile(goal, ROOT / "pipeline/reviews/goal_snapshot_20260910-1113.json")
    inventory = []
    for path in sorted((ROOT / "pipeline/analyses").glob("*.md")):
        text = path.read_text(encoding="utf-8")
        inventory.append({
            "path": str(path.relative_to(ROOT)), "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "content": text,
        })
    rows = list(csv.DictReader((ROOT / "pipeline/experiments.csv").open(encoding="utf-8-sig")))
    evidence = {"analysis_count": len(inventory), "analyses": inventory, "ledger": rows}
    (ROOT / "pipeline/reports/research_inventory_20260910-1113.json").write_text(
        json.dumps(evidence, indent=2, ensure_ascii=False), encoding="utf-8")
    lines = ["# Research Ledger Assessment", "", "Historical rows retained, not independent seed evidence.",
             "Exact paired metrics for recent parents are in review1113 and archived terminal analyses.",
             "", "| ID | State | Best mIoU | Epochs | Motivation assessment |",
             "|----|-------|-----------|--------|-----------------------|"]
    for row in rows:
        score = row.get("best_miou", "")
        try:
            value = float(score)
        except ValueError:
            value = None
        assessment = ("No usable metric; no efficacy inference" if value is None else
                      "Champion reference; seed robustness unproven" if value >= .502 else
                      "Below champion; no new superiority evidence" if value > .4894 else
                      "No observed baseline improvement")
        if row.get("state") in ("stopped_unknown", "crashed"):
            assessment += "; termination compromised"
        lines.append(f"| {row.get('id')} | {row.get('state')} | {score} | "
                     f"{row.get('epochs')} | {assessment} |")
    (ROOT / "pipeline/reports/research_assessment_20260910-1113.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    for suffix in SUFFIXES:
        parent = ROOT / "Cluster/framework/model/Quard_model" / f"{BASE}_{suffix}"
        child = parent.with_name(parent.name + "_tr")
        assert not child.exists(), child
        child.mkdir()
        files = sorted(parent.glob("*.py"))
        assert len(files) == 7
        for source in files:
            ast.parse(source.read_text(encoding="utf-8"))
            shutil.copyfile(source, child / source.name)
        src_config = ROOT / "Cluster/configs/Quard" / f"ctf_hcg_csort_{suffix}" / f"{BASE}_{suffix}.yaml"
        dst_config = ROOT / "Cluster/configs/Quard" / f"ctf_hcg_csort_{suffix}_tr" / f"{BASE}_{suffix}_tr.yaml"
        dst_config.parent.mkdir()
        shutil.copyfile(src_config, dst_config)
    print(f"Read and snapshotted {len(inventory)} analyses and {len(rows)} ledger rows; copied3 parents")


if __name__ == "__main__":
    main()
