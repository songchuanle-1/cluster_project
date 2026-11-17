"""Preserve only our hash-verified untracked native-test files before ff sync."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

ROOT = Path("/data3/songcl/Project/Cluster_project/Cluster")
PIPELINE = ROOT.parent / "pipeline"
AUDIT = PIPELINE / "bei_admission_audit_20261009-1042.json"
DEST = PIPELINE / "bei_tested_staging_archive_20261009-1044"


def main():
    audit = json.loads(AUDIT.read_text())
    expected = {row["path"].removeprefix("Cluster/"): row["sha256"]
                for row in audit["physical_sources"]}
    expected[audit["config"]] = "a18f2c6ffcaac3e3050835a5afea1db1e7b0d23afc79f25c6c65134c813b004a"
    expected["scripts/validate_bei_20261009.py"] = (
        "01950ccace36f92b8d5ee051f6a7b6197255db0cc9b7b7635d81c41ad8c4571a")
    assert not DEST.exists()
    resolved = ROOT.resolve()
    paths = []
    for relative, expected_hash in expected.items():
        source = (ROOT / relative).resolve()
        target = (DEST / relative).resolve()
        assert source.is_relative_to(resolved) and target.is_relative_to(DEST.resolve())
        assert source.is_file() and not (ROOT / relative).is_symlink()
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_hash, relative
        tracked = subprocess.run(
            ["git", "-C", str(ROOT), "ls-files", "--error-unmatch", "--", relative],
            capture_output=True)
        assert tracked.returncode == 1, "Refuse moving tracked file: " + relative
        paths.append((source, target))
    for source, target in paths:
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(source), str(target))
    print(json.dumps({"archive": str(DEST), "verified_files_preserved": len(paths),
                      "unrelated_paths_touched": False}))


if __name__ == "__main__":
    main()
