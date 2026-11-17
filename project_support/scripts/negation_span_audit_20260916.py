"""Lexical cue incidence in fixed TRAIN evidence; not semantic scope labels."""
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
source = ROOT/"pipeline/reports/entity_binding_20260916.json"
data = json.loads(source.read_text(encoding="utf-8"))["rows"]
pattern = re.compile(r"\b(?:no|not|without|neither|nor|except)\b", re.I)
rows = []
for record in data:
    cues = []
    for match in pattern.finditer(record["caption"]):
        coverage = []
        for entity in record["entities"]:
            for kind, spans in entity["spans"].items():
                for span in spans:
                    start, end = span["span"]
                    if start <= match.start() and match.end() <= end:
                        coverage.append(dict(node=entity["node_id"], kind=kind))
        cues.append(dict(text=match.group(), span=list(match.span()), coverage=coverage))
    if cues:
        rows.append(dict(scene=record["scene"], ann_id=record["ann_id"],
                         caption=record["caption"], success=record["success"],
                         confident_wrong=record["confident_wrong"],
                         cues=cues, edges=record["edges"]))
summary = {}
for name, predicate in (
    ("success", lambda r: r["success"]),
    ("confident_wrong", lambda r: r["confident_wrong"]),
    ("other_failure", lambda r: not r["success"] and not r["confident_wrong"]),
):
    population = [r for r in data if predicate(r)]
    selected = [r for r in rows if predicate(r)]
    summary[name] = dict(denominator=len(population), expressions=len(selected),
                         cues=sum(len(r["cues"]) for r in selected),
                         covered=sum(bool(c["coverage"]) for r in selected for c in r["cues"]))
assert sum(s["denominator"] for s in summary.values()) == len(data) == 123
assert len({(r["scene"], r["ann_id"]) for r in data}) == 123
probe = next(r for r in rows if r["scene"] == "scene0320_00" and r["ann_id"] == 19)
assert probe["confident_wrong"] and probe["cues"][0]["text"] == "no"
assert not probe["cues"][0]["coverage"]
result = dict(
    summary=summary, rows=rows,
    limitations="Lexical cue detection only, not negation scope or predicate truth. "
    "Saved entity audit contains target/modifier/relation spans, NOT pronoun spans. "
    "No claim that cue is absent from full contextual encoder or all losses. "
    "No causal explanation from cue incidence, no extra annotations or model change.",
    sources={str(p.relative_to(ROOT)): hashlib.sha256(p.read_bytes()).hexdigest()
             for p in (source, Path(__file__))},
)
destination = ROOT/"pipeline/reports/negation_span_audit_20260916.json"
destination.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(json.dumps(result, indent=2))
