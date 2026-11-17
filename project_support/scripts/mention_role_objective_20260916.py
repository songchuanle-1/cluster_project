"""Static role-likelihood audit and deterministic TRAIN control inventory."""
import hashlib
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
source = ROOT / "pipeline/reports/mention_gradient_20260916.json"
binding_path = ROOT / "pipeline/reports/entity_binding_20260916.json"
bindings = {(r["scene"], r["ann_id"]): r
            for r in json.loads(binding_path.read_text())["rows"]}
rows = []
for row in json.loads(source.read_text())["rows"]:
    graph = bindings[(row["scene"], row["ann_id"])]
    for mention in row["mentions"]:
        entity = next(e for e in graph["entities"] if e["node_id"] == mention["node_id"])
        start = min(s["span"][0] for s in entity["spans"]["target_char_span"])
        prefix = row["caption"][:start]
        sentence_prefix = prefix.rsplit(".", 1)[-1].strip().lower()
        # Text-only strata for negative controls, NOT coreference labels.
        if re.search(r"\b(another|different|other)\b", sentence_prefix):
            cue = "explicit_other_cue"
        elif sentence_prefix in ("the", "this"):
            cue = "sentence_initial_definite_repeat"
        else:
            cue = "unknown"
        rows.append(dict(scene=row["scene"], ann_id=row["ann_id"],
                         node_id=mention["node_id"], noun=mention["noun"],
                         cue=cue, sentence_prefix=sentence_prefix,
                         caption=row["caption"], success=row["success"],
                         confident_wrong=row["confident_wrong"]))


def loss(p, pi):
    return -math.log(pi * p + (1 - pi) * (1 - p))


def grad_logit(p, pi):
    return -(2 * pi - 1) * p * (1 - p) / (pi * p + (1 - pi) * (1 - p))


checks = []
grid = (.01, .1, .3, .5, .7, .9, .99)
assert all(abs(loss(p, .5) - math.log(2)) < 1e-12 for p in grid)
assert all(grad_logit(p, .5) == 0 for p in grid)
checks.append("Uniform independent role prior: constant loss log2 and zero gradient.")
for p in grid:
    z = math.log(p / (1 - p))
    for pi in (.1, .3, .7, .9):
        h = 1e-5
        sigmoid = lambda x: 1 / (1 + math.exp(-x))
        finite = (loss(sigmoid(z+h), pi)-loss(sigmoid(z-h), pi))/(2*h)
        assert abs(finite-grad_logit(p, pi)) < 1e-9
checks.append("Analytic logit gradient agrees with central finite differences.")
for p in grid:
    minimum = min(loss(p, 0), loss(p, 1))
    assert abs(minimum + math.log(max(p, 1-p))) < 1e-12
checks.append("Free per-example role minimization rewards current certainty, not true role.")
assert loss(.99, 1) == loss(.01, 0)
checks.append("Opposite role assignments have equal optimum confidence cost.")
for p in grid:
    assert abs(loss(p, 1) + math.log(p)) < 1e-12
    assert abs(loss(p, 0) + math.log(1-p)) < 1e-12
checks.append("Known role reduces exactly to ordinary binary cross entropy.")
summary = {}
for cue in ("explicit_other_cue", "sentence_initial_definite_repeat", "unknown"):
    subset = [r for r in rows if r["cue"] == cue]
    summary[cue] = dict(mentions=len(subset),
                       expressions=len({(r["scene"], r["ann_id"]) for r in subset}),
                       confident_wrong_mentions=sum(r["confident_wrong"] for r in subset),
                       success_mentions=sum(r["success"] for r in subset))
report = dict(
    summary=summary, control_manifest=rows, checks=checks,
    formula="L=-log(pi*p+(1-pi)*(1-p)); p=sigmoid(z)",
    scope="Static algebra and already-captured TRAIN text only; no native execution.",
    limitations="This rejects only an independent/unidentified binary role mixture. "
    "A role prior learned from genuinely identifying inputs is not ruled out. "
    "Lexical strata are not coreference truth or new training labels. A definite "
    "noun phrase can name a different entity. No efficacy or novelty established.",
    sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (Path(__file__), source, binding_path)},
)
destination = ROOT / "pipeline/reports/mention_role_objective_20260916.json"
destination.write_text(json.dumps(report, indent=2), encoding="utf-8")
print(json.dumps(dict(summary=summary, checks=checks), indent=2))
