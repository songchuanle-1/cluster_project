"""Verify repaired diagnostic artifacts preserve all numerical evidence."""
import hashlib
import json
from pathlib import Path
from diagnostic_identity import attach_description, manifest_index

root = Path(__file__).resolve().parents[1]
records = []
for name in ("same_target_native", "same_target_support", "scene_interchange"):
    original = root / f"pipeline/reports/{name}_20260916.json"
    corrected = original.with_name(original.stem + "_metadata_corrected.json")
    a, b = [json.loads(p.read_text(encoding="utf-8")) for p in (original, corrected)]
    index = manifest_index(a["manifest"])
    if "rows" in a:
        groups = [(a["rows"], b["rows"])]
    else:
        groups = [(x["branches"][key]["rows"], y["branches"][key]["rows"])
                  for x, y in zip(a["batches"], b["batches"]) for key in x["branches"]]
    total = 0
    for old, new in groups:
        assert len(old) == len(new)
        for x, y in zip(old, new):
            assert attach_description(x, index) == y
            total += 1
            # Restore just the original text; entire artifact must then match.
            y["utterance"] = x["utterance"]
    assert a == b
    records.append(dict(name=name, rows=total, text_only_change=True,
        evidence=[dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
                  for p in (original, corrected)]))
output = root / "pipeline/reports/description_metadata_verification_20260916.json"
output.write_text(json.dumps(dict(records=records, all_passed=True,
    sources=[dict(path=str(p.relative_to(root)), sha256=hashlib.sha256(p.read_bytes()).hexdigest())
             for p in (Path(__file__), Path(__file__).with_name("diagnostic_identity.py"))]),
    indent=2), encoding="utf-8")
print(json.dumps(records))
