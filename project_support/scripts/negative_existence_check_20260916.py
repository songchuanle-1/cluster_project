"""Static distinction between normalized anchor attention and existence."""
import hashlib
import json
import math
from pathlib import Path


def softmax(values):
    weights = [math.exp(v-max(values)) for v in values]
    return [w/sum(weights) for w in weights]


def sigmoid(value):
    return 1/(1+math.exp(-value))


low, high = [-10., -10.], [10., 10.]
assert softmax(low) == softmax(high) == [.5, .5]
relation = [1., 1.]
normalized_scores = [sum(a*r for a,r in zip(softmax(z), relation)) for z in (low, high)]
absence_scores = [math.prod(1-sigmoid(v)*r for v,r in zip(z,relation)) for z in (low,high)]
assert normalized_scores == [1., 1.]
assert absence_scores[0] > .999 and absence_scores[1] < 1e-8
# Products over points falsely count duplicate samples as independent witnesses.
p = .2
duplicates = [(1-p)**count for count in (1,2,10)]
assert duplicates[0] != duplicates[-1]
# Uniform learned presence=0 makes every negative-only observation satisfied.
assert math.prod(1-0*r for r in relation) == 1
# Relative reversal loses absolute existence information.
flat = softmax([0., 0., 0.])
reversed_flat = [max(flat)-x for x in flat]
assert reversed_flat == [0., 0., 0.]
result = dict(
    normalized_anchor_scores=normalized_scores,
    independent_presence_absence=absence_scores,
    duplicate_witness_absence=duplicates,
    flat_relative_reversal=reversed_flat,
    conclusion="Normalized anchor mass cannot distinguish absent from ubiquitous anchors. "
    "Independent presence can, but needs calibration/positive evidence and distinct "
    "witness support; negative-only allzero and duplicate-point shortcuts remain.",
    limitations="Synthetic countermodels only. Sigmoid/noisy-OR are standard operators, "
    "not novel contributions or evidence of native calibrated presence. No new labels, "
    "model implementation or training admission.",
    sources={str(Path(__file__)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
)
out=Path(__file__).resolve().parents[1]/"pipeline/reports/negative_existence_check_20260916.json"
out.write_text(json.dumps(result,indent=2),encoding="utf-8")
print(json.dumps(result,indent=2))
