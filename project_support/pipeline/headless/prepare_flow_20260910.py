"""Snapshot research evidence and mechanically copy the independent flow parent."""
import ast
import argparse
import csv
import hashlib
import json
from pathlib import Path
import shutil

ROOT = Path("D:/project/cluster_project")
BASE = "model_base1_quard2_c2f_enc_lite_posA_l1_ctf_hcg_csort"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--suffix", choices=("mqhf", "mqhc"), default="mqhf")
    parser.add_argument("--stamp", choices=("1316", "1324"), default="1316")
    args = parser.parse_args()
    stamp = "20260910-" + args.stamp
    shutil.copyfile(ROOT / "pipeline/goal.json",
                    ROOT / f"pipeline/reviews/goal_snapshot_{stamp}.json")
    evidence = []
    for p in sorted((ROOT / "pipeline/analyses").glob("*.md")):
        content = p.read_text(encoding="utf-8")
        evidence.append(dict(path=str(p.relative_to(ROOT)),
                             sha256=hashlib.sha256(p.read_bytes()).hexdigest(),
                             content=content))
    rows = list(csv.DictReader((ROOT / "pipeline/experiments.csv").open(encoding="utf-8-sig")))
    inventory = dict(analysis_count=len(evidence), analyses=evidence, ledger=rows)
    (ROOT / f"pipeline/reports/research_inventory_{stamp}.json").write_text(
        json.dumps(inventory, ensure_ascii=False, indent=2), encoding="utf-8")
    lines = ["# Research Ledger Assessment", "", "Historical duplicates are not independent runs.",
             f"Source analysis content and paired metric tables: research_inventory_{stamp}.json.",
             "Compromised M169/M172/M174 stopping evidence cannot establish convergence.",
             "", "| ID | State | mIoU | Motivation contribution |",
             "|----|-------|------|-------------------------|"]
    for row in rows:
        try:
            value = float(row["best_miou"])
        except ValueError:
            value = None
        assessment = ("No usable efficacy metric" if value is None else
                      "Champion reference; robustness unproven" if value >= .502 else
                      "Context candidate above baseline, no champion improvement" if value > .4894 else
                      "No observed baseline improvement")
        if row["state"] in ("stopped_unknown", "crashed") or row["id"].startswith(("M169-", "M172-", "M174-")):
            assessment += "; compromised termination"
        lines.append(f"| {row['id']} | {row['state']} | {row['best_miou']} | {assessment} |")
    (ROOT / f"pipeline/reports/research_assessment_{stamp}.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8")
    parent = ROOT / "Cluster/framework/model/Quard_model" / (BASE + "_" + args.suffix)
    child = parent.with_name(parent.name + "_tr")
    assert not child.exists()
    child.mkdir()
    files = list(parent.glob("*.py"))
    assert len(files) == 7
    for source in files:
        ast.parse(source.read_text(encoding="utf-8"))
        shutil.copyfile(source, child / source.name)
    old = ROOT / "Cluster/configs/Quard" / ("ctf_hcg_csort_" + args.suffix) / (parent.name + ".yaml")
    new = ROOT / "Cluster/configs/Quard" / ("ctf_hcg_csort_" + args.suffix + "_tr") / (child.name + ".yaml")
    new.parent.mkdir()
    shutil.copyfile(old, new)
    print("Read all analyses and ledger:", len(evidence), len(rows), "; copied7 independent files")


if __name__ == "__main__":
    main()
