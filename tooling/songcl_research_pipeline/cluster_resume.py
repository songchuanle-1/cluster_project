"""Fail-closed, full-checkpoint resume for an existing Cluster experiment only."""
import math
import re
from pathlib import Path, PurePosixPath

import source_integrity


def requested(project, task):
    # A dropped path must never turn a proof-bearing resume into a fresh run.
    return Path(project).name == "cluster_project" and any(
        key in task for key in ("resume_from", "resume_authorization",
                                "resume_checkpoint_evidence"))


def validate(project, server, task, gpu):
    """Validate hashed human authorization and a prior CPU checkpoint inspection."""
    import closure
    if not requested(project, task):
        raise ValueError("Cluster resume was not requested")
    gpu_id = str(gpu)
    if (server.get("name") != "server-4" or task.get("server") != "server-4"
            or gpu_id not in ("0", "1") or str(task.get("gpu")) != gpu_id
            or gpu_id not in {str(g) for g in server.get("allowed_gpus", [])}):
        raise ValueError("Cluster resume requires an authorized server-4 GPU0 or GPU1")
    if closure.read(Path(project) / "pipeline/closure_policy.json", {}).get("launcher"):
        raise ValueError("Cluster resume requires the original native launcher")
    checkpoint = task.get("resume_from")
    if (not isinstance(checkpoint, str) or not PurePosixPath(checkpoint).is_absolute()
            or ".." in PurePosixPath(checkpoint).parts
            or str(PurePosixPath(checkpoint)) != checkpoint):
        raise ValueError("Resume checkpoint must be a fixed absolute POSIX path")
    commit = task.get("code_commit", "")
    if not re.fullmatch(r"[0-9a-f]{40}", commit):
        raise ValueError("Invalid admitted resume commit")
    documents = []
    for key in ("resume_authorization", "resume_checkpoint_evidence"):
        entry = task.get(key)
        if not isinstance(entry, dict):
            raise ValueError("Missing " + key)
        document = closure.read(closure.artifact(project, entry), {})
        if not isinstance(document, dict):
            raise ValueError("Invalid " + key)
        documents.append(document)
    authorization, evidence = documents
    expected = dict(schema_version=1, purpose="cluster_native_resume", id=task.get("id"),
                    config=task.get("config"), code_commit=commit, server="server-4",
                    gpu=gpu_id, remote_code_root=server["remote_code_root"],
                    resume_from=checkpoint)
    for document in documents:
        if any(document.get(key) != value for key, value in expected.items()):
            raise ValueError("Resume evidence identity mismatch")
    checksum = authorization.get("checkpoint_sha256", "")
    if (not re.fullmatch(r"[0-9a-f]{64}", str(checksum))
            or evidence.get("checkpoint_sha256") != checksum):
        raise ValueError("Resume checkpoint SHA256 mismatch")
    if (authorization.get("authorization_granted") is not True
            or authorization.get("source") != "human"
            or not isinstance(authorization.get("human_request"), str)
            or not authorization["human_request"].strip()):
        raise ValueError("Explicit human resume authorization required")
    inspection = evidence.get("cpu_inspection", {})
    flags = ("load_succeeded", "model_state_present", "optimizer_state_present",
             "scheduler_state_present", "model_state_nonempty",
             "optimizer_state_nonempty", "scheduler_state_nonempty")
    if (not isinstance(inspection, dict) or inspection.get("map_location") != "cpu"
            or any(inspection.get(key) is not True for key in flags)):
        raise ValueError("Incomplete full-checkpoint CPU inspection")
    meta = inspection.get("meta", {})
    if not isinstance(meta, dict):
        raise ValueError("Invalid resume checkpoint meta")
    for key in ("epoch", "epochs_no_improve"):
        if type(meta.get(key)) is not int or meta[key] < 0:
            raise ValueError("Invalid resume checkpoint " + key)
    best = meta.get("best_miou")
    if (type(best) not in (int, float) or not math.isfinite(best)):
        raise ValueError("Invalid resume checkpoint best_miou")
    return dict(expected, checkpoint_sha256=checksum)


def verify_source(project, code, server, task, gpu, ssh):
    """Read only: verify the admitted old object and the existing remote tree."""
    import closure
    contract = validate(project, server, task, gpu)
    commit = contract["code_commit"]
    if closure.git(code, "rev-parse", commit + "^{commit}") != commit:
        raise ValueError("Admitted resume git object is unavailable")
    policy = closure.read(Path(project) / "pipeline/closure_policy.json", {})
    mappings = [(item["source"], server[item["server_key"]].rstrip("/"))
                for item in policy.get("path_mappings", [])]
    # Includes exact HEAD, tracked source changes, untracked source, and only
    # the existing semantic YAML path mappings. Never synchronize this run.
    source_integrity.verify_git(server, commit, mappings, ssh)
    return contract


def checkpoint_check(contract):
    """Run immediately before Popen; no checkpoint loading or fallback selection."""
    return f"""
checkpoint=pathlib.Path({contract['resume_from']!r})
assert checkpoint.is_file(), 'Resume checkpoint is unavailable'
import hashlib
_digest=hashlib.sha256()
with checkpoint.open('rb') as _stream:
    for _block in iter(lambda: _stream.read(1024*1024), b''):
        _digest.update(_block)
assert _digest.hexdigest()=={contract['checkpoint_sha256']!r}, 'Resume checkpoint SHA256 mismatch'
"""
