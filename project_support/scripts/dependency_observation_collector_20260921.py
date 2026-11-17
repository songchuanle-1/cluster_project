"""Collect the static dependency observation contract without model imports.

This module is intentionally stdlib-only so it can be copied to the authorized
server-4 environment. It reads package metadata, module files and ELF headers;
it does not import the nine declared packages, load the native extension, run a
test, allocate a GPU or establish ABI/loader compatibility.
"""
import argparse
import ast
import hashlib
import importlib.metadata
import importlib.machinery
import json
import math
import os
from pathlib import Path, PurePosixPath
import platform
import re
import struct
import subprocess
import sys
import sysconfig
import time


PLAN_CONTRACT = "installed-dependency-collection-plan-v1"
OBSERVATION_CONTRACT = "installed-dependency-observation-v1"
NATIVE_EXTENSION = "pointgroup_ops.pointgroup_ops_ext"
DIRECT_PACKAGES = frozenset({
    "dgl", "gorilla", "numpy", "scipy", "sng_parser", "torch",
    "torch_scatter", "tqdm", "transformers",
})
DISTRIBUTION_CANDIDATES = {
    "sng_parser": ("sng-parser", "sng_parser"),
    "torch_scatter": ("torch-scatter", "torch_scatter"),
}
PLAN_KEYS = frozenset({
    "contract", "roots", "bootstrap", "cuda_version",
    "extension_artifact", "distribution_overrides", "library_overrides",
})
ROOT_KEYS = frozenset({
    "conda_source", "environment_root", "site_packages", "code_root",
    "data_root", "work_root",
})
MAX_PLAN_BYTES = 1024 * 1024
ELF_CLASS = {1: "ELF32", 2: "ELF64"}
ELF_DATA = {1: "little", 2: "big"}
ELF_MACHINE = {
    3: "Intel 80386",
    8: "MIPS",
    20: "PowerPC",
    21: "PowerPC64",
    40: "ARM",
    62: "Advanced Micro Devices X86-64",
    183: "AArch64",
    243: "RISC-V",
}


def _strict_json(raw):
    def unique_object(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    def invalid_constant(value):
        raise ValueError("Nonfinite JSON value: " + value)

    if isinstance(raw, bytes):
        raw = raw.decode("ascii")
    return json.loads(raw, object_pairs_hook=unique_object,
                      parse_constant=invalid_constant)


def _exact_object(value, keys, label):
    if not isinstance(value, dict) or set(value) != set(keys):
        raise ValueError("Invalid " + label + " schema")
    return value


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonempty " + label + " required")
    return value


def _normalized_distribution_name(value):
    return re.sub(r"[-_.]+", "-", value).lower()


def _canonical_absolute(value, label):
    if (not isinstance(value, str) or not value
            or "\\" in value or ":" in value):
        raise ValueError("Canonical absolute POSIX " + label + " required")
    path = PurePosixPath(value)
    if (not path.is_absolute() or str(path) != value
            or any(part in ("", ".", "..") for part in path.parts)):
        raise ValueError("Canonical absolute POSIX " + label + " required")
    return value


def _resolve_path(value, label, directory=False):
    canonical = _canonical_absolute(value, label)
    path = Path(canonical)
    if not path.is_absolute():
        raise ValueError("Absolute " + label + " required")
    resolved = path.resolve(strict=True)
    if directory and not resolved.is_dir():
        raise ValueError(label + " is not a directory")
    if not directory and not resolved.is_file():
        raise ValueError(label + " is not a regular file")
    if any(part in ("", ".", "..") for part in resolved.parts):
        raise ValueError("Noncanonical resolved " + label)
    return resolved


def _sha256(path):
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _file_row(value, label):
    path = _resolve_path(value, label)
    return {"path": str(path), "sha256": _sha256(path)}


def _directory_path(value, label):
    return str(_resolve_path(value, label, directory=True))


def _validate_plan(plan):
    plan = _exact_object(plan, PLAN_KEYS, "collection plan")
    if plan["contract"] != PLAN_CONTRACT:
        raise ValueError("Unsupported collection plan contract")
    roots = _exact_object(plan["roots"], ROOT_KEYS, "collection roots")
    for key in ("environment_root", "code_root", "data_root", "work_root"):
        _canonical_absolute(roots[key], key)
    _canonical_absolute(roots["conda_source"], "conda source")
    if (not isinstance(roots["site_packages"], list)
            or not roots["site_packages"]):
        raise ValueError("Nonempty site-packages plan required")
    for path in roots["site_packages"]:
        _canonical_absolute(path, "site-packages root")
    if len(set(roots["site_packages"])) != len(roots["site_packages"]):
        raise ValueError("Duplicate site-packages root")

    bootstrap = plan["bootstrap"]
    if not isinstance(bootstrap, list) or not bootstrap:
        raise ValueError("Nonempty bootstrap plan required")
    names = set()
    for row in bootstrap:
        _exact_object(row, {"name", "path"}, "bootstrap plan row")
        name = _text(row["name"], "bootstrap module")
        if any(not part.isidentifier() for part in name.split(".")):
            raise ValueError("Invalid bootstrap module name")
        if name in names:
            raise ValueError("Duplicate bootstrap module")
        names.add(name)
        _canonical_absolute(row["path"], "bootstrap module path")

    overrides = plan["distribution_overrides"]
    if not isinstance(overrides, dict):
        raise ValueError("Distribution overrides must be an object")
    if not set(overrides).issubset(DIRECT_PACKAGES):
        raise ValueError("Unknown distribution override import root")
    for key, value in overrides.items():
        _text(value, "distribution override for " + key)

    libraries = plan["library_overrides"]
    if not isinstance(libraries, dict):
        raise ValueError("Library overrides must be an object")
    for soname, path in libraries.items():
        _text(soname, "shared-library soname")
        _canonical_absolute(path, "shared-library override")

    _text(plan["cuda_version"], "CUDA version")
    _canonical_absolute(plan["extension_artifact"], "extension artifact")
    return plan


def load_plan(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_PLAN_BYTES:
        raise ValueError("Collection plan is too large")
    return _validate_plan(_strict_json(raw))


def _module_spec(import_root, site_packages):
    spec = importlib.machinery.PathFinder.find_spec(
        import_root, [str(path) for path in site_packages])
    if spec is None or not spec.origin:
        raise ValueError("Module file not found: " + import_root)
    return spec


def _distribution_for(import_root, site_packages, overrides):
    requested = overrides.get(import_root)
    names = ((requested,) if requested else
             DISTRIBUTION_CANDIDATES.get(import_root, (import_root,)))
    requested_names = {_normalized_distribution_name(name) for name in names}
    matches = []
    seen = set()
    for site in site_packages:
        for distribution in importlib.metadata.distributions(path=[str(site)]):
            name = distribution.metadata.get("Name")
            if not name:
                continue
            normalized = _normalized_distribution_name(name)
            identity = (normalized, str(distribution.locate_file("")), distribution.version)
            if normalized in requested_names and identity not in seen:
                seen.add(identity)
                matches.append(distribution)
    if len(matches) != 1:
        raise ValueError(
            "Expected one distribution for %s, found %d" % (
                import_root, len(matches)))
    return matches[0]


def _collect_packages(roots, overrides):
    site_packages = [
        _resolve_path(path, "site-packages root", directory=True)
        for path in roots["site_packages"]
    ]
    rows = []
    for import_root in sorted(DIRECT_PACKAGES):
        distribution = _distribution_for(
            import_root, site_packages, overrides)
        spec = _module_spec(import_root, site_packages)
        module = _file_row(spec.origin, import_root + " module")
        metadata_entries = [
            entry for entry in (distribution.files or [])
            if entry.name == "METADATA"
        ]
        if len(metadata_entries) != 1:
            raise ValueError(
                "Expected one METADATA file for " + import_root)
        metadata_path = distribution.locate_file(metadata_entries[0])
        metadata = _file_row(str(metadata_path), import_root + " metadata")
        rows.append(dict(
            import_root=import_root,
            distribution=distribution.metadata["Name"],
            version=distribution.version,
            module=module,
            metadata=metadata))
    return rows


def _read_int(data, offset, width, byte_order):
    if offset < 0 or offset + width > len(data):
        raise ValueError("Truncated ELF structure")
    return int.from_bytes(data[offset:offset + width], byte_order)


def inspect_elf(data):
    """Return ELF identity and DT_NEEDED strings without executing the file."""
    if not isinstance(data, bytes) or len(data) < 64:
        raise ValueError("Truncated ELF file")
    if data[:4] != b"\x7fELF":
        raise ValueError("Invalid ELF magic")
    elf_class = ELF_CLASS.get(data[4])
    byte_order = ELF_DATA.get(data[5])
    if elf_class is None or byte_order is None:
        raise ValueError("Unsupported ELF class or byte order")
    machine = ELF_MACHINE.get(
        _read_int(data, 18, 2, byte_order), "Unknown ELF machine")

    if elf_class == "ELF32":
        section_offset = _read_int(data, 32, 4, byte_order)
        section_size = _read_int(data, 46, 2, byte_order)
        section_count = _read_int(data, 48, 2, byte_order)
        dynamic_format = "IIIIIIIIII"
        dynamic_default_size = 8
        address_size = 4
    else:
        section_offset = _read_int(data, 40, 8, byte_order)
        section_size = _read_int(data, 58, 2, byte_order)
        section_count = _read_int(data, 60, 2, byte_order)
        dynamic_format = "IIQQQQIIQQ"
        dynamic_default_size = 16
        address_size = 8
    if section_size < struct.calcsize(dynamic_format) or section_count <= 0:
        raise ValueError("ELF section table unavailable")

    sections = []
    struct_prefix = "<" if byte_order == "little" else ">"
    for index in range(section_count):
        offset = section_offset + index * section_size
        if offset + section_size > len(data):
            raise ValueError("Truncated ELF section table")
        sections.append(struct.unpack_from(
            struct_prefix + dynamic_format, data, offset))
    dynamic_sections = [section for section in sections if section[1] == 6]
    if len(dynamic_sections) != 1:
        raise ValueError("Expected one ELF dynamic section")
    dynamic = dynamic_sections[0]
    dynamic_offset, dynamic_size = dynamic[4], dynamic[5]
    string_index, entry_size = dynamic[6], dynamic[9]
    if not 0 <= string_index < len(sections):
        raise ValueError("Invalid ELF dynamic string-table index")
    string_section = sections[string_index]
    string_offset, string_size = string_section[4], string_section[5]
    if string_offset + string_size > len(data):
        raise ValueError("Truncated ELF string table")
    string_table = data[string_offset:string_offset + string_size]
    if entry_size == 0:
        entry_size = dynamic_default_size
    if entry_size < dynamic_default_size or dynamic_size % entry_size:
        raise ValueError("Invalid ELF dynamic entry size")

    needed = []
    for offset in range(dynamic_offset, dynamic_offset + dynamic_size, entry_size):
        if offset + entry_size > len(data):
            raise ValueError("Truncated ELF dynamic entries")
        tag = _read_int(data, offset, address_size, byte_order)
        value = _read_int(data, offset + address_size, address_size, byte_order)
        if tag == 0:
            break
        if tag != 1:
            continue
        if value >= len(string_table):
            raise ValueError("Invalid DT_NEEDED string offset")
        end = string_table.find(b"\0", value)
        if end < 0:
            raise ValueError("Unterminated DT_NEEDED string")
        try:
            name = string_table[value:end].decode("ascii")
        except UnicodeDecodeError as error:
            raise ValueError("Non-ASCII DT_NEEDED string") from error
        if not name:
            raise ValueError("Empty DT_NEEDED string")
        needed.append(name)
    if not needed or len(set(needed)) != len(needed):
        raise ValueError("Nonempty unique ELF DT_NEEDED entries required")
    return dict(
        class_=elf_class,
        byte_order=byte_order,
        machine=machine,
        declared_needed=sorted(needed))


def read_elf(path):
    return inspect_elf(Path(path).read_bytes())


def parse_ldconfig(output):
    rows = []
    pattern = re.compile(r"^\s*(\S+)\s+\([^)]*\)\s+=>\s+(\S+)\s*$")
    for line in output.splitlines():
        match = pattern.match(line)
        if match:
            rows.append(dict(soname=match.group(1), path=match.group(2)))
    return rows


def read_ldconfig_cache():
    executable = None
    for candidate in ("/sbin/ldconfig", "/usr/sbin/ldconfig", "ldconfig"):
        try:
            result = subprocess.run(
                [candidate, "-p"], check=True, capture_output=True,
                text=True, timeout=15)
        except (FileNotFoundError, subprocess.SubprocessError):
            continue
        executable = candidate
        break
    if executable is None:
        raise ValueError("ldconfig cache query unavailable")
    return parse_ldconfig(result.stdout)


def _visible_devices(environ):
    value = environ.get("CUDA_VISIBLE_DEVICES")
    if value is None:
        raise ValueError("CUDA_VISIBLE_DEVICES must be observed")
    devices = [part.strip() for part in value.split(",") if part.strip()]
    if not devices or len(set(devices)) != len(devices):
        raise ValueError("Unique visible CUDA device identities required")
    return devices


def _cache_candidates(needed, overrides, cache_reader):
    observed = cache_reader()
    if not isinstance(observed, list):
        raise ValueError("Shared-library cache reader returned invalid rows")
    indexed = {}
    for row in observed:
        _exact_object(row, {"soname", "path"}, "shared-library cache row")
        soname = _text(row["soname"], "shared-library cache soname")
        indexed.setdefault(soname, []).append(row["path"])
    rows = []
    for soname in sorted(needed):
        candidates = (
            [overrides[soname]] if soname in overrides
            else indexed.get(soname, []))
        if not candidates:
            raise ValueError("Missing shared-library cache candidate: " + soname)
        rows.append(dict(
            soname=soname,
            **_file_row(candidates[0], "shared-library candidate")))
    return rows


def collect_observation(plan, environ=None, elf_reader=read_elf,
                        cache_reader=read_ldconfig_cache):
    """Collect one complete observation; never import a declared package."""
    plan = _validate_plan(plan)
    environ = os.environ if environ is None else environ
    roots = plan["roots"]
    packages = _collect_packages(roots, plan["distribution_overrides"])
    torch_package = next(row for row in packages if row["import_root"] == "torch")

    extension = _file_row(
        plan["extension_artifact"], "native extension artifact")
    elf = elf_reader(str(_resolve_path(
        plan["extension_artifact"], "native extension artifact")))
    _exact_object(
        elf, {"class_", "byte_order", "machine", "declared_needed"},
        "ELF observation")
    needed = elf["declared_needed"]
    if (not isinstance(needed, list) or not needed
            or any(not isinstance(value, str) or not value for value in needed)):
        raise ValueError("Nonempty ELF DT_NEEDED observations required")
    needed = sorted(needed)
    if len(set(needed)) != len(needed):
        raise ValueError("Duplicate ELF DT_NEEDED observations")
    candidates = _cache_candidates(
        needed, plan["library_overrides"], cache_reader)

    bootstrap = []
    for row in plan["bootstrap"]:
        bootstrap.append(dict(
            name=row["name"],
            **_file_row(row["path"], row["name"] + " bootstrap module")))
    return dict(
        contract=OBSERVATION_CONTRACT,
        observed_at=time.time(),
        runtime=dict(
            executable=_file_row(sys.executable, "runtime executable"),
            python=dict(
                version=platform.python_version(),
                soabi=_text(sysconfig.get_config_var("SOABI") or "", "Python SOABI"),
                platform=platform.platform()),
            torch=dict(
                version=torch_package["version"],
                module=torch_package["module"]),
            cuda=dict(
                version=plan["cuda_version"],
                visible_devices=_visible_devices(environ))),
        roots=dict(
            conda_source=_file_row(roots["conda_source"], "conda source"),
            environment_root=_directory_path(
                roots["environment_root"], "environment root"),
            site_packages=[
                _directory_path(path, "site-packages root")
                for path in roots["site_packages"]],
            code_root=_directory_path(roots["code_root"], "code root"),
            data_root=_directory_path(roots["data_root"], "data root"),
            work_root=_directory_path(roots["work_root"], "work root")),
        bootstrap=bootstrap,
        packages=packages,
        extension=dict(
            module=NATIVE_EXTENSION,
            artifact=extension,
            elf=dict(
                **{"class": elf["class_"]},
                byte_order=elf["byte_order"],
                machine=elf["machine"]),
            declared_needed=needed,
            cache_candidates=candidates))


def write_observation(observation, output_path):
    output = Path(output_path).absolute()
    if (output.exists() or output.is_symlink()
            or any(parent.is_symlink() for parent in output.parents)
            or not output.parent.is_dir()):
        raise ValueError("Canonical fresh observation path required")
    encoded = json.dumps(
        observation, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")
    descriptor = os.open(
        output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink(missing_ok=True)
        raise
    return output, hashlib.sha256(encoded).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--plan", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    plan = load_plan(args.plan)
    observation = collect_observation(plan)
    output, sha256 = write_observation(observation, args.output)
    print("%s %s" % (output, sha256))


if __name__ == "__main__":
    main()
