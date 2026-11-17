"""Native dataset grouping coverage, without reorganizing training examples."""
from collections import Counter
import hashlib
import json
from pathlib import Path

base = Path(__file__).with_name("coverage_stage_capture_20260916.py")
source = base.read_text().split("loader = build_dataloader")[0]
ns = {"__file__": str(base)}
exec(compile(source, str(base), "exec"), ns)
dataset = ns["dataset"]
rows = []
for index, group in enumerate(dataset.scene_inputs):
    assert len({r["scene_id"] for r in group}) == 1
    counts = Counter(tuple(sorted(r.get("object_ids", [int(r["object_id"])]))) for r in group)
    eligible = sum(n for ids, n in counts.items() if len(ids) == 1 and n > 1)
    rows.append(dict(group=index, scene=group[0]["scene_id"], expressions=len(group),
        eligible_expressions=eligible,
        object_multiplicities=[dict(ids=list(ids), count=n) for ids, n in sorted(counts.items())],
        ann_ids=[r["ann_id"] for r in group]))
summary = dict(groups=len(rows), expressions=sum(r["expressions"] for r in rows),
    eligible_groups=sum(r["eligible_expressions"] > 0 for r in rows),
    eligible_expressions=sum(r["eligible_expressions"] for r in rows),
    scenes=len({r["scene"] for r in rows}),
    eligible_scenes=len({r["scene"] for r in rows if r["eligible_expressions"] > 0}),
    lang_num_max=ns["cfg"].data.train.lang_num_max)
destination = ns["ROOT"].parent / "pipeline/interchange_training_coverage_20260916"
destination.mkdir(exist_ok=True)
paths = [Path(__file__), base, ns["config"],
         ns["ROOT"] / "framework/dataset/scannetv2.py"]
report = dict(summary=summary, groups=rows,
    sources={str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},
    limitations="Native scene_inputs before stochastic augmentation;metadata eligibility,not "
    "visible-target or full backward coverage. Only within one dataset group shares augmentation. "
    "Never join separate groups by equal sceneID alone. No sampler/config/model changes.")
(destination / "result.json").write_text(json.dumps(report, indent=2))
print(json.dumps(summary))
