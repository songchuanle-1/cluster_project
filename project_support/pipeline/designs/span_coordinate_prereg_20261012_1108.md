# Native Caption Character-Coordinate Diagnosis

Tick:63db8202cf55406f8f29e19f14229f70.
Stable ID:m95-native-caption-span-coordinate-shift.
Hypothesis ID: caption-normalization-displaces-supervision-character-spans.

The native dataset normalizes graph utterance using comma spacing and whitespace
split/join, then converts unchanged graph character spans into token maps.
If this operation changes actual strings before a supervised span, native
supervision coordinates may refer to different tokens. This is not token-length
truncation, padding participation or choosing a different parsed root.

Prediction-blind first test: compare graph utterance with exact native
normalization for every unchanged TRAIN annotation, binding graphs/annotations.
Keep missing graphs separate. Count actual changed strings and freeze32/128
separately. If real strings differ, align character coordinates and evaluate
exact native maps before inferring supervision harm.
If every native string is already canonical, reject this coordinate-displacement
premise for the unchanged graphs, not arbitrary preprocessing/parse errors.

Sensitivity control uses constructed multi-comma input with original stale
versus canonical target coordinates and the native RoBERTa/get_positive_map.
An already canonical input must have identical spans/maps; a wrong-phrase
control must differ. Constructed input is only a control, not native prevalence.
For frozen128, invoke original native full role-map getter and a canonicalized
utterance clone; report map equality under identical strings, not full model
forward/backward or trained efficacy.
No original source, data, span, label, schedule, threshold or model mutation.
