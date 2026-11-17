"""Independent read-only export audit; reports never contain matched values."""
from __future__ import annotations

import ast
import collections
import concurrent.futures
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading

sys.path.insert(0, str(Path(__file__).resolve().parent))
import cluster_github_export_audit as base

STAGE = Path(r"D:/project/cluster_github_export_20261117")
OUT = base.OUT
SOURCE = base.ROOT
ENV = dict(os.environ, GIT_OPTIONAL_LOCKS="0", GIT_TERMINAL_PROMPT="0")
CACHE_FILE = OUT / "final_export_content_scan_cache.json"
WEIGHT_EXT = {".pt", ".pth", ".ckpt", ".safetensors", ".onnx", ".h5", ".hdf5",
              ".pkl", ".pickle", ".npy", ".npz", ".pb", ".bin"}
CODE_EXT = base.SOURCE_EXT | {".vbs"}
MORE_PATTERNS = [
    ("huggingface_token", "high", re.compile(r"\bhf_[A-Za-z0-9]{25,255}\b")),
    ("npm_token", "high", re.compile(r"\bnpm_[A-Za-z0-9]{30,255}\b")),
    ("pypi_token", "high", re.compile(r"\bpypi-AgEI[A-Za-z0-9_-]{30,255}\b")),
]
UNQUOTED = re.compile(
    r"""(?im)^\s*(?:export\s+)?
    (?P<key>[A-Za-z0-9_]*(?:password|passwd|pwd|secret|api_key|apikey|
    access_token|auth_token|github_token|hf_token|wandb_api_key)[A-Za-z0-9_]*)
    \s*[:=]\s*(?P<value>[^\s"'#<>]+)""", re.X
)
CACHE_VERSION = 2
lock = threading.Lock()
cache = {}
if CACHE_FILE.exists():
    loaded = json.loads(CACHE_FILE.read_text(encoding="utf-8"))
    if loaded.get("version") == CACHE_VERSION:
        cache = loaded["contents"]


def git(*args, data=None, repo=STAGE):
    p = subprocess.run(
        ["git", "-c", "safe.directory=*", "-C", str(repo), *args],
        input=data, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV,
    )
    if p.returncode:
        raise RuntimeError("Read-only Git command failed: " + args[0])
    return p.stdout


def refs():
    data = git("for-each-ref", "--format=%(refname) %(objectname)", "refs/heads")
    return dict(line.split(" ", 1) for line in data.decode().splitlines())


def scan_text(text):
    hits = base.scan_text(text)
    for lineno, line in enumerate(text.splitlines(), 1):
        for kind, confidence, pattern in MORE_PATTERNS:
            if pattern.search(line):
                hits.append({"line": lineno, "type": kind, "confidence": confidence})
    for m in UNQUOTED.finditer(text):
        value = m.group("value").rstrip(",;")
        if len(value) < 4 or base.PLACEHOLDER.search(value):
            continue
        if any(c in value for c in "$(){}[]\\") or value.startswith(("/", "./", "../", "~", "_")):
            continue
        if value.lower() in {"true", "false", "none", "null", "str", "string", "bytes", "int",
                             "self.", "settings.", "config.", "getenv", "getpass"}:
            continue
        if re.fullmatch(r"[A-Z][A-Z0-9_]*", value) or value.endswith((".", ":")):
            continue
        if "." in value and re.fullmatch(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+", value):
            continue
        key = m.group("key").lower()
        kind = "unquoted_password_literal" if any(x in key for x in ("password", "passwd", "pwd")) else "unquoted_secret_or_token_literal"
        hits.append({"line": text.count("\n", 0, m.start()) + 1,
                     "type": kind, "confidence": "candidate"})
    return sorted({(x["line"], x["type"], x["confidence"]): x for x in hits}.values(),
                  key=lambda x: (x["line"], x["type"]))


def classify(data, force_text=False):
    sha = hashlib.sha256(data).hexdigest()
    with lock:
        item = cache.get(sha)
    if item is None or (force_text and not item["text"]):
        text = base.decode_text(data)
        if text is None and force_text:
            if data.startswith((b"\xff\xfe", b"\xfe\xff")):
                text = data.decode("utf-16", errors="replace")
            else:
                text = data.decode("utf-8", errors="replace").replace("\x00", "")
        item = {"bytes": len(data), "text": text is not None,
                "findings": scan_text(text) if text is not None else []}
        with lock:
            cache[sha] = item
    return sha, item


def inventory():
    out = {}
    for directory, dirs, files in os.walk(STAGE, followlinks=False):
        dirs[:] = [d for d in dirs if d != ".git"]
        parent = Path(directory)
        for name in files:
            p = parent / name
            key = p.relative_to(STAGE).as_posix()
            st = p.lstat()
            out[key] = {"bytes": st.st_size, "mtime_ns": st.st_mtime_ns,
                        "symlink": p.is_symlink()}
    return out


def scan_file(item):
    name, meta = item
    if meta["symlink"]:
        return name, {**meta, "sha256": None, "text": False,
                      "findings": [], "read_skipped": "symlink"}
    data = (STAGE / name).read_bytes()
    force_text = Path(name).suffix.lower() in (
        base.TEXT_EXT | {".jsonl", ".diff", ".patch", ".tex", ".bib", ".sty", ".vbs"}
    )
    sha, result = classify(data, force_text=force_text)
    return name, {**meta, "bytes": len(data), "sha256": sha,
                  "text": result["text"], "findings": result["findings"]}


def read_blob(oid, process):
    process.stdin.write((oid + "\n").encode())
    process.stdin.flush()
    header = process.stdout.readline().decode().split()
    data = process.stdout.read(int(header[2]))
    process.stdout.read(1)
    return data


def history_audit(headrefs):
    objects = {}
    raw = git("rev-list", "--objects", *headrefs.values())
    for line in raw.decode("utf-8", "replace").splitlines():
        oid, _, name = line.partition(" ")
        objects.setdefault(oid, name)
    batch = git("cat-file", "--batch-check=%(objectname) %(objecttype) %(objectsize)",
                data=("\n".join(objects) + "\n").encode())
    kinds = collections.Counter()
    sizes = collections.Counter()
    blobs = []
    for line in batch.decode().splitlines():
        oid, kind, size = line.split()
        size = int(size)
        kinds[kind] += 1
        sizes[kind] += size
        if kind == "blob":
            blobs.append({"oid": oid, "representative_path": objects[oid], "bytes": size})
    p = subprocess.Popen(
        ["git", "-c", "safe.directory=*", "-C", str(STAGE), "cat-file", "--batch"],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=ENV,
    )
    hits, binary, manifest = [], [], {}
    text_count = 0
    try:
        for b in blobs:
            data = read_blob(b["oid"], p)
            sha, result = classify(data)
            manifest[b["oid"]] = {"sha256": sha, "bytes": len(data), "text": result["text"]}
            if result["text"]:
                text_count += 1
            else:
                binary.append(b)
            for hit in result["findings"]:
                hits.append({**b, **hit})
    finally:
        p.stdin.close()
        p.wait(timeout=30)
    return {
        "heads": headrefs, "object_counts": dict(kinds), "object_bytes": dict(sizes),
        "unique_blobs": len(blobs), "text_blobs_scanned": text_count,
        "binary_blob_count": len(binary), "binary_blobs": binary,
        "findings": hits, "blobs_gt20MiB": [x for x in blobs if x["bytes"] > 20*1024*1024],
        "blobs_gt100MiB": [x for x in blobs if x["bytes"] > 100*1024*1024],
        "blob_content_manifest": manifest,
    }


def main():
    started = dt.datetime.now(dt.timezone.utc).isoformat()
    begin_refs = refs()
    initial = inventory()
    scanned = {}
    with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
        for start in range(0, len(initial), 256):
            batch = list(initial.items())[start:start+256]
            scanned.update(pool.map(scan_file, batch))
    print(f"Scanned current files: {len(scanned)}", flush=True)
    stable = False
    for attempt in range(3):
        now = inventory()
        changed = {k: v for k, v in now.items() if k not in scanned or
                   v["mtime_ns"] != scanned[k]["mtime_ns"] or v["bytes"] != scanned[k]["bytes"]}
        scanned = {k: v for k, v in scanned.items() if k in now}
        if not changed:
            stable = True
            break
        with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
            scanned.update(pool.map(scan_file, changed.items()))
    final_refs = refs()
    print(f"Scanning history reachable from {len(final_refs)} heads", flush=True)
    hist = history_audit(final_refs)
    end_refs = refs()
    current_hits = [{"path": name, **hit} for name, item in scanned.items() for hit in item["findings"]]
    top = collections.defaultdict(collections.Counter)
    for name, item in scanned.items():
        key = name.split("/")[0]
        top[key]["files"] += 1
        top[key]["bytes"] += item["bytes"]
        top[key]["text_files"] += int(item["text"])
    source_audit = json.loads((OUT / "export_scope_security_audit.json").read_text(encoding="utf-8"))
    ref_integrity = []
    for w in source_audit["worktrees"]:
        if w["path"] == "Cluster":
            name = "refs/heads/archive/local-main-committed-20261117"
        else:
            name = "refs/heads/archive/isolated/" + w["name"]
        ref_integrity.append({"ref": name, "expected": w["head"], "actual": end_refs.get(name),
                              "matches": end_refs.get(name) == w["head"]})
    local_ref = "refs/heads/archive/local-working-20261117"
    expected_dirty = {x["path"]: x for x in source_audit["worktrees"][0]["status_entries"]}
    local_diff = []
    for line in git("diff", "--name-status", source_audit["main_head"], end_refs[local_ref]).decode().splitlines():
        status, name = line.split("\t", 1)
        local_diff.append({"status": status, "path": name})
    actual_dirty = {x["path"]: x for x in local_diff}
    local_preservation = []
    for name, expected in expected_dirty.items():
        p = SOURCE / "Cluster" / name
        actual = git("show", local_ref + ":" + name)
        raw = p.read_bytes()
        local_preservation.append({
            "path": name, "present_in_archive_diff": name in actual_dirty,
            "source_sha256": hashlib.sha256(raw).hexdigest(),
            "archive_sha256": hashlib.sha256(actual).hexdigest(),
            "byte_identical": actual == raw,
            "normalized_newlines_identical": actual.replace(b"\r\n", b"\n") == raw.replace(b"\r\n", b"\n"),
        })
    baseline = "5413102c57b526035f3920b5e7a81f3b58ad764d"
    main_source_expected, main_source_missing, main_source_changed = 0, [], []
    for rec in git("ls-tree", "-r", "-z", baseline).split(b"\0"):
        if not rec:
            continue
        metadata, rawname = rec.split(b"\t", 1)
        mode, kind, oid = metadata.decode().split()
        name = rawname.decode("utf-8", "replace")
        if kind != "blob" or Path(name).suffix.lower() not in CODE_EXT:
            continue
        main_source_expected += 1
        if name not in scanned:
            main_source_missing.append(name)
        elif scanned[name]["sha256"] != hist["blob_content_manifest"][oid]["sha256"]:
            main_source_changed.append(name)
    main_source_integrity = {
        "baseline": baseline, "source_config_files_expected": main_source_expected,
        "missing": main_source_missing, "byte_different": main_source_changed,
    }
    source_copy_checks = []
    for group in ("configs", "framework", "scripts", "pipeline", "Checkpoints"):
        srcroot = SOURCE / group
        missing, differing, expected_count = [], [], 0
        for directory, dirs, files in os.walk(srcroot):
            parent = Path(directory)
            dirs[:] = [d for d in dirs if d not in base.GENERATED_PARTS and d != "isolated_versions"
                       and (parent/d) != SOURCE/"pipeline/handoffs/20261117_github_migration"]
            for filename in files:
                p = parent / filename
                if p.suffix.lower() not in CODE_EXT:
                    continue
                name = p.relative_to(SOURCE).as_posix()
                expected_count += 1
                destname = "project_support/" + name
                if destname not in scanned:
                    missing.append(name)
                    continue
                digest = hashlib.sha256(p.read_bytes()).hexdigest()
                if scanned[destname]["sha256"] != digest:
                    differing.append(name)
        source_copy_checks.append({"group": group, "source_config_files_expected": expected_count,
                                   "missing": missing, "byte_different": differing})
    tools = []
    for skill in ("songcl_research_pipeline", "songcl_remote_train"):
        srcroot = Path(r"C:/Users/chuanle song/.codex/skills") / skill
        missing, differing, expected_count = [], [], 0
        for directory, dirs, files in os.walk(srcroot):
            dirs[:] = [d for d in dirs if d not in base.GENERATED_PARTS and d != "_task_backup"]
            for filename in files:
                p = Path(directory) / filename
                name = p.relative_to(srcroot).as_posix()
                expected_count += 1
                destname = "tooling/" + skill + "/" + name
                if destname not in scanned:
                    missing.append(name)
                elif hashlib.sha256(p.read_bytes()).hexdigest() != scanned[destname]["sha256"]:
                    differing.append(name)
        tools.append({"skill": skill, "canonical_source": str(srcroot),
                      "expected_files": expected_count, "missing": missing, "byte_different": differing})
    current_large = [{"path": n, "bytes": x["bytes"]} for n, x in scanned.items() if x["bytes"] > 100*1024*1024]
    weight_files = [{"path": n, "bytes": x["bytes"]} for n, x in scanned.items() if Path(n).suffix.lower() in WEIGHT_EXT]
    filenames = [{"path": n, "type": base.sensitive_filename(Path(n))} for n in scanned if base.sensitive_filename(Path(n))]
    report = {
        "audit_started_utc": started,
        "audit_finished_utc": dt.datetime.now(dt.timezone.utc).isoformat(),
        "stage": str(STAGE), "read_only": True,
        "working_tree_scan_stable": stable, "heads_before": begin_refs, "heads_after": end_refs,
        "heads_changed_during_history_scan": end_refs != final_refs,
        "current": {"files": len(scanned), "bytes": sum(x["bytes"] for x in scanned.values()),
                    "text_files_scanned": sum(x["text"] for x in scanned.values()),
                    "unique_content_cache_entries": len(cache),
                    "findings": current_hits, "sensitive_filename_candidates": filenames,
                    "files_gt100MiB": current_large, "weight_or_dataset_artifact_files": weight_files,
                    "top_level_inventory": [{"path": k, **dict(v)} for k, v in sorted(top.items())]},
        "history": hist, "archived_original_head_integrity": ref_integrity,
        "local_working_archive": {"ref": local_ref, "expected_dirty_files": len(expected_dirty),
                                 "actual_diff_files": len(actual_dirty),
                                 "extra_diff_paths": sorted(set(actual_dirty)-set(expected_dirty)),
                                 "file_checks": local_preservation},
        "root_source_copy_integrity": source_copy_checks,
        "integrated_main_source_integrity": main_source_integrity,
        "vendored_tooling_integrity": tools,
        "test_placeholder_review": json.loads((OUT/"test_placeholder_review.json").read_text(encoding="utf-8")),
        "status": "SCAN_COMPLETE_REQUIRES_FINAL_REF_AND_MANIFEST_CONFIRMATION",
        "matched_values_disclosed": False,
        "manifest": {k: {a: b for a, b in v.items() if a not in {"findings", "mtime_ns"}}
                     for k, v in sorted(scanned.items())},
    }
    (OUT/"final_export_security_scan.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    CACHE_FILE.write_text(json.dumps({"version": CACHE_VERSION, "contents": cache}, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    summary = {
        "files": len(scanned), "text_files_scanned": report["current"]["text_files_scanned"],
        "current_findings": current_hits, "history_findings": hist["findings"],
        "history_unique_blobs": hist["unique_blobs"], "history_text_blobs": hist["text_blobs_scanned"],
        "large_current": current_large, "large_history": hist["blobs_gt100MiB"],
        "weight_artifacts": weight_files, "root_integrity": source_copy_checks,
        "integrated_main_source_integrity": main_source_integrity,
        "tooling_integrity": tools,
        "local_archive_extra_diff": report["local_working_archive"]["extra_diff_paths"],
        "local_archive_all_source_preserved": all(x["byte_identical"]
                                                 for x in local_preservation),
        "all_archived_original_heads_match": all(x["matches"] for x in ref_integrity),
        "head_change_during_history_scan": end_refs != final_refs,
    }
    (OUT/"final_export_security_summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
