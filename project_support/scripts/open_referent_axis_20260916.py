"""Apply the user's scope decision B: open the referent-supervision axis in goal.json.

Minimal, append-only edit: adds ONE constraint recording the authorisation and the
evidence that removed the old exclusion basis. Does not touch the 11 banned[] entries
or any other constraint. Writes valid JSON and verifies round-trip.
"""
import json
from pathlib import Path

GOAL = Path("D:/project/cluster_project/pipeline/goal.json")

NEW_CONSTRAINT = (
    "[USER-SCOPE-B 2026-09-16] Open the referent-supervision axis. "
    "Supervision-level structural changes for the referent decision "
    "(new loss / new positive-set definition / new supervision unit) are "
    "re-admissible as the project's primary direction. "
    "Basis: the two 2026-09-13 route_change decisions (20260913-061110 and "
    "20260913-071026) excluded supervision repair and relabeling on the stated "
    "ground 'descriptive association is not causal evidence' while declaring "
    "scientific admission incomplete. That ground was removed on 2026-09-16 by a "
    "causal intervention on the fixed M95 checkpoint in one same-forward capture "
    "that changed only the selection rule: restricting selection to the native "
    "training-positive set gives +17.9pp scene-balanced (87.0 vs 69.1, 95% CI "
    "[+10.9,+25.8], 22 fixed / 0 broken), while the objectness-only control "
    "(seed inside ANY instance) is exactly null. "
    "All other constraints and every banned[] entry stay in force unchanged: "
    "Phase1 no-tuning, FLOPs<=10G, peak memory, validation boundaries, scene-level "
    "uncertainty, pre-defined rejection criteria, and the full "
    "motivation_review -> exp_design -> smell-check -> independent model/config -> "
    "native backward -> resources -> independence -> admission receipt -> safe sync "
    "chain. RefMask3D, DETR and other existing work must not be presented as this "
    "project's contribution: exp_design must state the whole-mechanism difference "
    "against the verified originals and the increment over generic mask-aware "
    "matching."
)


def main():
    data = json.loads(GOAL.read_text(encoding="utf-8"))
    before_c = len(data["constraints"])
    before_b = len(data["banned"])
    if any("USER-SCOPE-B" in c for c in data["constraints"]):
        print("already present; no change")
        return
    data["constraints"].append(NEW_CONSTRAINT)
    GOAL.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n",
                    encoding="utf-8")
    check = json.loads(GOAL.read_text(encoding="utf-8"))
    print(json.dumps({
        "constraints_before": before_c,
        "constraints_after": len(check["constraints"]),
        "banned_before": before_b,
        "banned_after": len(check["banned"]),
        "banned_unchanged": before_b == len(check["banned"]),
        "last_constraint_prefix": check["constraints"][-1][:60],
        "append_only": check["constraints"][:before_c] == data["constraints"][:before_c],
    }, indent=2))


if __name__ == "__main__":
    main()
