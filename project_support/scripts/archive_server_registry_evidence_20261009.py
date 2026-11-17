"""Repair historical citations only after reproducing their exact bound bytes."""
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, "C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
import foreground_tick


def main():
    owner = foreground_tick.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == "e3d3340fabdd45bb9fc636e57be24156"
    assert owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    expected = "4da92203f8e9600ef1264b85d6509a524c7be9f373c44d3d40747615f651eedc"
    current = (ROOT / "SERVERS.yaml").read_bytes()
    historical = current.replace(b"192.168.1.115", b"192.168.1.137")
    assert hashlib.sha256(historical).hexdigest() == expected
    archive = "pipeline/reports/SERVERS_historical_4da92203_20261009.yaml"
    with (ROOT / archive).open("xb") as stream:
        stream.write(historical)
    work = foreground_tick.load(ROOT / "pipeline/research_work.json")
    changed = []
    for candidate in work["candidates"]:
        for entry in candidate["evidence"]:
            if entry["path"] == "SERVERS.yaml" and entry["sha256"] == expected:
                assert candidate["stage"] == "rejected"
                entry.update(path=archive, original_path="SERVERS.yaml",
                             archive_reason="User changed server4 IP; preserve exact historical evidence, not current authorization")
                changed.append(candidate["id"])
    assert len(changed) == 8
    foreground_tick.save(ROOT / "pipeline/research_work.json", work)
    record = {
        "timestamp": datetime.now().astimezone().isoformat(),
        "historical_path": archive, "historical_sha256": expected,
        "current_path": "SERVERS.yaml",
        "current_sha256": hashlib.sha256(current).hexdigest(),
        "verification": "Inverse of the documented .137 to .115 address edit reproduces exact original bound SHA256.",
        "preserved_scientific_stages_and_conclusions": True,
        "changed_citations_only": changed, "current_registry_modified": False,
        "historical_registry_is_current_authorization": False,
        "connections_to_server4": False}
    with (ROOT / "pipeline/reports/server_registry_citation_repair_20261009.json").open(
            "x", encoding="utf-8") as stream:
        json.dump(record, stream, indent=2)
    print(json.dumps(record))


if __name__ == "__main__":
    main()
