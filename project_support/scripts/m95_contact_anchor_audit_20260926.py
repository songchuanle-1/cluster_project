"""Strict graph-subject to native ScanRefer scene-object binding audit."""
import argparse
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path


SCREEN_SHA = "cdaef8fc2fae29b47be303cd45356c7e6c11d6e65f2d1828972aaf62f6afe996"
GRAPH_AUDIT_SHA = "d706fdba1ff98822d1740b19637d9d6ca13b3ce0099dabd05913ec62bc9d5a3d"
TERMS = ("top", "under", "below", "against", "attach", "hanging",
         "standing on", "sitting on", "resting on")
PRONOUNS = {"it", "this", "that", "they", "them", "one", "there"}


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def norm(text):
    return " ".join(re.findall(r"[a-z]+", str(text).lower()))


def main():
    p = argparse.ArgumentParser()
    for name in ("screen", "graph-audit", "manifest", "source", "graphs", "output"):
        p.add_argument("--" + name, type=Path, required=True)
    a = p.parse_args()
    if a.output.exists():
        raise ValueError("Output exists")
    if digest(a.screen) != SCREEN_SHA or digest(a.graph_audit) != GRAPH_AUDIT_SHA:
        raise ValueError("Frozen input differs")
    screen = json.loads(a.screen.read_text(encoding="utf-8"))
    audit = json.loads(a.graph_audit.read_text(encoding="utf-8"))
    manifest = json.loads(a.manifest.read_text(encoding="utf-8"))
    source = json.loads(a.source.read_text(encoding="utf-8"))
    graphs = json.loads(a.graphs.read_text(encoding="utf-8"))
    audited = {int(r["manifest_index"]): r for r in audit["rows"]}
    names = defaultdict(lambda: defaultdict(set))
    for item in source:
        names[item["scene_id"]][norm(item["object_name"])].add(str(item["object_id"]))
    by_index = {int(r["manifest_index"]): r for r in manifest["rows"]}
    rows = []
    for row in screen["rows"]:
        if row["stratum"] != "ambiguous" or not row["contact_phrases"]:
            continue
        entry = by_index[int(row["manifest_index"])]
        graph_audit_row = audited[int(row["manifest_index"])]
        if (row["scene"] != entry["scene_id"] or
                graph_audit_row["scene"] != row["scene"] or
                graph_audit_row["failed"] != row["failed"]):
            raise ValueError("Frozen scene/outcome binding differs")
        edges = graphs[row["scene"]][str(entry["ann_id"])]["graph_edge"]
        candidates = []
        for edge in edges:
            if not any(term in norm(edge["relation"]) for term in TERMS):
                continue
            subject = norm(edge.get("subject", ""))
            matches = sorted(names[row["scene"]].get(subject, set())) if subject not in PRONOUNS else []
            candidates.append({"relation": edge["relation"], "subject": subject,
                               "match_count": len(matches), "object_ids": matches})
        rows.append({"manifest_index": row["manifest_index"], "scene": row["scene"],
                     "failed": row["failed"], "contact_edges": candidates,
                     "has_unique_anchor": any(e["match_count"] == 1 for e in candidates)})
    if len(rows) != 27:
        raise ValueError("Ambiguous contact denominator changed")
    summary = {}
    for failed in (True, False):
        group = [r for r in rows if r["failed"] == failed]
        summary["failed" if failed else "successful"] = {
            "rows": len(group), "with_unique_anchor": sum(r["has_unique_anchor"] for r in group),
            "with_contact_edge": sum(bool(r["contact_edges"]) for r in group),
        }
    output = {"contract": "m95_contact_anchor_resolvability_v1",
              "screen_sha256": SCREEN_SHA, "graph_audit_sha256": GRAPH_AUDIT_SHA,
              "manifest_sha256": digest(a.manifest), "source_sha256": digest(a.source),
              "graphs_sha256": digest(a.graphs), "summary": summary,
              "rows": rows, "admission": False}
    a.output.write_text(json.dumps(output, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps(summary, sort_keys=True))


if __name__ == "__main__":
    main()
