"""Explicit, prospective experiment-first policy; never a resource permission."""
import math
from datetime import datetime
from pathlib import Path


SCOPE = "project_experiment_workflow"
GATES = ("native_backward", "resources", "independence", "constraints")


def validate_policy(root, policy):
    import closure

    if not policy or policy.get("enabled") is not True:
        return {}
    grant = closure.read(closure.artifact(root, policy["authorization"]), {})
    if (grant.get("scope") != SCOPE or grant.get("project") != Path(root).name
            or grant.get("authorization_granted") is not True
            or not grant.get("source_thread_id") or not grant.get("human_reply")
            or grant.get("resource_expansion") is not False):
        raise ValueError("Experiment-first policy lacks scoped human authorization")
    defaults = {"waiting_target": 2, "actionable_limit": 4, "max_new_candidates": 2}
    result = {"enabled": True, "authorization": policy["authorization"]}
    for key, default in defaults.items():
        value = policy.get(key, default)
        if not isinstance(value, int) or isinstance(value, bool) or value < 0:
            raise ValueError("Invalid experiment-first bound: " + key)
        result[key] = value
    return result


def effective(root):
    import closure

    context = closure.bound_foreground_context(root)
    # A running tick without this field remains legacy even after opt-in.
    if context is not None:
        return validate_policy(root, context.get("experiment_first", {}))
    policy = closure.read(Path(root) / "pipeline/closure_policy.json", {})
    if policy.get("enabled") is not True:
        return {}
    return validate_policy(root, policy.get("experiment_first", {}))


def validate_smoke(root, receipt):
    """Validate recorded native observations, not predicted research efficacy."""
    import closure

    smoke = closure.read(closure.artifact(root, receipt["native_smoke"]), {})
    if Path(str(receipt.get("config", ""))).suffix.lower() not in (".yaml", ".yml"):
        raise ValueError("Experiment-first tasks must retain the native YAML config")
    for field in ("id", "config", "code_commit", "goal_sha256"):
        if not smoke.get(field) or smoke[field] != receipt.get(field):
            raise ValueError("Native smoke identity mismatch: " + field)
    steps = smoke.get("steps")
    losses = smoke.get("losses")
    if (not isinstance(steps, int) or isinstance(steps, bool) or steps < 2
            or not isinstance(losses, list) or len(losses) < 2
            or any(isinstance(x, bool) or not isinstance(x, (int, float))
                   or not math.isfinite(x) for x in losses)
            or smoke.get("native_data_loaded") is not True
            or smoke.get("backward_finite") is not True
            or smoke.get("intended_path_observed") is not True
            or smoke.get("split") != "train"
            or not all(smoke.get(k) for k in ("command", "data_source", "evidence"))):
        raise ValueError("Native smoke lacks real data, finite backward or exercised path")
    for entry in smoke["evidence"]:
        closure.artifact(root, entry)


def validate_outcome(root, context, candidates, queue):
    """One evidenced bounded attempt can finish; untouched backlog may carry over."""
    import closure

    policy = validate_policy(root, context["experiment_first"])
    known = context.get("research_work", {}).get("progress_baselines", {})
    created = [c for c in candidates if c["id"] not in known]
    budget = context.get("research_work", {}).get("creation_budget", 0)
    if len(created) > min(budget, policy["max_new_candidates"]):
        raise ValueError("Experiment-first candidate creation budget exceeded")
    if context["mode"] != "design":
        return
    delta = closure.tick_admission_delta(root, context, queue)
    # Admission validity and archived launch proof were already checked by postflight.
    if delta and (any(t.get("status") in ("waiting", "claiming", "running",
                                         "done_complete", "done_earlystop")
                     for _, t in delta[1].values())
                  or any(closure.read(p, {}).get("status") in
                         ("done_complete", "done_earlystop")
                         for p in closure.new_tick_experiments(root, context).values())):
        return
    work = closure.read(Path(root) / "pipeline/research_work.json", {})
    attempt = work.get("tick_attempt", {})
    changed = closure.changed_candidate_ids(context, candidates)
    if (attempt.get("tick_started_at") != context["generated_at"]
            or attempt.get("candidate_id") not in changed
            or attempt.get("kind") not in ("native_smoke", "implementation_test", "resource_check")
            or attempt.get("result") not in ("passed", "failed", "blocked")
            or not all(attempt.get(k) for k in ("command", "observation", "evidence"))):
        raise ValueError("Experiment-first design needs an admission or a real current test")
    since = datetime.fromisoformat(context["generated_at"]).timestamp()
    candidate = next(c for c in candidates if c["id"] == attempt["candidate_id"])
    for entry in attempt["evidence"]:
        if entry not in candidate.get("evidence", []):
            raise ValueError("Current test evidence is not bound to its candidate")
        if closure.artifact(root, entry).stat().st_mtime < since:
            raise ValueError("Current test cannot reuse old results")
