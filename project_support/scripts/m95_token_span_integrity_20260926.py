"""Read-only audit of native TRAIN text/graph supervision token alignment."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path

SOURCE_SHA = "018754b90bcc27d5746bb50d6c35d6e7a35fd39519ac669e3fbe3fa6f425922d"
GRAPH_SHA = "e058fdd5bee5acd4fce7e78516d88b07581131e9fe83afd226cb835e80942e08"
CAPTURE_SHA = "5a1ddd9a906983416adbfb0e9d03b386de92a21803fdf20afe40740b5a69687e"


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def map_span(encoded, beg, end):
    a = encoded.char_to_token(beg)
    b = encoded.char_to_token(end - 1)
    if a is None:
        for offset in (1, 2):
            a = encoded.char_to_token(beg + offset)
            if a is not None:
                break
    if b is None:
        for offset in (2, 3):
            b = encoded.char_to_token(end - offset)
            if b is not None:
                break
    return a, b


def audit(source, graphs, frozen, tokenizer):
    descriptions = defaultdict(list)
    for item in source:
        descriptions[(item["scene_id"], int(item["ann_id"]), str(item["object_id"]))].append(item)
    result = []
    if len(frozen["rows"]) != 256:
        raise ValueError("Frozen cohort must have exactly 256 rows")
    for item in frozen["rows"]:
        key = item["scene"], int(item["ann_id"]), str(item["target"])
        if len(descriptions[key]) != 1:
            raise ValueError("Description identity not unique: " + str(key))
        graph = graphs[key[0]][str(key[1])]
        caption = " ".join(graph["utterance"].replace(",", " ,").split())
        model_text = caption + " . not mentioned"
        original = tokenizer(caption, return_offsets_mapping=True)
        actual = tokenizer(model_text, return_offsets_mapping=True)
        if original["input_ids"][:-1] != actual["input_ids"][:len(original["input_ids"]) - 1]:
            raise ValueError("Appended suffix modified caption token IDs")
        spans = []
        for node in graph["graph_node"]:
            role = "target" if node["node_id"] == 0 else "other"
            keys = ("target_char_span", "mod_char_span", "pron_char_span", "rel_char_span") if role == "target" else ("target_char_span",)
            for name in keys:
                for pair in node.get(name, []):
                    beg, end = map(int, pair)
                    bounds = 0 <= beg < end <= len(caption)
                    start, stop = map_span(original, beg, end) if bounds else (None, None)
                    mapped = start is not None and stop is not None and start <= stop < 256
                    same = mapped and all(
                        original["input_ids"][pos] == actual["input_ids"][pos]
                        for pos in range(start, stop + 1)
                    )
                    text = caption[beg:end] if bounds else ""
                    offsets = original["offset_mapping"][start:stop + 1] if mapped else []
                    token_text = caption[offsets[0][0]:offsets[-1][1]] if offsets else ""
                    spans.append({
                        "role": role, "kind": name, "span": [beg, end],
                        "text": text, "token_text": token_text,
                        "mapped": bool(mapped), "same_model_tokens": bool(same),
                        "aligned_text": bool(mapped and text.strip().lower() == token_text.strip().lower()),
                        "token_positions": [start, stop],
                    })
        target = [s for s in spans if s["role"] == "target" and s["kind"] == "target_char_span"]
        result.append({
            "manifest_index": item["manifest_index"], "scene": key[0], "ann_id": key[1],
            "target": key[2], "stratum": item["stratum"], "failed": item["failed"],
            "token_count": len(actual["input_ids"]),
            "target_span_count": len(target),
            "target_unreachable": bool(target) and not any(s["mapped"] and s["same_model_tokens"] for s in target),
            "target_unaligned": bool(target) and not any(s["aligned_text"] for s in target),
            "spans": spans,
        })

    def counts(rows):
        return {
            "rows": len(rows), "scenes": len({r["scene"] for r in rows}),
            "failures": sum(r["failed"] for r in rows),
            "missing_target_span": sum(not r["target_span_count"] for r in rows),
            "unreachable_target": sum(r["target_unreachable"] for r in rows),
            "unaligned_target": sum(r["target_unaligned"] for r in rows),
            "over_256_tokens": sum(r["token_count"] > 256 for r in rows),
            "other_spans": sum(len([s for s in r["spans"] if s["role"] == "other"]) for r in rows),
            "unreachable_other_spans": sum(
                not s["mapped"] or not s["same_model_tokens"]
                for r in rows for s in r["spans"] if s["role"] == "other"
            ),
        }
    return {
        "contract": "m95_token_span_integrity_v1", "admission": False,
        "source_sha256": SOURCE_SHA, "graph_sha256": GRAPH_SHA, "capture_sha256": CAPTURE_SHA,
        "summary": {name: counts(group) for name, group in (
            ("all", result),
            ("failed", [r for r in result if r["failed"]]),
            ("success", [r for r in result if not r["failed"]]),
            ("ambiguous", [r for r in result if r["stratum"] == "ambiguous"]),
            ("class_unique", [r for r in result if r["stratum"] == "class_unique"]),
        )}, "rows": result,
    }


def main():
    from transformers import RobertaTokenizerFast

    p = argparse.ArgumentParser()
    for name in ("source", "graphs", "cohort", "tokenizer", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    args = p.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    for name, expected in (("source", SOURCE_SHA), ("graphs", GRAPH_SHA)):
        if sha(getattr(args, name)) != expected:
            raise ValueError(name + " SHA differs")
    cohort = json.loads(args.cohort.read_text(encoding="utf-8"))
    if cohort.get("capture_sha256") != CAPTURE_SHA:
        raise ValueError("Cohort capture differs")
    tokenizer = RobertaTokenizerFast.from_pretrained(str(args.tokenizer), local_files_only=True)
    result = audit(
        json.loads(args.source.read_text(encoding="utf-8")),
        json.loads(args.graphs.read_text(encoding="utf-8")), cohort, tokenizer,
    )
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(result["summary"], sort_keys=True))


if __name__ == "__main__":
    main()
