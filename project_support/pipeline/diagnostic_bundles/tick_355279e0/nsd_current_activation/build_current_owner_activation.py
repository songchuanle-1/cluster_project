"""Separate metadata-only owner activation; root release and execution excluded."""
from pathlib import Path
from datetime import datetime, timezone
import hashlib
import json
import os
import sys

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_f74f3603/nsd_current_activation"
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
TOKEN = "355279e0b7b14943aa7b6060b58d63f0"
AUTHOR = "01a1b6ff-4235-7741-943b-732c0abb417d"


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p):
    return json.loads(Path(p).read_bytes())


def ref(p):
    return {"path": Path(p).relative_to(ROOT).as_posix(), "sha256": sha(p)}


def guard():
    assert os.environ.get("CODEX_THREAD_ID") == AUTHOR
    assert sys.dont_write_bytecode and os.environ.get("PYTHONDONTWRITEBYTECODE") == "1"
    o = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    owner = {k: o[k] for k in KEYS}
    assert owner["token"] == TOKEN and owner["thread_id"] == "01a159c5-29ab-7a22-ba7f-e79174757253"
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    return owner


def save(name, value):
    guard()
    p = HERE / name
    assert p.resolve().is_relative_to(HERE.resolve())
    p.parent.mkdir(parents=True, exist_ok=True)
    raw = value if isinstance(value, bytes) else (value.encode() if isinstance(value, str)
          else (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode())
    with p.open("xb") as stream:
        stream.write(raw)


def main():
    owner = guard()
    assert sha(OLD / "FROZEN.json") == "c6f26d1150ac37ca2542a85b08b86287ea34c6661881df92fe2b208f805e3a03"
    assert all(sha(OLD / n) == h for n, h in read(OLD / "FROZEN.json")["files"].items())
    review = OLD.parent / "nsd_activation_independent_review.json"
    assert sha(review) == "16d940e5ecec734fafa390631e9b0d36614535a3af63adcdf27080ff56e598bb"
    assert read(review)["passed"] is True
    old_binding = read(OLD / "current_binding.json")
    for name, digest in old_binding["activation_files"].items():
        assert sha(OLD / name) == digest
        save(name, (OLD / name).read_bytes())
    binding = {**old_binding, "owner": owner}
    save("current_binding.json", binding)
    old_anchor = "CURRENT_BINDING_SHA256 = '" + sha(OLD / "current_binding.json") + "'"
    new_anchor = "CURRENT_BINDING_SHA256 = '" + sha(HERE / "current_binding.json") + "'"
    adapter = (OLD / "adapter.py").read_bytes().decode()
    assert adapter.count(old_anchor) == 1
    save("adapter.py", adapter.replace(old_anchor, new_anchor, 1))
    release = read(OLD / "release_template.json")
    release["current_binding"] = ref(HERE / "current_binding.json")
    release["source_hashes"] = {n: sha(HERE / n) for n in ("adapter.py", "remote_ops.py")}
    save("release_template.json", release)
    save("README.md", "Separate current-owner NSD metadata activation. Reuses exact reviewed f74f3603 native packet, source f625/parent-runtime0ccc, corrected operational v2, original protocol and1020sec run margin. Native source-version/preparation owner fields are historical author provenance only, copied byte-for-byte; current_binding.owner alone binds the live owner. No root release, execution binding/lease/manifest/request, prepare intent, stage or actual execution is created. Root must independently review, anchor and resource-check before its original operations. Original diagnostic-only immutable conda base6c80 retained; old expired production shim/SERVERS and every old artifact remain untouched.\n")
    names = ["build_current_owner_activation.py", "owner_sanity.py", "current_binding.json",
             "adapter.py", "release_template.json", "README.md"] + list(binding["activation_files"])
    save("change_manifest.json", {
        "recorded_at": datetime.now(timezone.utc).isoformat(), "author_actual_child_thread": AUTHOR,
        "owner": owner, "reused_reviewed_activation": ref(OLD / "FROZEN.json"),
        "reused_independent_review": ref(review),
        "binding_changed_fields_only": ["owner." + k for k in KEYS],
        "adapter_changed_fields_only": ["CURRENT_BINDING_SHA256"],
        "release_changed_fields_only": ["current_binding.path", "current_binding.sha256", "source_hashes.adapter.py"],
        "native_remote_launcher_unchanged": binding["activation_files"],
        "native_owner_fields_remain_historical_provenance_only": True,
        "root_release_execution_metadata_prepare_intent_created": False})
    names.append("change_manifest.json")
    old_p = read(OLD / "preparation.json")
    p = {**old_p, "recorded_at": datetime.now(timezone.utc).isoformat(),
         "owner_provenance_only": owner, "reused_reviewed_activation": ref(OLD / "FROZEN.json"),
         "native_preparation": ref(HERE / "native/preparation.json"),
         "native_manifest_template": ref(HERE / "native/manifest_template.json"),
         "current_binding": ref(HERE / "current_binding.json"),
         "release_template": ref(HERE / "release_template.json"),
         "root_launcher": ref(HERE / "run_nsd_operation.py"),
         "prepared_file_hashes": {n: sha(HERE / n) for n in names}}
    save("preparation.json", p)
    print(json.dumps({"preparation": ref(HERE / "preparation.json"),
                      "current_binding": ref(HERE / "current_binding.json"),
                      "native_unchanged": True, "root_release_created": False}))


if __name__ == "__main__":
    main()
