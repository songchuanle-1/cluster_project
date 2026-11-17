"""Create an independent export without modifying the research repository."""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
PROJECT = Path("D:/project/cluster_project")
SOURCE = PROJECT / "Cluster"
EXPORT = Path("D:/project/cluster_github_export_20261117")
BASELINE = "5413102c57b526035f3920b5e7a81f3b58ad764d"
ENV = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", GIT_OPTIONAL_LOCKS="0",
           GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
CODE = {
    ".py", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".vbs",
    ".yaml", ".yml", ".toml", ".ini", ".cfg", ".conf",
    ".c", ".cc", ".cpp", ".cxx", ".h", ".hpp", ".cu", ".cuh",
    ".js", ".ts", ".jsx", ".tsx", ".mjs", ".r", ".jl", ".ipynb",
    ".tex", ".sty", ".bst", ".bib", ".sql", ".proto",
}
TEXT = {".md", ".rst", ".txt", ".json", ".jsonl", ".csv", ".diff", ".patch", ".html", ".xml"}
BINARY = {
    ".pth", ".pt", ".ckpt", ".bin", ".safetensors", ".onnx",
    ".npy", ".npz", ".h5", ".hdf5", ".ply", ".pcd",
    ".so", ".pyd", ".o", ".obj", ".a", ".dll", ".exe",
    ".pyc", ".pyo", ".png", ".jpg", ".jpeg", ".gif", ".pdf",
    ".tar", ".gz", ".tgz", ".zip", ".bundle", ".pack", ".idx", ".rev",
}
SKIP_DIRS = {
    ".git", "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache",
    "node_modules", ".venv", "venv", "build", "dist", "_task_backup",
}


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git(root: Path, *args: str) -> str:
    proc = subprocess.run(
        ["git", "-c", "safe.directory=" + root.as_posix(), "-C", str(root), *args],
        env=ENV, capture_output=True, text=True, encoding="utf8", timeout=300,
    )
    if proc.returncode:
        raise RuntimeError("git " + " ".join(args[:3]) + " failed: " + proc.stderr[-1500:])
    return proc.stdout


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf8")


def source_state() -> dict:
    index = SOURCE / ".git" / "index"
    raw = git(SOURCE, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    records = []
    for entry in raw.split("\0"):
        if not entry:
            continue
        # The audited source has no renames; fail rather than guess their format.
        if entry[0:2] in ("R ", " R", "C ", " C"):
            raise RuntimeError("Source rename requires explicit snapshot handling.")
        rel = entry[3:]
        path = SOURCE / rel
        records.append({
            "status": entry[:2], "path": rel,
            "sha256": sha(path.read_bytes()) if path.is_file() else None,
            "bytes": path.stat().st_size if path.is_file() else None,
        })
    return {
        "head": git(SOURCE, "rev-parse", "HEAD").strip(),
        "branch": git(SOURCE, "symbolic-ref", "--short", "HEAD").strip(),
        "index_sha256": sha(index.read_bytes()), "dirty": records,
    }


def worktrees() -> list[dict]:
    rows = []
    for block in git(SOURCE, "worktree", "list", "--porcelain").strip().split("\n\n"):
        fields = dict(line.split(" ", 1) if " " in line else (line, True)
                      for line in block.splitlines())
        rows.append({"path": fields["worktree"], "head": fields["HEAD"]})
    return rows


def paths(root: Path, skip_extra=()) -> list[Path]:
    result = []
    for directory, dirs, names in os.walk(root):
        dirs[:] = sorted(d for d in dirs if d not in SKIP_DIRS
                         and d not in skip_extra and not d.endswith(".git")
                         and ".lockdir" not in d)
        for name in sorted(names):
            result.append(Path(directory) / name)
    return result


def classification(path: Path, relative: Path) -> tuple[bool, str]:
    name = path.name.lower()
    suffix = path.suffix.lower()
    if name.startswith(".env") or name in {
        "id_rsa", "id_ed25519", "credentials", "server-accounts.md",
    } or suffix in {".pem", ".key", ".p12", ".pfx"}:
        return False, "credential_or_local_secret_file"
    if "work_before" in name:
        return False, "historical_owner_snapshot_not_execution_authority"
    if suffix in BINARY:
        return False, "asset_binary_or_build_product"
    if suffix in {".log", ".stdout", ".stderr", ".partial", ".lock", ".bak"}:
        return False, "raw_log_or_runtime_state"
    if suffix in CODE or name in {
        "makefile", "dockerfile", ".gitignore", ".gitattributes", "python", "license", "copying",
    }:
        return True, "source_or_configuration"
    if suffix in TEXT:
        if path.stat().st_size <= 2 * 1024 * 1024 or relative.as_posix() == "pipeline/research_work.json":
            return True, "historical_record_or_document"
        return False, "large_historical_record_over_2MiB"
    if not suffix and path.stat().st_size <= 256 * 1024:
        try:
            if path.read_bytes().startswith(b"#!"):
                return True, "extensionless_script"
        except OSError:
            pass
    return False, "unsupported_or_generated_artifact"


def copy_record(src: Path, dest: Path, source_label: str, records: list) -> None:
    data = src.read_bytes()
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    records.append({
        "source": source_label, "destination": dest.relative_to(EXPORT).as_posix(),
        "bytes": len(data), "sha256": sha(data),
    })


def prepare() -> None:
    if EXPORT.exists():
        raise RuntimeError("Export destination already exists; use finalize/verify instead.")
    before = source_state()
    trees = worktrees()
    write_json(HERE / "source_state.before.json", before)
    proc = subprocess.run(
        ["git", "-c", "safe.directory=" + SOURCE.as_posix(),
         "-c", "safe.directory=" + (SOURCE / ".git").as_posix(), "clone", "--no-hardlinks",
         "--no-checkout", "-c", "core.autocrlf=false", "-c", "core.longpaths=true",
         str(SOURCE), str(EXPORT)],
        capture_output=True, text=True, env=ENV, timeout=300,
    )
    if proc.returncode:
        raise RuntimeError("Independent local clone failed: " + proc.stderr[-1000:])
    git(EXPORT, "config", "user.name", "Chuanle Song")
    git(EXPORT, "config", "user.email", "songchle@mail2.sysu.edu.cn")
    git(EXPORT, "config", "commit.gpgsign", "false")
    git(EXPORT, "remote", "remove", "origin")
    # The local clone contains the complete object store, including detached heads.
    branches = []
    for row in trees:
        path = Path(row["path"])
        if path == SOURCE:
            continue
        dirty = git(path, "status", "--porcelain=v1", "--untracked-files=all")
        if dirty.strip():
            raise RuntimeError("An isolated version became dirty; preserve it explicitly first.")
        branch = "archive/isolated/" + path.name
        git(EXPORT, "cat-file", "-e", row["head"] + "^{commit}")
        git(EXPORT, "update-ref", "refs/heads/" + branch, row["head"])
        branches.append(dict(row, branch=branch, exact_original_commit=True))
    committed = "archive/local-main-committed-20261117"
    git(EXPORT, "update-ref", "refs/heads/" + committed, before["head"])
    working = "archive/local-working-20261117"
    git(EXPORT, "switch", "-c", working, before["head"])
    for row in before["dirty"]:
        src, dest = SOURCE / row["path"], EXPORT / row["path"]
        if row["sha256"] is None:
            if dest.is_file():
                dest.unlink()
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(src.read_bytes())
    git(EXPORT, "add", "-A")
    git(EXPORT, "commit", "-m", "Archive local research working changes without modifying the source tree")
    branches.append({
        "path": str(SOURCE), "head": git(EXPORT, "rev-parse", "HEAD").strip(),
        "source_head": before["head"], "branch": working, "dirty_files_preserved": len(before["dirty"]),
        "exact_original_commit": False,
    })
    git(EXPORT, "switch", "-C", "main", BASELINE)
    # Avoid retaining duplicate aliases of the old main as misleading default branches.
    for branch in ("master",):
        if git(EXPORT, "branch", "--list", branch).strip():
            git(EXPORT, "branch", "-D", branch)
    # Source builds are copied through Git history; remove binary products from current main.
    removed = []
    for name in git(EXPORT, "ls-files", "-z").split("\0"):
        if not name:
            continue
        rel = Path(name)
        path = EXPORT / rel
        if path.suffix.lower() in BINARY or any(part in {"build", "__pycache__"} for part in rel.parts):
            removed.append(rel.as_posix())
            if path.is_file():
                path.unlink()
    records, omissions = [], []
    roots = ["scripts", "configs", "framework", "docs", "pipeline", "Checkpoints"]
    for top in roots:
        root = PROJECT / top
        if not root.exists():
            continue
        for path in paths(root, skip_extra={"isolated_versions", "handoffs"}):
            rel = path.relative_to(PROJECT)
            include, reason = classification(path, rel)
            if include:
                copy_record(path, EXPORT / "project_support" / rel, rel.as_posix(), records)
            else:
                omissions.append({"source": rel.as_posix(), "bytes": path.stat().st_size, "reason": reason})
    copy_record(PROJECT / "SERVERS.yaml", EXPORT / "project_support" / "SERVERS.yaml",
                "SERVERS.yaml", records)
    for skill in ["songcl_research_pipeline", "songcl_remote_train"]:
        root = Path("C:/Users/chuanle song/.codex/skills") / skill
        for path in paths(root):
            rel = path.relative_to(root)
            include, reason = classification(path, rel)
            if include:
                copy_record(path, EXPORT / "tooling" / skill / rel,
                            "external_canonical_skill/" + skill + "/" + rel.as_posix(), records)
            else:
                omissions.append({
                    "source": "external_canonical_skill/" + skill + "/" + rel.as_posix(),
                    "bytes": path.stat().st_size, "reason": reason,
                })
    # Retain ignored source files as a distinct archive; do not overlay old code on integrated541.
    ignored = git(SOURCE, "ls-files", "--others", "--ignored", "--exclude-standard", "-z").split("\0")
    for name in ignored:
        if not name:
            continue
        rel = Path(name)
        if any(part in SKIP_DIRS or part.endswith(".git") for part in rel.parts):
            continue
        src = SOURCE / rel
        include, reason = classification(src, rel)
        if include and (src.suffix.lower() in CODE or src.name in {"Makefile", "Dockerfile"}):
            copy_record(src, EXPORT / "project_support/local_ignored_source" / rel,
                        "Cluster/ignored/" + rel.as_posix(), records)
    # Add explicit ignores to the isolated export only.
    ignore = EXPORT / ".gitignore"
    previous = ignore.read_text(encoding="utf8") if ignore.exists() else ""
    ignore.write_text(previous.rstrip() + """

# Server migration export: transfer datasets, weights and generated builds separately.
__pycache__/
*.py[cod]
*.pth
*.pt
*.ckpt
*.safetensors
*.so
*.pyd
*.o
*.obj
*.log
.env
.env.*
.venv/
venv/
build/
dist/
""", encoding="utf8")
    manifest = {
        "prepared_at": datetime.now(timezone.utc).isoformat(),
        "source_project": str(PROJECT), "source_repository": str(SOURCE),
        "export_repository": str(EXPORT), "main_source_commit": BASELINE,
        "source_state_before": before,
        "archive_branches": branches,
        "committed_source_branch": {"branch": committed, "sha": before["head"]},
        "support_files": records, "support_file_count": len(records),
        "support_bytes": sum(row["bytes"] for row in records),
        "excluded_files": omissions, "excluded_file_count": len(omissions),
        "excluded_bytes": sum(row["bytes"] for row in omissions),
        "removed_from_current_main": removed,
        "exclusion_notes": [
            "Original .git object directories, isolated worktrees, handoffs, caches and build directories were pruned.",
            "All isolated worktree HEADs are preserved as exact archive branches.",
            "History retains its original compiled binaries and papers if present; current main omits these assets.",
            "Weights/data/raw logs are not uploaded. Omission sizes are metadata only, not checksum verification.",
            "Historical runtime/lease/configuration files are archival evidence, not valid launch authority.",
        ],
    }
    write_json(HERE / "export_manifest.prepare.json", manifest)
    if source_state() != before:
        raise RuntimeError("Source state changed during export; investigate before publication.")
    print(json.dumps({
        "prepared": True, "export": str(EXPORT),
        "archive_branches": len(branches) + 1, "support_files": len(records),
        "support_MiB": round(manifest["support_bytes"] / 2**20, 2),
        "omitted_files": len(omissions), "source_untouched": True,
    }))


def finalize() -> None:
    if not EXPORT.exists():
        raise RuntimeError("Prepare export first.")
    copied = []
    # The original repository records DEST3D only as an opaque gitlink without
    # .gitmodules. Include the actual available source as normal files on main.
    nested_root = SOURCE / "framework/DEST3D"
    nested_records, nested_excluded = [], []
    for path in paths(nested_root):
        rel = path.relative_to(nested_root)
        include, reason = classification(path, rel)
        if include:
            copy_record(path, EXPORT / "framework/DEST3D" / rel,
                        "Cluster/framework/DEST3D/" + rel.as_posix(), nested_records)
        else:
            nested_excluded.append({"path": rel.as_posix(), "bytes": path.stat().st_size, "reason": reason})
    for entry in git(EXPORT, "ls-files", "--stage", "-z").split("\0"):
        if entry and entry.split("\t", 1)[1] == "framework/DEST3D" and entry.startswith("160000 "):
            git(EXPORT, "rm", "--cached", "-f", "--", "framework/DEST3D")
    write_json(EXPORT / "provenance/nested_sources.json", {
        "source": "Cluster/framework/DEST3D",
        "original_gitlink_commit": "9512afa38fd58114555c5e42a86056c20135e522",
        "archival_mode": "Current available source files flattened into main; original archive refs retain the gitlink.",
        "gitlink_identity_matches_files": "UNKNOWN: no nested .git or .gitmodules is present in the source snapshot.",
        "files": nested_records, "excluded_files": nested_excluded,
        "license_preserved": (EXPORT / "framework/DEST3D/LICENSE").is_file(),
    })
    upstream = EXPORT / "docs/upstream/README.md"
    if not upstream.exists():
        upstream.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(EXPORT / "README.md", upstream)
    copy_record(HERE / "README.github.md", EXPORT / "README.md", "handoff/README.github.md", copied)
    for name, target in [("docs", "docs/migration"), ("experiments", "experiments")]:
        for path in paths(HERE / name):
            copy_record(path, EXPORT / target / path.relative_to(HERE / name),
                        "handoff/" + name + "/" + path.relative_to(HERE / name).as_posix(), copied)
    provenance = EXPORT / "provenance"
    for name in [
        "export_manifest.prepare.json", "source_state.before.json",
        "github_access.actual.json", "github_repository.create.json",
        "verification_checks.actual.json",
        "migration_helper_verification.actual.json",
    ]:
        copy_record(HERE / name, provenance / name, "handoff/" + name, copied)
    for path in paths(HERE / "audit") if (HERE / "audit").exists() else []:
        if path.suffix.lower() in {".json", ".md", ".csv", ".py"} and "cache" not in path.name.lower():
            copy_record(path, provenance / "audit" / path.relative_to(HERE / "audit"),
                        "handoff/audit/" + path.relative_to(HERE / "audit").as_posix(), copied)
    for name in ["build_export.py", "github_repository.py", "check_github_access.py",
                 "verify_export.py", "materialize_project.py"]:
        copy_record(HERE / name, EXPORT / "tooling/export" / name, "handoff/" + name, copied)
    manifest = json.loads((HERE / "export_manifest.prepare.json").read_text(encoding="utf8"))
    write_json(provenance / "handoff_files.json", copied)
    actual = source_state()
    if actual != manifest["source_state_before"]:
        raise RuntimeError("Source state differs from preserved state; publication halted.")
    modes = {}
    for entry in git(EXPORT, "ls-files", "--stage", "-z").split("\0"):
        if entry:
            info, name = entry.split("\t", 1)
            modes[name] = info.split(" ", 1)[0]
    rows = []
    for path in paths(EXPORT):
        rel = path.relative_to(EXPORT).as_posix()
        if rel in {"provenance/files.sha256.json", "provenance/verification.actual.json"}:
            continue
        data = path.read_bytes()
        mode = modes.get(rel, "100644")
        row = {"path": rel, "bytes": len(data), "sha256": sha(data),
               "kind": "symlink" if mode == "120000" else "file", "git_mode": mode}
        if mode == "120000":
            row["link_target"] = data.decode("utf8")
        rows.append(row)
    verification = {
        "verified_at": datetime.now(timezone.utc).isoformat(),
        "source_untouched": True, "dirty_files_preserved": len(actual["dirty"]),
        "main_source_commit": BASELINE, "archive_branch_count": len(manifest["archive_branches"]) + 1,
        "files": len(rows), "bytes": sum(row["bytes"] for row in rows),
        "largest_bytes": max(row["bytes"] for row in rows),
        "all_current_files_below_GitHub_100MiB": all(row["bytes"] < 100 * 2**20 for row in rows),
    }
    write_json(provenance / "files.sha256.json", rows)
    write_json(provenance / "verification.actual.json", verification)
    write_json(HERE / "export_verification.actual.json", verification)
    print(json.dumps(verification))


def verify() -> None:
    rows = json.loads((EXPORT / "provenance/files.sha256.json").read_text(encoding="utf8"))
    mismatches = [
        row["path"] for row in rows
        if not (EXPORT / row["path"]).is_file()
        or sha((EXPORT / row["path"]).read_bytes()) != row["sha256"]
    ]
    source = json.loads((HERE / "source_state.before.json").read_text(encoding="utf8"))
    if mismatches or source_state() != source:
        raise RuntimeError("Export or original source verification failed: " + repr(mismatches[:10]))
    manifest = json.loads((HERE / "export_manifest.prepare.json").read_text(encoding="utf8"))
    for branch in manifest["archive_branches"]:
        if git(EXPORT, "rev-parse", "refs/heads/" + branch["branch"]).strip() != branch["head"]:
            raise RuntimeError("Archived source branch changed.")
    print(json.dumps({"verified_files": len(rows), "mismatches": 0, "source_untouched": True,
                      "archive_branches_verified": len(manifest["archive_branches"])}))


def commit() -> None:
    """Write a single pack instead of thousands of slow Windows loose objects."""
    verify()
    if git(EXPORT, "rev-parse", "HEAD").strip() != BASELINE:
        raise RuntimeError("Expected the original integrated baseline before export commit.")
    rows = json.loads((EXPORT / "provenance/files.sha256.json").read_text(encoding="utf8"))
    for rel in ["provenance/files.sha256.json", "provenance/verification.actual.json"]:
        data = (EXPORT / rel).read_bytes()
        rows.append({"path": rel, "git_mode": "100644", "sha256": sha(data)})
    command = ["git", "-c", "safe.directory=" + EXPORT.as_posix(),
               "-C", str(EXPORT), "fast-import", "--quiet"]
    process = subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                               stderr=subprocess.PIPE, env=ENV)
    try:
        for number, row in enumerate(rows, 1):
            path = EXPORT / row["path"]
            data = path.read_bytes()
            if sha(data) != row["sha256"]:
                raise RuntimeError("File changed before packed import: " + row["path"])
            process.stdin.write(f"blob\nmark :{number}\ndata {len(data)}\n".encode("ascii"))
            process.stdin.write(data)
            process.stdin.write(b"\n")
        message = b"Archive current Cluster code, experiment inventory and server migration handover"
        process.stdin.write(
            f"commit refs/heads/main\ncommitter Chuanle Song <songchle@mail2.sysu.edu.cn> {int(time.time())} +0000\n"
            .encode("ascii")
        )
        process.stdin.write(f"data {len(message)}\n".encode("ascii") + message + b"\n")
        process.stdin.write(f"from {BASELINE}\ndeleteall\n".encode("ascii"))
        for number, row in enumerate(rows, 1):
            mode = row.get("git_mode", "100644")
            if mode not in {"100644", "100755", "120000"}:
                raise RuntimeError("Unsupported file mode in export manifest.")
            quoted = json.dumps(row["path"], ensure_ascii=False)
            process.stdin.write(f"M {mode} :{number} {quoted}\n".encode("utf8"))
        process.stdin.write(b"\ndone\n")
        process.stdin.close()
        process.wait(timeout=180)
        errors = process.stderr.read().decode("utf8", errors="replace")
        if process.returncode:
            raise RuntimeError("Packed import failed: " + errors[-1800:])
    except BaseException:
        if process.poll() is None:
            process.terminate()
            process.wait(timeout=15)
        raise
    git(EXPORT, "read-tree", "--reset", "main")
    result = {
        "committed_at": datetime.now(timezone.utc).isoformat(),
        "main_sha": git(EXPORT, "rev-parse", "HEAD").strip(),
        "parent": BASELINE, "files": len(rows), "method": "single_pack_fast_import",
        "archive_refs_unchanged": True, "source_untouched": source_state() == json.loads(
            (HERE / "source_state.before.json").read_text(encoding="utf8")
        ),
    }
    write_json(HERE / "commit.actual.json", result)
    print(json.dumps(result))


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "finalize", "verify", "commit"])
    {"prepare": prepare, "finalize": finalize, "verify": verify, "commit": commit}[parser.parse_args().mode]()
