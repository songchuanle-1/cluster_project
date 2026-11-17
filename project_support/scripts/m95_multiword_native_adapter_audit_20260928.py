"""Static compatibility check for the frozen phrase cohort and native producer."""
import ast
import argparse
import hashlib
import json
from pathlib import Path


MANIFEST_SHA = "85e108e8c86d65bcdbdc25061987e0a973fa45b35b00030d0721d359da720040"
PRODUCER_SHA = "c76eae8906bc8abe136acd4df8fe5eb4e78a6755508d80a318a9371c4658d821"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--manifest", type=Path, required=True)
    parser.add_argument("--producer", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if (args.output.exists() or sha(args.manifest) != MANIFEST_SHA
            or sha(args.producer) != PRODUCER_SHA):
        raise ValueError("Frozen input changed or output exists")
    doc = json.loads(args.manifest.read_text(encoding="utf-8"))
    tree = ast.parse(args.producer.read_text(encoding="utf-8"))
    constants = {}
    for node in tree.body:
        if isinstance(node, ast.Assign) and len(node.targets) == 1:
            target = node.targets[0]
            if isinstance(target, ast.Name) and target.id in ("MANIFEST_CONTRACT", "MANIFEST_ROWS"):
                constants[target.id] = ast.literal_eval(node.value)
    if doc["contract"] != "m95_multiword_capture_manifest_v1":
        raise ValueError("New manifest contract differs")
    records = doc["records"]
    keys = [(r["scene"], int(r["ann_id"])) for r in records]
    if (len(records) != 31 or len(set(keys)) != 31
            or len({r["scene"] for r in records}) != 2
            or constants != {"MANIFEST_CONTRACT": "m95_preregistered_identity_controls_v1",
                             "MANIFEST_ROWS": 256}):
        raise ValueError("Frozen native contracts differ")
    result = {
        "contract": "m95_multiword_native_adapter_audit_v1",
        "admission": False,
        "inputs": {"manifest": MANIFEST_SHA, "producer": PRODUCER_SHA},
        "manifest_rows": len(records),
        "manifest_scenes": len({r["scene"] for r in records}),
        "manifest_exposed": sum(r["arm"] == "phrase" for r in records),
        "manifest_unique_controls": sum(r["arm"] == "phrase_absent" for r in records),
        "producer_contract": constants["MANIFEST_CONTRACT"],
        "producer_rows": constants["MANIFEST_ROWS"],
        "direct_compatibility": False,
        "next_action": "Review a separate adapter with identity, source hash, original text, target and checkpoint parity; do not coerce the frozen producer or run while GPU7 has foreign work.",
        "limits": "Static compatibility only; no model outcome, GPU run, backward or admission.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
