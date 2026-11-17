"""Read-only cluster_project export audit. Never emits matching secret values."""
from __future__ import annotations

import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import subprocess
import sys
import urllib.parse


ROOT = Path(r"D:/project/cluster_project")
REPO = ROOT / "Cluster"
OUT = ROOT / "pipeline/handoffs/20261117_github_migration/audit"
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
TEXT_EXT = {
    ".py", ".pyi", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".c", ".cc",
    ".cpp", ".cu", ".cuh", ".h", ".hpp", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".conf", ".env", ".md", ".rst", ".txt", ".csv", ".tsv", ".json",
    ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".html", ".css", ".cmake",
    ".ninja", ".xml", ".ipynb", ".dockerignore", ".gitignore", ".gitattributes",
}
SOURCE_EXT = {
    ".py", ".pyi", ".sh", ".bash", ".ps1", ".bat", ".cmd", ".c", ".cc",
    ".cpp", ".cu", ".cuh", ".h", ".hpp", ".yaml", ".yml", ".toml", ".ini",
    ".cfg", ".conf", ".js", ".mjs", ".cjs", ".ts", ".tsx", ".jsx", ".cmake",
}
GENERATED_PARTS = {
    "__pycache__", ".pytest_cache", ".mypy_cache", ".ruff_cache", "node_modules",
    ".venv", "venv", ".git",
}
NO_JSON_PARTS = {
    "diagnostic_bundles", "diagnostic_runs", "Checkpoints", "checkpoints",
    "outputs", "output", "work_dir", "logs_analysis",
}
CURRENT_MAX_TEXT = 2 * 1024 * 1024
CURRENT_MAX_JSON = 256 * 1024
PATTERNS = [
    ("private_key_material", "high", re.compile(
        r"-----BEGIN (?:OPENSSH |RSA |DSA |EC |ENCRYPTED )?PRIVATE KEY-----")),
    ("github_token", "high", re.compile(
        r"\b(?:gh[pousr]_[A-Za-z0-9]{30,255}|github_pat_[A-Za-z0-9_]{30,255})\b")),
    ("aws_access_key_id", "high", re.compile(r"\b(?:AKIA|ASIA)[A-Z0-9]{16}\b")),
    ("openai_api_key", "high", re.compile(
        r"\bsk-(?:proj-|svcacct-)?[A-Za-z0-9_-]{24,255}\b")),
    ("slack_token", "high", re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{15,255}\b")),
    ("google_api_key", "high", re.compile(r"\bAIza[A-Za-z0-9_-]{30,60}\b")),
    ("gitlab_token", "high", re.compile(r"\bglpat-[A-Za-z0-9_-]{16,255}\b")),
    ("credential_in_url", "candidate", re.compile(
        r"\b(?:https?|ssh|ftp)://[^\s/:@\"'<>]+:[^\s/@\"'<>]{4,}@[^\s/\"'<>]+")),
    ("literal_bearer_token", "candidate", re.compile(
        r"\bBearer\s+[A-Za-z0-9_+/.=-]{24,255}\b")),
]
ASSIGN = re.compile(
    r"""(?ix)
    (?<![A-Za-z0-9_])
    ["']?(?P<key>(?:[A-Za-z0-9_]*(?:password|passwd|pwd|secret|api_key|apikey|
    access_token|auth_token|github_token|hf_token|wandb_api_key)[A-Za-z0-9_]*))["']?
    \s*[:=]\s*(?P<quote>["'])(?P<value>[^"'\r\n]{4,500})(?P=quote)
    """
)
PLACEHOLDER = re.compile(
    r"(?ix)^(?:none|null|false|true|password|passwd|secret|token|api[_-]?key|"
    r"dummy|test|example|changeme|your[_ -]|replace[_ -]|placeholder|redacted|"
    r"xxx|abc|<|\$\{|\{\{|os\.|environ|https?://)"
)


def git(path: Path, *args: str, input_bytes: bytes | None = None) -> bytes:
    p = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(path), *args],
        input=input_bytes, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV,
    )
    if p.returncode:
        raise RuntimeError(f"Read-only git command failed: {args[0]} at {path.name}")
    return p.stdout


def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()


def sensitive_filename(path: Path) -> str | None:
    n = path.name.lower()
    if re.fullmatch(r"id_(?:rsa|dsa|ecdsa|ed25519)", n):
        return "ssh_private_key_filename"
    if n in {".netrc", ".npmrc", ".pypirc", ".git-credentials", "credentials"}:
        return "credential_store_filename"
    if n == ".env" or n.startswith(".env."):
        return "environment_secrets_filename"
    if path.suffix.lower() in {".pem", ".key", ".p12", ".pfx"}:
        return "key_or_certificate_filename"
    if re.search(r"(?:^|[._-])credentials?(?:[._-]|$)", n):
        return "credential_named_file"
    return None


def scan_text(text: str) -> list[dict]:
    found = []
    for lineno, line in enumerate(text.splitlines(), 1):
        line_types = set()
        for kind, confidence, pattern in PATTERNS:
            if pattern.search(line):
                line_types.add((kind, confidence))
        for m in ASSIGN.finditer(line):
            value = m.group("value").strip()
            if not PLACEHOLDER.search(value) and not (
                value.startswith(("/", "./", "../", "C:", "D:", "~"))
                or value in {"${PASSWORD}", "${TOKEN}", "getpass.getpass()"}
                or re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*(?:_PASSWORD|_TOKEN|_KEY)", value)
            ):
                key = m.group("key").lower()
                kind = "password_literal" if any(x in key for x in ("password", "passwd", "pwd")) else "secret_or_token_literal"
                line_types.add((kind, "candidate"))
        for kind, confidence in sorted(line_types):
            found.append({"line": lineno, "type": kind, "confidence": confidence})
    return found


def decode_text(data: bytes) -> str | None:
    if b"\x00" in data[:8192]:
        return None
    try:
        return data.decode("utf-8-sig")
    except UnicodeDecodeError:
        try:
            return data.decode("gb18030")
        except UnicodeDecodeError:
            return None


def sanitized_remote(raw: str) -> dict:
    raw = raw.strip()
    if "://" in raw:
        u = urllib.parse.urlsplit(raw)
        return {
            "scheme": u.scheme,
            "host": u.hostname,
            "path": u.path,
            "embedded_credentials_present": bool(u.username or u.password),
        }
    m = re.match(r"(?:[^@]+@)?([^:]+):(.+)", raw)
    if m:
        return {"scheme": "ssh", "host": m.group(1), "path": m.group(2),
                "embedded_credentials_present": False}
    return {"scheme": "local_or_unparsed", "value_omitted": True}


def parse_worktrees() -> list[dict]:
    worktrees = []
    for block in git(REPO, "worktree", "list", "--porcelain").decode("utf-8").strip().split("\n\n"):
        item = {}
        for line in block.splitlines():
            k, _, v = line.partition(" ")
            if k in {"worktree", "HEAD", "branch"}:
                item[k] = v
            elif k in {"detached", "locked", "prunable"}:
                item[k] = True
        if item:
            worktrees.append(item)
    return worktrees


def status_items(path: Path) -> list[dict]:
    items = []
    raw = git(path, "status", "--porcelain=v1", "-z", "--untracked-files=all")
    parts = raw.split(b"\0")
    i = 0
    while i < len(parts):
        rec = parts[i]
        i += 1
        if not rec:
            continue
        status = rec[:2].decode("ascii", "replace")
        item = {"status": status, "path": rec[3:].decode("utf-8", "replace")}
        if "R" in status or "C" in status:
            item["original_path"] = parts[i].decode("utf-8", "replace")
            i += 1
        items.append(item)
    return items


def diff_items(base: str, head: str) -> list[dict]:
    data = git(REPO, "diff", "--name-status", "-z", base, head).split(b"\0")
    out = []
    i = 0
    while i < len(data) and data[i]:
        status = data[i].decode()
        i += 1
        name = data[i].decode("utf-8", "replace")
        i += 1
        item = {"status": status, "path": name}
        if status.startswith(("R", "C")):
            item["new_path"] = data[i].decode("utf-8", "replace")
            i += 1
        out.append(item)
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    worktrees = parse_worktrees()
    main_head = git(REPO, "rev-parse", "HEAD").decode().strip()
    print(f"Audit started: {len(worktrees)} worktrees", flush=True)
    records = []
    top = collections.defaultdict(lambda: collections.Counter())
    subdir = collections.defaultdict(lambda: collections.Counter())
    skipped = collections.Counter()
    git_markers = []
    errors = []
    seen_dirs = set()

    def walk(directory: Path):
        try:
            with os.scandir(directory) as entries:
                for entry in entries:
                    p = Path(entry.path)
                    if p == OUT or p.is_relative_to(OUT):
                        continue
                    if entry.is_symlink():
                        records.append({"path": rel(p), "kind": "symlink", "bytes": 0})
                        continue
                    if entry.is_dir(follow_symlinks=False):
                        if entry.name == ".git":
                            git_markers.append({"path": rel(p), "kind": "directory"})
                            skipped["git_metadata_directories"] += 1
                            continue
                        seen_dirs.add(rel(p))
                        walk(p)
                    elif entry.is_file(follow_symlinks=False):
                        if entry.name == ".git":
                            git_markers.append({"path": rel(p), "kind": "file"})
                            continue
                        st = entry.stat(follow_symlinks=False)
                        name = rel(p)
                        parts = p.relative_to(ROOT).parts
                        ext = p.suffix.lower()
                        generated = bool(set(parts) & GENERATED_PARTS)
                        source = ext in SOURCE_EXT and not generated
                        records.append({"path": name, "bytes": st.st_size, "ext": ext,
                                        "source": source, "generated": generated})
                        a = top[parts[0]]
                        a["files"] += 1
                        a["bytes"] += st.st_size
                        if source:
                            a["source_files"] += 1
                            a["source_bytes"] += st.st_size
                        key = "/".join(parts[:3]) if parts[0] == "pipeline" else "/".join(parts[:2])
                        b = subdir[key]
                        b["files"] += 1
                        b["bytes"] += st.st_size
                        if source:
                            b["source_files"] += 1
                            b["source_bytes"] += st.st_size
        except (OSError, ValueError) as exc:
            errors.append({"path": rel(directory), "error_type": type(exc).__name__})

    walk(ROOT)
    print(f"Metadata inventory: {len(records)} files", flush=True)
    current_findings = []
    secret_names = []
    current_scanned = collections.Counter()
    scan_skips = collections.Counter()
    source_hashes = {}
    unique_content = {}
    text_results = {}
    for item in records:
        if item.get("kind") == "symlink":
            continue
        p = ROOT / item["path"]
        name_kind = sensitive_filename(p)
        if name_kind:
            secret_names.append({"path": item["path"], "type": name_kind})
        if item["generated"]:
            scan_skips["generated_or_cache"] += 1
            continue
        ext = item["ext"]
        is_text_candidate = ext in TEXT_EXT or p.name in {
            "Dockerfile", "Makefile", "CMakeLists.txt", ".gitignore", ".gitattributes",
        } or bool(name_kind)
        if not is_text_candidate:
            scan_skips["non_text_extension"] += 1
            continue
        parts = set(p.relative_to(ROOT).parts)
        if ext in {".json", ".ipynb"} and (
            bool(parts & NO_JSON_PARTS) or item["bytes"] > CURRENT_MAX_JSON
        ):
            scan_skips["diagnostic_or_large_json"] += 1
            continue
        if item["bytes"] > CURRENT_MAX_TEXT:
            scan_skips["text_over_2MiB"] += 1
            continue
        try:
            data = p.read_bytes()
        except OSError as exc:
            errors.append({"path": item["path"], "error_type": type(exc).__name__})
            continue
        sha = hashlib.sha256(data).hexdigest()
        if item["source"]:
            source_hashes[item["path"]] = {"sha256": sha, "bytes": len(data)}
        current_scanned["files"] += 1
        current_scanned["bytes"] += len(data)
        unique_content.setdefault(sha, {"bytes": len(data), "paths": []})["paths"].append(item["path"])
        if sha not in text_results:
            text = decode_text(data)
            text_results[sha] = scan_text(text) if text is not None else None
            if text is not None:
                current_scanned["unique_text_blobs"] += 1
                current_scanned["unique_text_bytes"] += len(data)
        findings = text_results[sha]
        if findings:
            for hit in findings:
                current_findings.append({"path": item["path"], **hit})
    print(f"Current text scan: {current_scanned['files']} paths, "
          f"{current_scanned['unique_text_blobs']} unique texts", flush=True)

    def worktree_info(w: dict) -> dict:
        path = Path(w["worktree"])
        tracked = git(path, "ls-files", "-z").split(b"\0")
        tracked_names = [x.decode("utf-8", "replace") for x in tracked if x]
        large = []
        total = 0
        for name in tracked_names:
            p = path / name
            try:
                size = p.stat().st_size
                total += size
                if size > 20 * 1024 * 1024:
                    large.append({"path": name, "bytes": size})
            except OSError:
                pass
        status = status_items(path)
        prefix = rel(path) + "/"
        source = {k[len(prefix):]: v for k, v in source_hashes.items() if k.startswith(prefix)}
        same = changed = added = 0
        for name, val in source.items():
            main_val = source_hashes.get("Cluster/" + name)
            if not main_val:
                added += 1
            elif main_val["sha256"] == val["sha256"]:
                same += 1
            else:
                changed += 1
        return {
            "name": path.name, "path": rel(path), "head": w["HEAD"],
            "branch": w.get("branch"), "detached": bool(w.get("detached")),
            "tracked_files": len(tracked_names), "tracked_current_bytes": total,
            "tracked_current_files_gt20MiB": large,
            "status_counts": dict(collections.Counter(s["status"] for s in status)),
            "status_entries": status,
            "source_files": len(source),
            "source_bytes": sum(x["bytes"] for x in source.values()),
            "source_same_as_main_working_copy": same,
            "source_changed_vs_main_working_copy": changed,
            "source_added_vs_main_working_copy": added,
            "head_diff_vs_main_head": diff_items(main_head, w["HEAD"]),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        worktree_details = list(pool.map(worktree_info, worktrees))
    print("Worktree index and divergence inventory completed", flush=True)

    remote_names = git(REPO, "remote").decode().splitlines()
    remotes = []
    for name in remote_names:
        for raw in git(REPO, "remote", "get-url", "--all", name).decode().splitlines():
            remotes.append({"name": name, **sanitized_remote(raw)})

    heads = sorted({x["HEAD"] for x in worktrees})
    raw_objects = git(REPO, "rev-list", "--objects", "--all", *heads)
    objects = {}
    for line in raw_objects.decode("utf-8", "replace").splitlines():
        oid, _, name = line.partition(" ")
        objects.setdefault(oid, name)
    batch = git(REPO, "cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                input_bytes=("\n".join(objects) + "\n").encode())
    object_types = collections.Counter()
    object_bytes = collections.Counter()
    blobs = []
    for line in batch.decode().splitlines():
        oid, kind, raw_size = line.split()
        size = int(raw_size)
        object_types[kind] += 1
        object_bytes[kind] += size
        if kind == "blob":
            blobs.append({"oid": oid, "path": objects[oid], "bytes": size})
    historical_findings = []
    historical_scanned = collections.Counter()
    historical_skips = []
    process = subprocess.Popen(
        ["git", "-c", "safe.directory=*", "-C", str(REPO), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV,
    )
    try:
        for b in blobs:
            # The full reachable history is 158 MB; all blobs can be classified.
            # No current diagnostic JSON or external weights are read here.
            process.stdin.write((b["oid"] + "\n").encode())
            process.stdin.flush()
            header = process.stdout.readline().decode().strip().split()
            size = int(header[2])
            data = process.stdout.read(size)
            process.stdout.read(1)
            text = decode_text(data)
            if text is None:
                historical_skips.append({**b, "reason": "binary_or_non_decodable"})
                continue
            historical_scanned["unique_text_blobs"] += 1
            historical_scanned["text_bytes"] += len(data)
            for hit in scan_text(text):
                historical_findings.append({**b, **hit})
    finally:
        process.stdin.close()
        process.wait(timeout=30)
    print(f"History scan: {len(blobs)} unique blobs; "
          f"{historical_scanned['unique_text_blobs']} decoded as text", flush=True)

    mirrors = []
    for topname in ("configs", "framework", "scripts", "docs"):
        prefix = topname + "/"
        candidates = {k[len(prefix):]: v for k, v in source_hashes.items() if k.startswith(prefix)}
        same, changed, only = [], [], []
        for name, value in candidates.items():
            other = source_hashes.get("Cluster/" + topname + "/" + name)
            if other is None:
                only.append(name)
            elif value["sha256"] == other["sha256"]:
                same.append(name)
            else:
                changed.append(name)
        mirrors.append({"root_directory": topname, "source_files": len(candidates),
                        "same_as_Cluster": len(same), "different_from_Cluster": len(changed),
                        "only_in_project_root": len(only),
                        "different_paths": changed, "root_only_paths": only})

    isolated_source_paths = {k: v for k, v in source_hashes.items()
                             if k.startswith("pipeline/isolated_versions/")}
    isolated_unique = {}
    for value in isolated_source_paths.values():
        isolated_unique[value["sha256"]] = value["bytes"]
    current_high = [x for x in current_findings if x["confidence"] == "high"]
    history_high = [x for x in historical_findings if x["confidence"] == "high"]
    audit = {
        "audit_started_utc": started,
        "audit_finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "project_root": str(ROOT),
        "read_only_scope": "Source and Git reads; only audit JSON/Markdown written in handoff audit directory.",
        "upload_authorization_decision": "NOT_PROVIDED; this is an input audit, staged export requires a separate audit.",
        "main_head": main_head,
        "actual_server4_integrated_head_reported_by_parent": "5413102c57b526035f3920b5e7a81f3b58ad764d",
        "server_access": "None",
        "private_server_accounts_read": False,
        "git_remotes_sanitized": remotes,
        "top_level_inventory": [{"name": k, **dict(v)} for k, v in sorted(top.items())],
        "source_subdirectory_inventory": [
            {"path": k, **dict(v)} for k, v in sorted(subdir.items())
            if v["source_files"] or k.startswith("pipeline/isolated_versions")
        ],
        "git_markers": git_markers,
        "worktrees": worktree_details,
        "root_mirror_comparisons": mirrors,
        "isolated_source_duplication": {
            "source_file_paths": len(isolated_source_paths),
            "logical_bytes": sum(v["bytes"] for v in isolated_source_paths.values()),
            "unique_sha256_contents": len(isolated_unique),
            "unique_content_bytes": sum(isolated_unique.values()),
        },
        "current_text_scan": {
            **dict(current_scanned), "path_skips": dict(scan_skips),
            "sensitive_filename_candidates": secret_names,
            "findings": current_findings, "high_confidence_hits": len(current_high),
            "limit_bytes": CURRENT_MAX_TEXT, "json_limit_bytes": CURRENT_MAX_JSON,
            "excluded_json_components": sorted(NO_JSON_PARTS),
        },
        "reachable_history_scan": {
            "explicit_worktree_heads": heads,
            "ref_scope": "--all plus every current registered worktree HEAD",
            "objects_by_type": dict(object_types),
            "object_bytes_by_type": dict(object_bytes),
            "unique_blobs": len(blobs), **dict(historical_scanned),
            "findings": historical_findings, "high_confidence_hits": len(history_high),
            "blobs_gt20MiB": [x for x in blobs if x["bytes"] > 20 * 1024 * 1024],
            "blobs_gt100MiB": [x for x in blobs if x["bytes"] > 100 * 1024 * 1024],
            "nontext_blobs_not_secret_scanned": historical_skips,
            "limitation": "Historical finding paths are representative object paths from rev-list; values are never emitted.",
        },
        "metadata_skips": dict(skipped),
        "filesystem_errors": errors,
        "recommendation": [
            "Preserve integrated 5413102 as the tested migration baseline; archive local 0747 plus all current dirty/untracked source separately.",
            "Preserve each isolated HEAD as a named archive ref and include any worktree dirty/untracked changes in that archive before snapshotting.",
            "Do not materialize 26 full isolated directories in the GitHub tree; Git archive refs share identical objects and preserve real commit ancestry.",
            "If a snapshot-only export becomes necessary, keep variants as base commit plus per-worktree delta, additions and deletion manifest; preserve binary differences separately.",
            "Include project-root scripts/framework/configs and pipeline source/documentation outside Cluster because they are not all represented by Cluster/main.",
            "Exclude runtime checkpoints, diagnostics, caches and generated build outputs from the publishable working tree; assess historical artifacts independently.",
            "Independently rescan the final staged tree and all refs selected for push; candidate literals require contextual review, and this audit is not upload approval.",
        ],
    }
    path = OUT / "export_scope_security_audit.json"
    path.write_text(json.dumps(audit, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md = [
        "# cluster_project GitHub migration input audit",
        "",
        f"- Audit date: 2026-11-17. Local main: `{main_head}`.",
        f"- Registered worktrees: {len(worktrees)} (main plus {len(worktrees)-1} isolated checkouts).",
        f"- Reachable history: {object_types['commit']} commits, {len(blobs)} unique blobs, "
        f"{object_bytes['blob']:,} blob bytes; {historical_scanned['unique_text_blobs']} text blobs scanned.",
        f"- History blobs above 20 MiB: {len(audit['reachable_history_scan']['blobs_gt20MiB'])}; "
        f"above 100 MiB: {len(audit['reachable_history_scan']['blobs_gt100MiB'])}.",
        f"- Current bounded text scan: {current_scanned['files']:,} file paths, "
        f"{current_scanned['unique_text_blobs']:,} unique text contents.",
        f"- High confidence credential-pattern hits: current {len(current_high)}, history {len(history_high)}.",
        f"- Candidate literal findings: current {len(current_findings)-len(current_high)}, "
        f"history {len(historical_findings)-len(history_high)}; only paths/types/line numbers are recorded.",
        f"- Current Git remotes: {len(remotes)}; embedded credential values were never emitted.",
        "",
        "| Top-level path | Files | Bytes | Source/config files | Source/config bytes |",
        "|---|---:|---:|---:|---:|",
    ]
    for name, val in sorted(top.items()):
        md.append(f"| `{name}` | {val['files']:,} | {val['bytes']:,} | "
                  f"{val['source_files']:,} | {val['source_bytes']:,} |")
    dup = audit["isolated_source_duplication"]
    md += [
        "",
        f"Isolated source/config copies occupy {dup['logical_bytes']:,} logical bytes "
        f"across {dup['source_file_paths']:,} paths, but only "
        f"{dup['unique_sha256_contents']:,} unique contents ({dup['unique_content_bytes']:,} bytes).",
        "",
        "The recommended export keeps one integrated main tree and separate archive refs for local and "
        "isolated versions. Git shares duplicate objects across these refs. Root-level operational scripts, "
        "framework/config overlays and pipeline source must be included independently; they are outside the "
        "Cluster repository and are not fully covered by its branches.",
        "",
        "The JSON records all worktree HEADs, dirty/untracked paths, source divergence, root mirrors, "
        "large-file findings and credential-pattern candidates. Worktree dirty changes must be preserved "
        "before an archive ref can represent the full checkout.",
        "",
        "Current diagnostic/checkpoint JSON, text above 2 MiB, caches and non-text binaries were excluded "
        "from current-content scanning. All reachable history blobs were classified and every decodable "
        "text blob was scanned. Neither server account references nor remote servers were accessed.",
        "",
        "**This is not a final upload approval. The exact staged export and selected push refs need an "
        "independent scan.**",
        "",
    ]
    (OUT / "export_scope_security_audit.md").write_text("\n".join(md), encoding="utf-8")
    print(json.dumps({
        "json": str(path), "markdown": str(OUT / "export_scope_security_audit.md"),
        "current_high": len(current_high), "history_high": len(history_high),
        "current_candidates": len(current_findings) - len(current_high),
        "history_candidates": len(historical_findings) - len(history_high),
        "files": len(records), "worktrees": len(worktrees),
        "filesystem_errors": len(errors),
    }, indent=2))


if __name__ == "__main__":
    main()
