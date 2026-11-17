"""Apply the user's 2026-09-16 allocation change: server-6 GPU7 only, 2 slots.

Append-only goal.json edit (one new constraint). SERVERS.yaml is edited separately.
The running M197-PIRS on server6 GPU7 is not touched.
"""
import json
from pathlib import Path

GOAL = Path("D:/project/cluster_project/pipeline/goal.json")

NEW_CONSTRAINT = (
    "[USER-ALLOCATION 2026-09-16] The project's training and native-diagnostic "
    "allocation is now server-6 GPU7 ONLY, with 2 task slots (SERVERS.yaml "
    "allowed_gpus [7], max_tasks_per_gpu 2), so the design capacity is 2 rather "
    "than 4. server-4 GPU0/GPU1 are removed from this project's whitelist "
    "(allowed_gpus []); its current foreign jobs were never touched and are no "
    "longer treated as project capacity. Every other constraint is unchanged: "
    "the operating-location rule of 2026-09-15 is superseded only for the host "
    "list, and all science, resource, schedule, validation, banned and closure "
    "requirements still apply. Local remains orchestration/edit/static only."
)


def main():
    data = json.loads(GOAL.read_text(encoding="utf-8"))
    before_c, before_b = len(data["constraints"]), len(data["banned"])
    if any("USER-ALLOCATION 2026-09-16" in c for c in data["constraints"]):
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
        "append_only": check["constraints"][:before_c] == data["constraints"][:before_c],
    }, indent=2))


if __name__ == "__main__":
    main()
