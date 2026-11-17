"""Read-only verification of the handoff's SHA-256 manifest; no project imports."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path


def verify_rows(root: Path, rows: list[dict], *, windows_placeholders: bool | None = None) -> dict:
    """Hash Git link-target bytes, never the contents of the linked directory."""
    if windows_placeholders is None:
        windows_placeholders = os.name == "nt"
    mismatches = []
    details = []
    symlinks_checked = 0
    placeholders_checked = 0
    for row in rows:
        path = root / row["path"]
        reason = None
        is_link = row.get("kind") == "symlink" or row.get("git_mode") == "120000"
        if row.get("git_mode") == "160000":
            reason = "gitlink_source_not_materialized"
        elif is_link:
            symlinks_checked += 1
            target = row.get("link_target")
            if not isinstance(target, str):
                reason = "symlink_metadata_missing_link_target"
            else:
                expected = target.encode("utf8", errors="surrogateescape")
                if hashlib.sha256(expected).hexdigest() != row["sha256"]:
                    reason = "symlink_metadata_target_sha256_mismatch"
                elif path.is_symlink():
                    # os.fsencode preserves POSIX surrogateescaped target bytes.
                    actual = os.fsencode(os.readlink(path))
                    if actual != expected or hashlib.sha256(actual).hexdigest() != row["sha256"]:
                        reason = "symlink_target_mismatch"
                elif windows_placeholders and path.is_file():
                    actual = path.read_bytes()
                    if actual != expected or hashlib.sha256(actual).hexdigest() != row["sha256"]:
                        reason = "windows_git_placeholder_target_mismatch"
                    else:
                        placeholders_checked += 1
                else:
                    reason = "expected_symlink_or_windows_git_placeholder"
        elif path.is_symlink():
            reason = "unexpected_symlink_for_regular_file"
        elif not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != row["sha256"]:
            reason = "regular_file_missing_or_sha256_mismatch"
        if reason:
            mismatches.append(row["path"])
            details.append({"path": row["path"], "reason": reason})
    return {
        "files_checked": len(rows), "symlink_entries_checked": symlinks_checked,
        "windows_git_placeholders_checked": placeholders_checked,
        "mismatches": mismatches, "mismatch_details": details,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    root = args.repo.resolve()
    rows = json.loads((root / "provenance/files.sha256.json").read_text(encoding="utf8"))
    result = verify_rows(root, rows)
    print(json.dumps(result, ensure_ascii=False))
    if result["mismatches"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
