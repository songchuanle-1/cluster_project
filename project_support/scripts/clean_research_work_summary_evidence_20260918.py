import json
from pathlib import Path


WORK = Path(
    r"D:/project/cluster_project/pipeline/research_work.json"
)
document = json.loads(WORK.read_text(encoding="utf-8"))
removed = []
for candidate in document["candidates"]:
    kept = []
    for evidence in candidate.get("evidence", []):
        name = Path(evidence["path"]).name
        if name.startswith("summary_") and name.endswith(".md"):
            removed.append({
                "id": candidate["id"],
                "path": evidence["path"],
                "sha256": evidence["sha256"],
            })
        else:
            kept.append(evidence)
    if not kept:
        raise ValueError("Candidate would lose all evidence: " + candidate["id"])
    candidate["evidence"] = kept

WORK.write_text(json.dumps(document, indent=2) + "\n", encoding="utf-8")
loaded = json.loads(WORK.read_text(encoding="utf-8"))
if any(
    Path(evidence["path"]).name.startswith("summary_")
    for candidate in loaded["candidates"]
    for evidence in candidate["evidence"]
):
    raise ValueError("Summary evidence remains after cleanup")
print(json.dumps({"removed": removed}, indent=2))
