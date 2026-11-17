"""Audit whether frozen contact expressions have explicit parsed graph edges."""
import argparse
import hashlib
import json
from pathlib import Path


SCREEN_SHA = "cdaef8fc2fae29b47be303cd45356c7e6c11d6e65f2d1828972aaf62f6afe996"
MANIFEST_SHA = "4ad801fe41fb2fb50e30c882edeeff9ff0c70440918c8b661a089da3332d7023"


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def analyze(screen, manifest, graphs):
    by_index = {int(r["manifest_index"]): r for r in manifest["rows"]}
    if len(by_index) != 256 or len(screen["rows"]) != 256:
        raise ValueError("Frozen cohort incomplete")
    result = []
    for row in screen["rows"]:
        index = int(row["manifest_index"])
        entry = by_index[index]
        scene, ann = entry["scene_id"], str(entry["ann_id"])
        if row["scene"] != scene:
            raise ValueError("Scene mismatch")
        graph = graphs.get(scene, {}).get(ann)
        edges = [] if graph is None else graph.get("graph_edge", [])
        relations = [str(edge.get("relation", "")) for edge in edges]
        if row["contact_phrases"]:
            result.append({
                "manifest_index": index, "scene": scene,
                "stratum": row["stratum"], "failed": row["failed"],
                "phrases": row["contact_phrases"], "graph_present": graph is not None,
                "edge_count": len(edges), "relations": relations,
                "has_contact_relation": any(
                    any(term in relation.lower() for term in
                        ("top", "under", "below", "against", "attach",
                         "hanging", "standing on", "sitting on", "resting on"))
                    for relation in relations),
            })
    return {
        "contact_rows": len(result),
        "ambiguous": {
            "rows": sum(r["stratum"] == "ambiguous" for r in result),
            "failures": sum(r["stratum"] == "ambiguous" and r["failed"] for r in result),
            "with_graph": sum(r["stratum"] == "ambiguous" and r["graph_present"] for r in result),
            "with_contact_edge": sum(r["stratum"] == "ambiguous" and r["has_contact_relation"] for r in result),
            "failed_with_contact_edge": sum(
                r["stratum"] == "ambiguous" and r["failed"] and r["has_contact_relation"]
                for r in result),
        },
        "rows": result,
    }


def main():
    parser = argparse.ArgumentParser()
    for name in ("screen", "manifest", "graphs", "output"):
        parser.add_argument("--" + name, type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output exists")
    if digest(args.screen) != SCREEN_SHA or digest(args.manifest) != MANIFEST_SHA:
        raise ValueError("Frozen input hash differs")
    screen = json.loads(args.screen.read_text(encoding="utf-8"))
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    graphs = json.loads(args.graphs.read_text(encoding="utf-8"))
    result = analyze(screen, manifest, graphs)
    result.update({"contract": "m95_contact_graph_audit_v1",
                   "screen_sha256": SCREEN_SHA, "manifest_sha256": MANIFEST_SHA,
                   "graphs_sha256": digest(args.graphs), "admission": False})
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="ascii")
    print(json.dumps({k: result[k] for k in ("contact_rows", "ambiguous")}, sort_keys=True))


if __name__ == "__main__":
    main()
