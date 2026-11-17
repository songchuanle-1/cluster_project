"""Prediction-blind source-level support vectors for the frozen native cohort."""
import math


def physical_support(superpoints, instances, classes, target_ids, context_classes,
                     curtain_ids, original, shower_curtain_class=13):
    """Reconstruct native support, then add only physical non-target phrase support.

    Classes are the original dataset's nyu40id2class outputs on the *transformed*
    point order. This runs at the dataset boundary, before collate drops labels.
    """
    n = len(superpoints)
    if not (n == len(instances) == len(classes)) or not n:
        raise ValueError("Transformed point axes differ")
    count = {}
    base = {}
    treated = {}
    by_sp_instance = {}
    instance_classes = {}
    target_ids = set(target_ids)
    curtain_ids = set(curtain_ids)
    context_classes = set(context_classes)
    if target_ids & curtain_ids or not target_ids or not curtain_ids:
        raise ValueError("Target and physical non-target curtain identities differ")
    actual_curtain = set()
    for sp, instance, cls in zip(superpoints, instances, classes):
        if not isinstance(sp, int) or sp < 0:
            raise ValueError("Invalid superpoint index")
        sp = int(sp)
        count[sp] = count.get(sp, 0) + 1
        by_sp_instance.setdefault(sp, set()).add(instance)
        if instance in instance_classes and instance_classes[instance] != cls:
            raise ValueError("Instance class differs across points")
        instance_classes[instance] = cls
        if instance in curtain_ids:
            if cls != shower_curtain_class:
                raise ValueError("Curtain physical class differs")
            actual_curtain.add(instance)
        value = 1.0 if instance in target_ids else 0.5 if cls in context_classes else 0.0
        base[sp] = base.get(sp, 0.0) + value
        treated[sp] = treated.get(sp, 0.0) + (
            0.5 if instance in curtain_ids and value == 0 else value)
    if actual_curtain != curtain_ids or sorted(count) != list(range(len(count))):
        raise ValueError("Curtain cropped or noncontiguous superpoints")
    if len(original) != len(count):
        raise ValueError("Native sp_ref_mask length differs")
    baseline = [base[i] / count[i] for i in range(len(count))]
    intervention = [treated[i] / count[i] for i in range(len(count))]
    if any(not math.isfinite(float(v)) or abs(float(v) - baseline[i]) > 1e-5
           for i, v in enumerate(original)):
        raise ValueError("Native support differs from source reconstruction")
    changed = [i for i in range(len(count))
               if intervention[i] - baseline[i] > 1e-6]
    if not changed:
        raise ValueError("No physical phrase support changed")
    # Superpoints with mixed identities remain eligible for treatment but
    # require final-FPS parity before constructing a matched placebo.
    placebo_pool = [
        i for i in range(len(count))
        if baseline[i] == 0 and not (by_sp_instance[i] & (target_ids | curtain_ids))
    ]
    return {
        "baseline": baseline,
        "treated": intervention,
        "changed_superpoints": changed,
        "placebo_pool": placebo_pool,
        "mixed_changed": [i for i in changed if len(by_sp_instance[i]) > 1],
    }
