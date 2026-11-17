"""Retarget one evidence citation to its already preserved identical bytes."""
from datetime import datetime
import hashlib
import os
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
SKILL = Path("C:/Users/chuanle song/.codex/skills/songcl_research_pipeline")
sys.path.insert(0, str(SKILL))
import foreground_tick as fg

TOKEN = "b395a8b5064a4b6a810cc2285c82c890"
OLD = "scripts/joint_selector_probe_20261011.py"
ARCHIVE = "pipeline/reports/joint_selector_population_adapter_failed_20261011.py"
EXPECTED = "e2170d127fcb21dbc959f2dac77fd1c5ebac5465a10ab3301b8b89e4bc098ac5"


def main():
    owner = fg.load(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
    assert hashlib.sha256((ROOT / ARCHIVE).read_bytes()).hexdigest() == EXPECTED
    work = fg.load(ROOT / "pipeline/research_work.json")
    candidate = next(c for c in work["candidates"] if c["id"] == "m95-native-joint-mask-selector")
    entry = next(e for e in candidate["evidence"] if e["path"] == OLD)
    assert entry["sha256"] == EXPECTED
    entry.update(path=ARCHIVE, original_path=OLD,
                 citation_repair="Identical archived bytes; original SHA unchanged.")
    record = {"observed_at": datetime.now().astimezone().isoformat(),
              "token": TOKEN, "candidate_id": candidate["id"],
              "previous_path": OLD, "repaired_path": ARCHIVE,
              "sha256_before": EXPECTED, "sha256_after": entry["sha256"],
              "original_sha_preserved": True, "scientific_disposition_changed": False,
              "failure_preserved": True,
              "reason": "POSTFLIGHT failed because mutable working-script path changed; exact archived original exists."}
    audit = ROOT / "pipeline/reports/source_reference_repair_20261011.json"
    fg.save(audit, record)
    candidate["evidence"].append({"path": audit.relative_to(ROOT).as_posix(),
                                 "sha256": hashlib.sha256(audit.read_bytes()).hexdigest()})
    fg.save(ROOT / "pipeline/research_work.json", work)
    print(record)


if __name__ == "__main__":
    main()
