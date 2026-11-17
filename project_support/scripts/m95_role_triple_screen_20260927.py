"""Count exact same-scene, same-instance, same-FPS role triples."""
import argparse
import hashlib
import json
from collections import defaultdict
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--expected-sha", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise ValueError("Output already exists")
    data = args.source.read_bytes()
    if hashlib.sha256(data).hexdigest() != args.expected_sha:
        raise ValueError("Source hash differs")
    source = json.loads(data)
    scenes = defaultdict(list)
    for row in source["rows"]:
        scenes[row["scene"]].append(row)
    if len(source["rows"]) != 128 or len(scenes) != 32:
        raise ValueError("Population differs")
    triples = []
    for scene, group in scenes.items():
        if len(group) != 4 or len({r["batch_input_sha256"] for r in group}) != 1:
            raise ValueError("Scene expressions do not share captured input")
        for a in group:
            if len(a["target_instances"]) != 1:
                raise ValueError("Native target is not unique")
            target = int(a["target_instances"][0])
            roles = {
                id(b): {
                    float(entry[2]): set()
                    for entry in b["unprotected_seed_roles"]
                    if int(entry[1]) == target
                }
                for b in group if b is not a
            }
            for b in group:
                if b is a:
                    continue
                for seed, instance, label in b["unprotected_seed_roles"]:
                    if int(instance) == target:
                        roles[id(b)][float(label)].add(int(seed))
            for b in group:
                if b is a:
                    continue
                context = roles[id(b)].get(.25, set())
                if not context:
                    continue
                for c in group:
                    if c is a or c is b:
                        continue
                    shared = sorted(context & roles[id(c)].get(0., set()))
                    if shared:
                        triples.append({
                            "scene": scene, "target_instance": target,
                            "target_ann": a["ann_id"],
                            "context_ann": b["ann_id"],
                            "zero_ann": c["ann_id"],
                            "shared_fps_positions": shared,
                        })
    result = {
        "contract": "m95_role_triple_screen_v1", "admission": False,
        "source_sha256": args.expected_sha, "expressions": 128,
        "scenes": 32, "role_triples": len(triples),
        "triple_scenes": len({r["scene"] for r in triples}),
        "shared_positions": sum(len(r["shared_fps_positions"]) for r in triples),
        "triples": triples,
        "limits": "Feasibility only. Target-expression positive labels and gradients "
                  "must be verified on native same-forward tensors.",
    }
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n",
                           encoding="utf-8")
    print(json.dumps({k: result[k] for k in (
        "role_triples", "triple_scenes", "shared_positions")}))


if __name__ == "__main__":
    main()
