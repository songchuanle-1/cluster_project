"""Local metadata-only packet finalization; default NOP; no SSH or imports."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent


def read(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def require(value, message):
    if not value:
        raise RuntimeError(message)


def build_packet(constructor_path, expected_sha, peer_review_sha):
    require(isinstance(peer_review_sha, str) and len(peer_review_sha) == 64,
            "VERIFIED_WRAPPER_PEER_REVIEW_HASH_REQUIRED")
    path = Path(constructor_path).resolve()
    require(path.is_relative_to(HERE.parent), "CONSTRUCTOR_ACTUAL_OUTSIDE_CURRENT_TICK")
    require(sha(path) == expected_sha, "CONSTRUCTOR_ACTUAL_HASH")
    actual = read(path)
    owner = read(HERE.parent / "current_owner_binding.json")
    require(actual.get("owner") == owner and actual.get("certainty") == "terminal" and
            actual.get("returncode") == 0 and actual.get("transport_passed") is True,
            "CONSTRUCTOR_TRANSPORT_NOT_CURRENT_TERMINAL_PASS")
    observed = actual["observation"]
    require(observed.get("owner") == owner and observed.get("constructor_complete") is True and
            observed.get("status") == "CONSTRUCTOR_AND_CACHE_COVERAGE_PASS" and
            observed.get("readonly_helper_uncertain") is not True,
            "CURRENT_CONSTRUCTOR_AND_FULL_CACHE_COVERAGE_PASS_REQUIRED")
    carrier = observed["carrier"]
    require(carrier.get("certainty") == "terminal" and carrier.get("returncode") == 0,
            "CONSTRUCTOR_CARRIER_NOT_TERMINAL_ZERO")
    result_rows = [row for row in carrier["records"] if row.get("stage") == "constructor_result"]
    require(len(result_rows) == 1, "EXACT_CONSTRUCTOR_RESULT_REQUIRED")
    result = result_rows[0]
    require(result.get("missing_key_count") == 0 and result.get("malformed_light_schema_count") == 0 and
            result.get("cuda_initialized") is False and result.get("workers_started") == 0 and
            result.get("samples_fetched") == 0, "CONSTRUCTOR_SCOPE_OR_CACHE_RESULT")
    origins = result["module_origins"]
    require(all(isinstance(value, str) and value for value in origins.values()), "EXACT_MODULE_ORIGINS")
    # These are already constructor-verified source/cache/tokenizer identities,
    # not a large PTH manifest or repeated content hash.
    guarded = []
    provenance = observed["current_source_cache_asset_provenance"]
    pins = read(path.parent / "provenance_pins.json")
    require(pins.get("owner") == owner, "CURRENT_CONSTRUCTOR_PIN_BINDING")
    by_path = {row["path"]: row for row in pins["pins"]}
    for row in provenance:
        pin = by_path[row["path"]]
        guarded.append({"path": row["path"], "resolved": pin["resolved"],
                        "identity": row["stat_identity"]})
    helper_proof = observed["readonly_helper_and_config_source_preflight"]
    # The preflight retains exact path/hash/identity plus platform source.
    policy = helper_proof.get("policy") or helper_proof.get("helper_policy")
    if policy is None:
        # Ops may retain the policy fields directly in its preflight object.
        fields = ("path", "sha256", "identity", "platform_path", "platform_sha256")
        if all(key in helper_proof for key in fields):
            policy = {key: helper_proof[key] for key in fields}
    require(policy is not None, "EXACT_UNAME_POLICY_MISSING_FROM_CONSTRUCTOR_ACTUAL")
    fields = ("path", "sha256", "identity", "platform_path", "platform_sha256")
    require(all(key in policy for key in fields), "INCOMPLETE_UNAME_POLICY")
    ipv6_source = observed.get("urllib3_ipv6_source_before_validation", {})
    ipv6_policy = (observed.get("local_ipv6_probe_policy") or observed.get("ipv6_policy") or
                   ipv6_source.get("policy"))
    if ipv6_policy is None:
        require(ipv6_source.get("path") and len(ipv6_source.get("sha256", "")) == 64 and
                ipv6_source.get("complete_source"), "AUTHENTIC_URLLIB3_IPV6_SOURCE_PROOF_REQUIRED")
        ipv6_policy = {"path": ipv6_source["path"], "sha256": ipv6_source["sha256"],
                       "identity": ipv6_source.get("identity"),
                       "maximum_binds": 1, "address": ["::1", 0],
                       "family": "AF_INET6", "type": "SOCK_STREAM"}
    require(ipv6_policy.get("maximum_binds") == 1 and ipv6_policy.get("address") == ["::1", 0],
            "EXACT_LOOPBACK_ONLY_IPV6_POLICY")
    count = result.get("ipv6_loopback_capability_binds")
    allowed = [row for row in carrier["records"] if row.get("stage") == "allowed_loopback_ipv6_capability_bind"]
    require(count in (0, 1) and len(allowed) == count, "CONSTRUCTOR_IPV6_CAPABILITY_ACCOUNTING")
    if allowed:
        row = allowed[0]
        require(row.get("address") == ["::1", 0] and row.get("source_sha256") == ipv6_policy["sha256"] and
                row.get("listen_connect_send_DNS_allowed") is False,
                "AUTHENTIC_CONSTRUCTOR_LOOPBACK_BIND_RECORD")
    helper_guards = helper_proof.get("guarded_files", [])
    for row in helper_guards:
        if row["path"] not in {entry["path"] for entry in guarded}:
            guarded.append(row)
    require(all(row.get("identity_unchanged") is True
                for row in observed["guarded_file_identity_after_observation"]),
            "CONSTRUCTOR_ASSET_CHANGED_AFTER_PROBE")
    packet = copy.deepcopy(read(HERE / "packet.template.json"))
    packet.update(owner=owner, execution_authorized=True,
                  status="READY_AFTER_ACTUAL_CONSTRUCTOR_AND_PEER_REVIEW",
                  carrier_sha256=sha(HERE / "trace_carrier.py"),
                  constructor_actual_sha256=expected_sha,
                  constructor_status="CONSTRUCTOR_AND_CACHE_COVERAGE_PASS",
                  peer_review_sha256=peer_review_sha,
                  capacity_admitted=True, capacity_observation_sha256=expected_sha,
                  guarded_files=guarded, expected_module_origins=origins,
                  readonly_helper_policy=policy, local_ipv6_probe_policy=ipv6_policy)
    packet.update(min_mem_available_kib=64 * 1024 * 1024,
                  min_shm_available_bytes=16 * 1024 ** 3,
                  min_cgroup_memory_headroom_bytes=64 * 1024 ** 3,
                  max_total_rss_kib=64 * 1024 * 1024)
    packet["capacity_scope"] = (
        "One standalone CPU diagnostic: current host and each finite cgroup memory headroom>=64GiB, "
        "sharing free>=16GiB, affinity>=4 CPUs, ancestor pids headroom>=8. "
        "Fresh supervisor measurements precede carrier start; no GPU/model/training admission.")
    return packet


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--constructor-actual", type=Path)
    parser.add_argument("--constructor-sha256")
    parser.add_argument("--peer-review-sha256")
    args = parser.parse_args()
    if not args.prepare:
        print(json.dumps({"status": "DEFAULT_NOP_NO_READINESS_OR_EXECUTION"}))
        return
    packet = build_packet(args.constructor_actual, args.constructor_sha256, args.peer_review_sha256)
    destination = HERE / "packet.prepared.json"
    with destination.open("x", encoding="utf-8", newline="\n") as output:
        json.dump(packet, output, indent=2)
        output.write("\n")
    print(json.dumps({"path": str(destination), "sha256": sha(destination), "SSH_executed": False}))


if __name__ == "__main__":
    main()
