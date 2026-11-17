"""TRAIN-only geometric oracle: boundary cues, never inferred anchor labels."""
import hashlib
import json
from pathlib import Path

import numpy as np
import torch


def boundary_frame(points):
    xy = np.asarray(points, dtype=np.float64)[:, :2]
    center = xy.mean(0)
    centered = xy - center
    values, axes = np.linalg.eigh(centered.T @ centered / len(xy))
    local = centered @ axes
    lo, hi = local.min(0), local.max(0)
    # Axis 1 is the long principal axis; no directed front/back is inferred.
    ends = []
    for sign in (0, 1):
        end = np.array([(lo[0] + hi[0]) / 2, (lo[1], hi[1])[sign]])
        ends.append(center + end @ axes.T)
    corners = [center + np.array([x, y]) @ axes.T
               for x in (lo[0], hi[0]) for y in (lo[1], hi[1])]
    return dict(center=center, axes=axes, lo=lo, hi=hi,
                ends=np.array(ends), corners=np.array(corners),
                eigenvalues=values)


def distances(points, frame):
    center = np.asarray(points, dtype=np.float64)[:, :2].mean(0)
    local = (center - frame["center"]) @ frame["axes"]
    lo, hi = frame["lo"], frame["hi"]
    short = min(np.hypot(local[0] - np.clip(local[0], lo[0], hi[0]),
                         local[1] - y) for y in (lo[1], hi[1]))
    long = min(np.hypot(local[0] - x,
                        local[1] - np.clip(local[1], lo[1], hi[1]))
               for x in (lo[0], hi[0]))
    return dict(center=float(np.linalg.norm(center - frame["center"])),
                short_face=float(short), long_face=float(long),
                end_midpoint=float(np.linalg.norm(frame["ends"] - center, axis=1).min()),
                corner=float(np.linalg.norm(frame["corners"] - center, axis=1).min()),
                short_preference=float(long - short))


def controls():
    anchor = np.array([[x, y, 0] for x in (-1., 1.) for y in (-3., 3.)])
    subject = np.array([[0., 4., 0.]])
    expected = distances(subject, boundary_frame(anchor))
    assert expected["short_face"] == 1
    assert expected["short_preference"] > 0
    for angle in (0.2, 1.1, 2.4):
        c, s = np.cos(angle), np.sin(angle)
        rotation = np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
        offset = np.array([2., -5., 7.])
        actual = distances(subject @ rotation + offset,
                           boundary_frame(anchor @ rotation + offset))
        assert all(abs(actual[k] - expected[k]) < 1e-10 for k in expected)
    permuted = distances(subject, boundary_frame(anchor[::-1]))
    assert all(abs(permuted[k] - expected[k]) < 1e-10 for k in expected)
    scaled = distances(subject * 3, boundary_frame(anchor * 3))
    assert all(abs(scaled[k] - expected[k] * 3) < 1e-10 for k in expected)
    return 6


def main():
    root = Path("/data3/songcl/Project/Cluster_project")
    source = root / "pipeline/entity_binding_20260916/result.json"
    data = Path("/data3/songcl/data/data_cluster/scannetv2/train")
    phrases = ("short side", "long side", "corner of", "edge of", "end of", "foot of")
    records = json.loads(source.read_text())["rows"]
    selected = [r for r in records if any(p in r["caption"] for p in phrases)]
    rows, cache, sources = [], {}, {}
    torch.set_num_threads(1)
    for r in selected:
        scene = r["scene"]
        if scene not in cache:
            path = data / (scene + "_refer.pth")
            aggregation = data / (scene + ".aggregation.json")
            xyz, _, _, _, labels = torch.load(path, map_location="cpu", weights_only=False)
            xyz, labels = np.asarray(xyz), np.asarray(labels)
            names = {int(g["id"]): g["label"] for g in
                     json.loads(aggregation.read_text())["segGroups"]}
            objects = {int(i): xyz[labels == i] for i in np.unique(labels) if i >= 0}
            cache[scene] = objects, names
            for p in (path, aggregation):
                sources[str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
        objects, names = cache[scene]
        entities = []
        for entity in r["entities"]:
            if entity["node_id"] == 0:
                continue
            noun = " ".join(s["text"] for s in entity["spans"]["target_char_span"]).lower()
            candidates = []
            for obj, points in objects.items():
                if names.get(obj) != noun:
                    continue
                frame = boundary_frame(points)
                scores = {role: distances(objects[r[role]], frame)
                          if r[role] in objects else None
                          for role in ("target", "winner")}
                candidates.append(dict(instance=obj,
                    self_target=obj == r["target"], self_winner=obj == r["winner"],
                    eigenvalues=frame["eigenvalues"].tolist(),
                    extent=(frame["hi"] - frame["lo"]).tolist(), **scores))
            entities.append(dict(node_id=entity["node_id"], noun=noun, candidates=candidates))
        rows.append(dict(scene=scene, ann_id=r["ann_id"], caption=r["caption"],
                         cues=[p for p in phrases if p in r["caption"]],
                         target=r["target"], winner=r["winner"],
                         success=r["success"], confident_wrong=r["confident_wrong"],
                         edges=r["edges"], entities=entities))
    result = dict(scope="Existing fixed123TRAIN, all8 matching boundary-cue expressions. "
                  "Raw GT geometric oracle only; all exact-name candidates retained, "
                  "including self candidates with flags. PCA rectangles are proxies, "
                  "not object front/back or intended-anchor truth. Caption cues may "
                  "describe another object. No model or efficacy/novelty admission.",
                  checks_passed=controls(), rows=rows,
                  denominator=dict(all_expressions=len(records), selected=len(rows),
                                   scenes=len({r["scene"] for r in rows})),
                  sources=sources)
    for p in (source, Path(__file__)):
        result["sources"][str(p)] = hashlib.sha256(p.read_bytes()).hexdigest()
    out = root / "pipeline/anchor_boundary_observability_20260916"
    out.mkdir(exist_ok=True)
    (out / "result.json").write_text(json.dumps(result, indent=2))
    print(json.dumps(dict(denominator=result["denominator"], checks=result["checks_passed"])))
    for r in rows:
        for entity in r["entities"]:
            for candidate in entity["candidates"]:
                if not candidate["self_target"] and not candidate["self_winner"]:
                    print(json.dumps(dict(scene=r["scene"], ann=r["ann_id"],
                        noun=entity["noun"], anchor=candidate["instance"],
                        target=candidate["target"], winner=candidate["winner"])))


if __name__ == "__main__":
    main()
