"""Text-scope audit and finite-energy tests; no inferred scene-relation labels."""
from collections import Counter
from datetime import datetime
import hashlib
import json
import math
from pathlib import Path
import re
import urllib.request

ROOT = Path("D:/project/cluster_project")
P = ROOT / "pipeline"
OUT = P / "reports/binding_scope_20260911-1012"

# These are authored text readings, not independent annotation or scene truth.
READINGS = [
    ("scene0578_00", "5", "36", "error", ["around the table", "on the right side", "in the front"],
     ["table"], "scope_ambiguous", "Only around explicitly names table; right/front reference frame and attachment unspecified."),
    ("scene0208_00", "0", "20", "error", ["on the right wall", "another bookshelf", "perpendicular to it"],
     ["wall", "bookshelf"], "different_referents", "Wall extent and another bookshelf are distinct mentions; it attachment needs adjudication."),
    ("scene0328_00", "24", "52", "error", ["right of the stove", "dark brown rectangular prism"],
     ["stove"], "single_relation", "One explicit target-anchor predicate; appearance is unary, not a second table/stove relation."),
    ("scene0621_00", "2", "85", "error", ["in the middle", "square"],
     [], "unary_or_scene_relative", "Middle lacks specified comparison domain; square is unary shape."),
    ("scene0334_00", "5", "23", "error", ["donut shaped brown", "next to a couch"],
     ["couch"], "single_relation", "One explicit relation plus unary shape/color; two couch candidates not resolved by noun."),
    ("scene0621_00", "22", "68", "error", ["with wheels", "at the table closest to the open door"],
     ["table", "door"], "nested_chain", "At(chair,table) and closest(table,door) share an intermediate table, not two factors of the same target-anchor pair."),
    ("scene0146_00", "16", "8", "error", ["rectangular toilet paper dispenser", "to the left of the toilet"],
     ["toilet"], "single_relation", "Toilet in target noun is not an extra anchor mention; one left predicate."),
    ("scene0249_00", "23", "41", "error", ["blue and white recycling trash can", "next to a brown box", "in front of the entry way"],
     ["box", "entry way"], "different_referents_attachment_ambiguous", "Front may modify box or target; box and entry way are distinct mentions either way."),
    ("scene0046_00", "26", "27", "error", ["open white entry door", "in front of the toliet"],
     ["toliet"], "single_relation", "Preserve misspelling; no silent mapping to toilet; viewpoint missing."),
    ("scene0426_00", "22", "24", "error", ["large brown pillow", "on the bed", "behind the pile of blankets"],
     ["bed", "pile of blankets"], "different_referents_attachment_ambiguous", "Behind may modify bed or pillow; no same-anchor conjunction established."),
    ("scene0591_00", "14", "22", "error", ["pillow is orange", "on the black couch"],
     ["couch"], "single_relation", "One anchor relation plus color; do not assume on(couch) distinguishes the two pillows."),
    ("scene0652_00", "6", "33", "error", ["wooden filing cabinet", "taller of the two"],
     [], "comparison_domain_missing", "The second comparison object is not named; cabinet/dresser ontology cannot be merged silently."),
    ("scene0578_00", "11", "38", "control", ["in the middle of the room", "brown"],
     ["room"], "unary_or_scene_relative", "Room is a scene domain, not necessarily an annotated object."),
    ("scene0328_00", "17", "12", "control", ["above the oven", "two cabinets to the right and left", "in between"],
     ["oven", "cabinets"], "distinct_plural_anchors", "Two cabinet instances are distinct by explicit cardinality; between is higher arity."),
    ("scene0334_00", "7", "16", "control", ["to the left of another brown bench"],
     ["bench"], "single_relation", "Another bench explicitly excludes the target, without asserting its physical ID."),
    ("scene0146_00", "12", "19", "control", ["wall soap dispenser", "right of the sink"],
     ["sink"], "single_relation", "One explicit right relation; wall in noun context not automatically another predicate."),
    ("scene0249_00", "24", "52", "control", ["long table", "in the center of the room"],
     ["room"], "unary_or_scene_relative", "Long is unary; center domain/frame remains unspecified."),
    ("scene0046_00", "26", "34", "control", ["bathroom door", "it's open", "white"],
     [], "unary_or_scene_relative", "Open/color/type are unary; no explicit binary target-anchor relation."),
    ("scene0426_00", "24", "15", "control", ["against the wall", "under the window"],
     ["wall", "window"], "different_referents", "Two predicates use different object mentions, not one shared witness."),
    ("scene0591_00", "25", "30", "control", ["behind a desk with monitors"],
     ["desk", "monitors"], "nested_chain", "Behind(window,desk) plus with(desk,monitors); no same-pair conjunction established."),
    ("scene0652_00", "25", "11", "control", ["wall mounted television set", "above the black dresser"],
     ["dresser"], "single_relation", "One explicit above relation; wall-mounted is not a second dresser relation."),
]


def sha(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(4 * 1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def normalized(text):
    return re.findall(r"[a-z0-9]+", text.lower().replace("_", " "))


def logmix(energies, mass):
    if not energies or len(energies) != len(mass):
        raise ValueError("nonempty matching domain required")
    if any(p < 0 or not math.isfinite(p) for p in mass) or abs(sum(mass) - 1) > 1e-12:
        raise ValueError("probability mass required")
    if not all(math.isfinite(v) for v in energies):
        raise ValueError("finite energies required")
    vals = [e + math.log(p) for e, p in zip(energies, mass) if p > 0]
    peak = max(vals)
    return peak + math.log(sum(math.exp(v - peak) for v in vals))


def witness(ell, mass):
    assert ell and all(len(row) == len(mass) for row in ell)
    total = [sum(row[a] for row in ell) for a in range(len(mass))]
    return dict(U=sum(max(row) for row in ell), C=max(total),
                J=logmix(total, mass), independent_soft=sum(logmix(row, mass) for row in ell))


def tests():
    output = []
    def record(name, value):
        output.append(dict(name=name, result="passed", evidence=value))
    wrong, right = [[0., -4.], [-4., 0.]], [[-1., -3.], [-1., -3.]]
    a, b = witness(wrong, [.5, .5]), witness(right, [.5, .5])
    assert a["U"] > b["U"] and a["C"] < b["C"]
    record("hard_ranking_counterexample", dict(wrong=a, right=b))
    for ell in (wrong, right, [[1., 2.]], [[2., 2.], [1., 1.]]):
        v = witness(ell, [.5, .5])
        assert v["C"] <= v["U"]
    record("hard_upper_bound", 4)
    r1 = witness([[1., 2.]], [.5, .5])
    assert r1["C"] == r1["U"] and r1["J"] == r1["independent_soft"]
    record("single_predicate_degeneracy", r1)
    positive = a["independent_soft"] - a["J"]
    negative = b["independent_soft"] - b["J"]
    assert positive > 0 and negative < 0
    record("soft_gap_has_no_fixed_sign", dict(positive=positive, negative=negative))
    energies, mass = [2., -1.], [.4, .6]
    expected = logmix(energies, mass)
    subdivided = logmix([2., 2., -1.], [.1, .3, .6])
    assert abs(expected - subdivided) < 1e-12
    record("mass_conserving_duplicate", dict(original=expected, duplicate=subdivided))
    uniform = logmix([2., 2., -1.], [1/3, 1/3, 1/3])
    assert abs(uniform - expected) > .01
    record("unweighted_duplicate_not_invariant", uniform)
    assert abs(logmix([-1., 2.], [.6, .4]) - expected) < 1e-12
    record("joint_permutation", expected)
    posterior = [p * math.exp(e - expected) for e, p in zip(energies, mass)]
    variational = sum(q * e - q * math.log(q / p) for q, e, p in zip(posterior, energies, mass))
    assert abs(variational - expected) < 1e-12
    record("variational_optimum", dict(posterior=posterior, objective=variational))
    step = 1e-5
    numeric = []
    for i in range(2):
        plus, minus = energies[:], energies[:]
        plus[i] += step
        minus[i] -= step
        grad = (logmix(plus, mass) - logmix(minus, mass)) / (2 * step)
        assert abs(grad - posterior[i]) < 1e-8
        numeric.append(grad)
    record("finite_difference_energy_gradient", numeric)
    assert logmix([2., 1000.], [1., 0.]) == 2.
    record("zero_mass_mask", 2.)
    bad = 0
    for e, m in (([], []), ([1.], [0.]), ([1., 2.], [-1., 2.]), ([float("nan")], [1.])):
        try:
            logmix(e, m)
        except ValueError:
            bad += 1
    assert bad == 4
    record("invalid_domain_rejected", bad)
    # Separate named anchors legitimately attain the relaxed optimum.
    assert a["U"] == 0 and a["C"] == -4
    record("separate_anchor_negative_control", "Do not enforce one identity across distinct mentions.")
    assert abs(logmix([1002., 999.], mass) - 1000 - expected) < 1e-12
    record("stable_logsumexp_shift", expected)
    return output


def prepare():
    assert not OUT.exists()
    OUT.mkdir()
    goal = json.loads((P / "goal.json").read_text(encoding="utf-8"))
    protocol = dict(created=datetime.now().isoformat(), design_id="20260911-101200",
                    scope="Text-only applicability notes authored with prior outcomes already known; not blinded/independent annotations or scene-grounded causal labels.",
                    rules="Require at least two explicit target-to-anchor predicates with the same coreferent anchor to confirm narrow shared-witness eligibility. Nested chains, distinct/plural anchors, unary attributes do not qualify automatically. Ambiguous attachment/frame stays unknown. No object synonym or typo correction.",
                    upstream_sha256=sha(P / "reports/d1_identity_20260911-0912/identity_geometry.json"),
                    readings=READINGS, training_admission=False)
    (OUT / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
    review = f"""# Motivation Review - cluster_project
{protocol['created']} Asia/Shanghai
## 1. Goal
```json
{json.dumps(goal, ensure_ascii=False, indent=2)}
```
Checker10:08:41 Phase1NOTYET;M95.5020/baseline.4894/target.5100.
## 2. Story Status
| Hypothesis | Status | Evidence | Gap |
|---|---|---|---|
| Candidate selection headroom | measured | baseline90/M95111 of284 | Cause not known |
| Same-name wrong instance | verified cases |9of12fixed M95errors | Attribute/relation discriminability |
| Shared-anchor inconsistency | unverified | provisional memo only | Applicability,prior art,forward |
## 3. Experiment Assessment
| Experiment | mIoU | Motivation | Contribution |
|---|---|---|---|
| Baseline/M95 historical | .489449/.502461 exact | Reference | No freshfullreplay |
| M183/M186 | .491549/.494500 | Legacy controls | No championgain |
| D1 sample baseline/M95 | .535914/.502217 | Diagnosis | Notpopulation efficacy |
223 historical analyses reconciled by immutable inventory. No new terminal.
## 4. Gap Analysis
Repeated overlap audit cannot establish anchor binding. Need sentence-scope
applicability, counterexamples and closest primary operator comparisons.
## 5. Design Rationale
Q1:Does narrow shared-witness structure match fixed cases? Q2:boundedtextaudit,
hard/soft finite-energy tests and two primary method audits. Q3:reject unjustified
mechanism admission, identify exact missing assumptions. All12constraints/11bans
retained. Diagnostic/formal tests are not independent model novelty.
Sixareas:diagnosis+formal/noveltylimits now; matchedsynthetic controls now;
realmechanism,robustness andfullmodel efficiency remain pending.
## 6. Next Batch
exp_design_20260911-101200.md; no modeltraining/refill.
"""
    (P / "reviews/motivation_review_20260911-101200.md").write_text(review, encoding="utf-8")
    design = f"""# Experiment Design - cluster_project
{protocol['created']} Asia/Shanghai
## 1. Motivation
Verbatim goal.description: {goal['description']}
Waiting4/capacity4 triggers review; scientific admission overrides refill.
## 2. Current Best Results
| ID | Config | State | mIoU | Acc50 | spmIOU | Epochs |
|---|---|---|---|---|---|---|
| Baseline | audited model_base1 | historical | .489449 | .541 | .451 |best15|
| M95 | csort | historical | .502461 | .557 | .465 |best16|
| M186 | mqht_tr | done_earlystop | .494500 | .548 | .459 |27|
## 3. Analysis & Direction
Effective:baseline/context historical andbank diagnostics. Failed:explicitrouting,
legacyreadout gains inadequate. Unverified:shared-anchor cause/novelty.
{protocol['rules']}
HardU=sum max ell, C=max sum ell. TestC<=U,onepredicate degeneration,ranking
counterexample. SoftJ=log sum pi exp(sum ell). Testvariational optimum,gradients,
massconservation,zero-mass andinvaliddomains; independent soft sum has no assumed
order against J. Different referents are a negative control,not forced equal.
Primarysources:arXiv2303.13483v1 NS3D section3.3 and2411.14594v2 CSVG section3.
This is a bounded prior-art audit,not a systematic/full novelty clearance.
## 4. Experiment Plan
| # | ID | Input | Purpose | Expected Result | Priority | Depends On |
|---|---|---|---|---|---|---|
|1|D1-SCOPE|21existing descriptions|sentence applicability andmissingframes|explicitunknowns|P0|identity audit|
|2|T0-WITNESS|synthetic finite energies|verify hard/soft distinction|counterexamples/tests|P0|memo|
|3|N1-PRIOR|two primarypapers|novelty overlap boundaries|no broad noveltyclaim|P0|scope|
## 5. GPU Allocation Plan
| Server | GPU | Assignment | Config | Justification |
|---|---|---|---|---|
|server-4|0/1|M188/M187 preserved|existing|localCPU only|
|server-6|7|M184/M185 preserved|existing|capacity2 occupied|
No new data/inference/annotationAPI/LLM calls. Download primarypapers only.
## 6. Implementation Checklist
- [x] Fullgoalreview then design/protocol.
- [ ] Verify21source spans/IDs; persist ambiguity andmissinglexical anchors.
- [ ] Run13synthetic propertytests; record operator derivation/limitations.
- [ ] Archive primarypaper versions/hash andbounded claims.
- [ ] Hashsync standalonehelper/documents tobothservers,not active packages.
- [ ] Final livecheck,report,memory.
Trainingpackage/config/commit/enqueue N/A; no mechanism admitted.
## 7. Risk Assessment
Text readings unblinded,not humanagreement/scene truth. Fixedoutcome-selected
sample cannot estimate failureprevalence. Exactlabelmatching has explicitfalse
negatives; neverinferwrong anchor from lexicalmissingness. Algebra not novelty.
Two sources not exhaustive; no baselineneural incapacity claim. Training costs
and feasibility unmeasured;existing10G/seed/schedule bans unchanged.
<=3 helperrepairs;preserve failures;no trainingrerun. Smellcheck N/A diagnostic.
Status:APPROVED diagnostic/formal audit only.
"""
    (P / "designs/exp_design_20260911-101200.md").write_text(design, encoding="utf-8")


def main():
    prepare()
    data = json.loads((P / "reports/d1_identity_20260911-0912/identity_geometry.json").read_text(encoding="utf-8"))
    index = {(r["scene_id"], str(r["object_id"]), str(r["ann_id"])): r for r in data["rows"] if r["model"] == "m95"}
    assert len(index) == len(READINGS) == 21
    rows = []
    for scene, oid, ann, role, spans, anchors, scope, note in READINGS:
        r = index[(scene, oid, ann)]
        assert all(span in r["description"] for span in spans), (scene, ann, spans)
        objects = data["scenes"][scene]["objects"]
        matches = {anchor: [i for i, obj in objects.items()
                            if normalized(obj["label"]) == normalized(anchor) and i != oid]
                   for anchor in anchors}
        rows.append(dict(scene_id=scene, object_id=oid, ann_id=ann, role=role,
                         description=r["description"], spans=spans, anchor_mentions=matches,
                         no_exact_lexical_match=[k for k, v in matches.items() if not v],
                         scope=scope, note=note, same_pair_shared_witness_confirmed=False,
                         physical_relation_truth="unknown", cause="unknown"))
    results = tests()
    (OUT / "scope_audit.json").write_text(json.dumps(dict(rows=rows, source_sha256=sha(
        P / "reports/d1_identity_20260911-0912/identity_geometry.json")), indent=2), encoding="utf-8")
    (OUT / "formal_tests.json").write_text(json.dumps(dict(status="passed", tests=results), indent=2), encoding="utf-8")
    from bs4 import BeautifulSoup
    sources = []
    for name, url in (("NS3D", "https://arxiv.org/html/2303.13483v1"),
                      ("CSVG", "https://arxiv.org/html/2411.14594v2")):
        payload = urllib.request.urlopen(url, timeout=30).read()
        path = OUT / (name + ".html")
        path.write_bytes(payload)
        soup = BeautifulSoup(payload, "html.parser")
        sources.append(dict(name=name, url=url, title=soup.title.get_text(),
                            sha256=sha(path), fetched=datetime.now().isoformat(),
                            sections_reviewed="3.3; CSVG additionally3.1/3.2",
                            status="primary_fulltext_retrieved"))
    (OUT / "sources.json").write_text(json.dumps(sources, indent=2), encoding="utf-8")
    print(json.dumps(dict(rows=len(rows), errors=sum(r["role"] == "error" for r in rows),
                         confirmed=0, scope_counts=dict(Counter(r["scope"] for r in rows)),
                         tests=len(results), sources=sources), indent=2))


if __name__ == "__main__":
    main()
