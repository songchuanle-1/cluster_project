"""CPU-only invariants for the preregistered same-forward support replay.

This module does not construct an intervention or claim a native observation.
"""
import math


def check_final_targets(baseline, treated, placebo, protected, eligible_treat,
                        eligible_placebo, *, tolerance=1e-6):
    """Validate three aligned final focal-target vectors after native matching."""
    if not (len(baseline) == len(treated) == len(placebo)):
        raise ValueError("Final target axes differ")
    size = len(baseline)
    protected = set(protected)
    treat = set(eligible_treat)
    control = set(eligible_placebo)
    for indices in (protected, treat, control):
        if any(not isinstance(i, int) or i < 0 or i >= size for i in indices):
            raise ValueError("Out-of-range or non-integer seed index")
    if protected & (treat | control) or treat & control:
        raise ValueError("Protected or intervention seed overlap")
    if any(not math.isfinite(float(v)) or not 0 <= float(v) <= 1
           for arm in (baseline, treated, placebo) for v in arm):
        raise ValueError("Nonfinite or out-of-range final focal target")
    changed_treat = {i for i, (a, b) in enumerate(zip(baseline, treated))
                     if abs(float(a) - float(b)) > tolerance}
    changed_placebo = {i for i, (a, b) in enumerate(zip(baseline, placebo))
                       if abs(float(a) - float(b)) > tolerance}
    if not changed_treat or not changed_placebo:
        raise ValueError("No final focal-target intervention")
    if protected & (changed_treat | changed_placebo):
        raise ValueError("Protected final seed target changed")
    if changed_treat != treat or changed_placebo != control:
        raise ValueError("Unexpected final target change or overwritten intended seed")
    if len(treat) != len(control):
        raise ValueError("Final seed change counts differ")
    treat_delta = sorted(float(treated[i]) - float(baseline[i]) for i in treat)
    placebo_delta = sorted(float(placebo[i]) - float(baseline[i]) for i in control)
    if any(abs(a - b) > tolerance for a, b in zip(treat_delta, placebo_delta)):
        raise ValueError("Final seed target magnitudes differ")
    return {"treated_final_seed_count": len(treat),
            "placebo_final_seed_count": len(control),
            "final_target_delta": treat_delta}


def check_non_sample_losses(baseline, treated, placebo, *, tolerance=1e-6):
    """Other criterion components must be unchanged in the same forward."""
    keys = set(baseline)
    if set(treated) != keys or set(placebo) != keys or "sample_loss" not in keys:
        raise ValueError("Criterion component keys differ")
    for key in keys - {"sample_loss"}:
        values = [float(arm[key]) for arm in (baseline, treated, placebo)]
        if any(not math.isfinite(v) for v in values):
            raise ValueError("Nonfinite non-sample loss")
        if max(values) - min(values) > tolerance:
            raise ValueError("Non-sample loss changed: " + key)
    return True
