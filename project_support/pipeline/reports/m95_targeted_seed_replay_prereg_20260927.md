# M95 targeted native seed replay preregistration

Continue `m95-sample-context-support`. Before new outcomes, choose frozen
manifest rows 0 (`scene0588_00`, ann 15, dataset index 8096, previously
exposed ambiguous failure) and 1 (`scene0646_00`, ann 4, dataset index 8815,
previously non-exposed ambiguous control). Build the original native TRAIN
dataset and select those two indices without changing model/checkpoint/loss.
Run seed 1999 and record actual scene/annotation identities, final focal
targets, matched/top-k seed sets, same-forward sample-logit and sampling
parameter gradients under baseline and count/logit-matched label placebo.
The fresh transformations will differ from the 256-row full-order capture;
do not assert exact-input replication or accept a mechanism from this
outcome-selected pair. A native-prediction-blind population capture and a
genuinely class/instance-matched negative control remain necessary for
diagnosis and controls gates.
