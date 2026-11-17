"""Rebind the reviewed PSC activation to a fresh owner; copy source/worker bytes."""
from pathlib import Path
from datetime import datetime, timezone
import copy
import hashlib
import json
import os

ROOT = Path("D:/project/cluster_project")
HERE = Path(__file__).resolve().parent
OLD = ROOT / "pipeline/diagnostic_bundles/tick_0bb87433/psc_current_activation"
NATIVE = HERE / "native"
REVIEW = OLD.parent / "psc_activation_independent_review.json"
TOKEN = "d20ca92f1b654e24ba9cf29f634307b7"
THREAD = "01a159c5-29ab-7a22-ba7f-e79174757253"
CHILD = "01a1b166-dcbf-7d01-b0cb-c85fff644605"
KEYS = ("token", "thread_id", "generated_at", "deadline_at", "context_sha256", "pending_sha256")
SOURCE = "0cccd91c32751d8ea2f9e2d99d031ce23b5ef20d"
PARENT = "d20eb221eff6584b67d4e9b5673559d0e1cb735b"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(path):
    return json.loads(Path(path).read_bytes())


def ref(path):
    return {"path": Path(path).relative_to(ROOT).as_posix(), "sha256": sha(path)}


def guard():
    assert HERE == ROOT / "pipeline/diagnostic_bundles/tick_d20ca92f/psc_current_activation"
    assert os.environ.get("CODEX_THREAD_ID") == CHILD != THREAD
    owner = read(ROOT / "pipeline/headless/.foreground.lockdir/owner.json")
    assert owner["token"] == TOKEN and owner["thread_id"] == THREAD
    assert datetime.now(timezone.utc) < datetime.fromisoformat(owner["deadline_at"])
    assert sha(ROOT / "pipeline/headless/.tick_context.json") == owner["context_sha256"]
    assert sha(ROOT / "pipeline/headless/.tick_context_state.next.json") == owner["pending_sha256"]
    assert sha(ROOT / "SERVERS.yaml") == "6a87d428190d77955500b34d58bff0310eecb13c8b233c7b3e4fd7ef253787a7"
    return {key: owner[key] for key in KEYS}


def save(name, value):
    guard()
    path = (HERE / name).resolve()
    assert path.is_relative_to(HERE.resolve())
    path.parent.mkdir(parents=True, exist_ok=True)
    data = value if isinstance(value, bytes) else (
        value.encode("utf8") if isinstance(value, str) else
        (json.dumps(value, ensure_ascii=False, indent=2) + "\n").encode("utf8"))
    with path.open("xb") as stream:
        stream.write(data)


def once(text, old, new):
    assert text.count(old) == 1, old
    return text.replace(old, new, 1)


def main():
    owner = guard()
    assert sha(OLD / "FROZEN.json") == "e3b9fc778ebee1202a84409bbf100b78c9946dcf209c41487e20c7ad5b1f6bac"
    old_frozen = read(OLD / "FROZEN.json")
    assert all(sha(OLD / name) == digest for name, digest in old_frozen["files"].items())
    assert sha(REVIEW) == "526ba96a53cd6b23b1b3ebac566f03f275a2046ff41ea0b25aa68987215b125f"
    assert read(REVIEW)["passed"] is True
    old_prep, old_native_prep = read(OLD / "preparation.json"), read(OLD / "native/preparation.json")
    old_binding = read(OLD / "current_binding.json")
    assert old_binding["source_commit"] == SOURCE and old_binding["runtime_code_commit"] == PARENT
    assert sha(OLD / "native/worker.py") == "530a5230021fad8d880c37a34c18973b4c556e7dc1536b6c4faaffdd6d6f93d8"
    for name in old_native_prep["prepared_file_hashes"]:
        if name not in ("source_version_binding.json", "manifest_template.json"):
            save("native/" + name, (OLD / "native" / name).read_bytes())
    version = read(OLD / "native/source_version_binding.json")
    version["producer_source_version_binding"] = ref(OLD / "native/source_version_binding.json")
    version["producer_author_provenance_only"] = version["author_provenance_only"]
    version["author_provenance_only"] = {"prepared_under_current_owner": owner, "actual_child_thread": CHILD, "execution_binding": False}
    save("native/source_version_binding.json", version)
    template = read(OLD / "native/manifest_template.json")
    template["source_version_binding_sha256"] = sha(NATIVE / "source_version_binding.json")
    template["diagnostic_files"]["source_version_binding.json"] = sha(NATIVE / "source_version_binding.json")
    save("native/manifest_template.json", template)
    native_prep = copy.deepcopy(old_native_prep)
    native_prep.update(recorded_at=datetime.now(timezone.utc).isoformat(),
                       producer_native_preparation=ref(OLD / "native/preparation.json"),
                       producer_parent_owner_provenance_only=old_native_prep["prepared_under_current_parent_owner_provenance_only"],
                       prepared_under_current_parent_owner_provenance_only={**owner, "execution_binding": False},
                       actual_child_thread=CHILD, source_version_binding=ref(NATIVE / "source_version_binding.json"),
                       manifest_template=ref(NATIVE / "manifest_template.json"),
                       worker=ref(NATIVE / "worker.py"), runtime=ref(NATIVE / "native_runtime.py"))
    native_prep["prepared_file_hashes"] = {name: sha(NATIVE / name) for name in old_native_prep["prepared_file_hashes"]}
    save("native/preparation.json", native_prep)
    for name in ("remote_ops.py", "run_psc_operation.py", "README.md"):
        save(name, (OLD / name).read_bytes())
    local_check = (OLD / "local_software_check.py").read_text(encoding="utf8")
    local_check = local_check.replace("tick_0bb87433", "tick_d20ca92f").replace("0bb874337dde412e98bbbaac369f3370", TOKEN)
    save("local_software_check.py", local_check)
    frozen_refs = old_binding["frozen_packages"] + [
        {**ref(OLD / "FROZEN.json"), "declared_files_verified": len(old_frozen["files"])}]
    producer_refs = old_binding["producer_files"] + [
        ref(OLD / "FROZEN.json"), ref(REVIEW), ref(OLD / "preparation.json"),
        ref(OLD / "current_binding.json"), ref(OLD / "adapter.py"), ref(OLD / "release_template.json")]
    audit = read(OLD / "producer_hash_audit.json")
    audit.update(recorded_at=datetime.now(timezone.utc).isoformat(), owner_provenance_only=owner,
                 actual_author_child_thread_id=CHILD, frozen_packages=frozen_refs,
                 producer_files=producer_refs, reviewed_activation_reused=ref(OLD / "preparation.json"),
                 reviewed_activation_independent_review=ref(REVIEW),
                 no_model_worker_or_protocol_rebuild=True)
    save("producer_hash_audit.json", audit)
    binding = copy.deepcopy(old_binding)
    binding.update(owner=owner, actual_author_child_thread_id=CHILD, frozen_packages=frozen_refs,
                   producer_files=producer_refs, producer_hash_audit=ref(HERE / "producer_hash_audit.json"),
                   reviewed_previous_activation=ref(OLD / "preparation.json"),
                   reviewed_previous_activation_independent_review=ref(REVIEW))
    binding["activation_files"] = {name: sha(HERE / name) for name in old_binding["activation_files"]}
    save("current_binding.json", binding)
    adapter = (OLD / "adapter.py").read_text(encoding="utf8")
    adapter = once(adapter, "PREPARATION_SHA = '" + sha(OLD / "native/preparation.json") + "'",
                   "PREPARATION_SHA = '" + sha(NATIVE / "preparation.json") + "'")
    adapter = once(adapter, "TEMPLATE_SHA = '" + sha(OLD / "native/manifest_template.json") + "'",
                   "TEMPLATE_SHA = '" + sha(NATIVE / "manifest_template.json") + "'")
    adapter = once(adapter, "CURRENT_BINDING_SHA256 = '" + sha(OLD / "current_binding.json") + "'",
                   "CURRENT_BINDING_SHA256 = '" + sha(HERE / "current_binding.json") + "'")
    compile(adapter, "adapter.py", "exec")
    save("adapter.py", adapter)
    release = read(OLD / "release_template.json")
    release.update(native_preparation_sha256=sha(NATIVE / "preparation.json"),
                   manifest_template_sha256=sha(NATIVE / "manifest_template.json"),
                   source_version_binding_sha256=sha(NATIVE / "source_version_binding.json"),
                   source_hashes={name: sha(HERE / name) for name in ("adapter.py", "remote_ops.py")},
                   current_binding=ref(HERE / "current_binding.json"))
    save("release_template.json", release)
    preparation = copy.deepcopy(old_prep)
    preparation.update(recorded_at=datetime.now(timezone.utc).isoformat(), owner_provenance_only=owner,
                       actual_author_child_thread_id=CHILD, native_preparation=ref(NATIVE / "preparation.json"),
                       native_manifest_template=ref(NATIVE / "manifest_template.json"),
                       native_source_version_binding=ref(NATIVE / "source_version_binding.json"),
                       native_worker=ref(NATIVE / "worker.py"), current_binding=ref(HERE / "current_binding.json"),
                       release_template=ref(HERE / "release_template.json"), root_launcher=ref(HERE / "run_psc_operation.py"),
                       original_frozen_packages=frozen_refs, reviewed_previous_activation=ref(OLD / "preparation.json"),
                       reviewed_previous_activation_independent_review=ref(REVIEW),
                       software_validation_output=(HERE / "software_validation.json").relative_to(ROOT).as_posix(),
                       no_model_worker_or_protocol_rebuild=True)
    preparation["prepared_file_hashes"] = {
        name: sha(HERE / name) for name in old_prep["prepared_file_hashes"]}
    save("preparation.json", preparation)
    assert all(sha(OLD / name) == digest for name, digest in old_frozen["files"].items())
    print(json.dumps({"prepared": True, "preparation": ref(HERE / "preparation.json"),
                      "native_preparation": ref(NATIVE / "preparation.json"),
                      "template": ref(NATIVE / "manifest_template.json"),
                      "adapter_release_created": False, "native": "NOT_RUN", "resources": "NOT_RUN"}))


if __name__ == "__main__":
    main()
