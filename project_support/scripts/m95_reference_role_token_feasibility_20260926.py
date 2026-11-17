"""CPU-only exact token-span feasibility for frozen explicit-other mentions."""
import argparse
import hashlib
import json
import re
from pathlib import Path

ROLE_SHA = "65e110e0a11c7486c5f552b94c917525412d6cfc8e52a10974f709a69cafc01e"
ENTITY_SHA = None
REPLACEMENTS = ("the", "that", "this", "some", "other", "one", "a")


def audit(role, entities, tokenizer):
    indexed = {(r["scene"], int(r["ann_id"])): r for r in entities["rows"]}
    if len(indexed) != len(entities["rows"]):
        raise ValueError("Duplicate entity binding")
    rows = []
    for mention in role["control_manifest"]:
        if mention["cue"] != "explicit_other_cue":
            continue
        identity = mention["scene"], int(mention["ann_id"])
        record = indexed[identity]
        if record["caption"] != mention["caption"]:
            raise ValueError("Caption binding differs")
        entity = next(
            e for e in record["entities"]
            if int(e["node_id"]) == int(mention["node_id"])
        )
        spans = entity["spans"]["target_char_span"]
        if not spans or not all(s["valid"] for s in spans):
            raise ValueError("Missing role noun span")
        noun_start = min(int(s["span"][0]) for s in spans)
        text = record["caption"] + " . not mentioned"
        candidates = list(re.finditer(r"\b(?:another|different)\b", text[:noun_start]))
        if not candidates:
            raise ValueError("No preceding explicit-other marker")
        marker = candidates[-1]
        between = text[marker.end():noun_start]
        if between.strip():
            raise ValueError("Role marker is not adjacent to noun")
        original = tokenizer(text, return_tensors="pt")
        token_positions = sorted({
            original.char_to_token(c)
            for c in range(marker.start(), marker.end())
        } - {None})
        if not token_positions:
            raise ValueError("Marker has no native token")
        old = original["input_ids"][0]
        controls = []
        for replacement in REPLACEMENTS:
            edited = text[:marker.start()] + replacement + text[marker.end():]
            ids = tokenizer(edited, return_tensors="pt")["input_ids"][0]
            if ids.shape != old.shape:
                continue
            changed = (ids != old).nonzero().flatten().tolist()
            if changed and set(changed).issubset(token_positions):
                controls.append({"replacement": replacement,
                                 "changed_tokens": changed})
        rows.append({
            "scene": identity[0], "ann_id": identity[1],
            "node_id": int(mention["node_id"]),
            "marker": marker.group(), "char_span": [marker.start(), marker.end()],
            "token_positions": token_positions, "same_length_controls": controls,
        })
    return {
        "contract": "m95_reference_role_token_feasibility_v1",
        "admission": False, "role_sha256": ROLE_SHA,
        "rows": rows,
        "summary": {
            "mentions": len(rows),
            "expressions": len({(r["scene"], r["ann_id"]) for r in rows}),
            "same_length_eligible": sum(bool(r["same_length_controls"]) for r in rows),
        },
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--role", type=Path, required=True)
    p.add_argument("--entities", type=Path, required=True)
    p.add_argument("--tokenizer", type=Path, required=True)
    p.add_argument("--output", type=Path, required=True)
    args = p.parse_args()
    if args.output.exists() or hashlib.sha256(
        args.role.read_bytes()).hexdigest() != ROLE_SHA:
        raise ValueError("Output exists or role manifest differs")
    from transformers import RobertaTokenizerFast

    tokenizer = RobertaTokenizerFast.from_pretrained(str(args.tokenizer),
                                                     local_files_only=True)
    result = audit(json.loads(args.role.read_text(encoding="utf-8")),
                   json.loads(args.entities.read_text(encoding="utf-8")),
                   tokenizer)
    result["entity_sha256"] = hashlib.sha256(args.entities.read_bytes()).hexdigest()
    args.output.write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
