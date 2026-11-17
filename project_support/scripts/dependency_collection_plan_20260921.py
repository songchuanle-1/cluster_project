"""Materialize a bounded dependency collection plan in the target runtime.

The seed contains only explicit, authorized roots and repository-relative
bootstrap/extension identities. The target interpreter supplies its own
environment root, site-packages roots and extension suffix. No package is
imported and no target artifact is described as observed until the separate
collector runs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import sys
import sysconfig
import time

from dependency_observation_collector_20260921 import (
    PLAN_CONTRACT,
    _canonical_absolute,
    _exact_object,
    _strict_json,
    _validate_plan,
)


SEED_CONTRACT = "installed-dependency-collection-seed-v1"
MAX_SEED_BYTES = 1024 * 1024
SEED_KEYS = frozenset({
    "contract", "roots", "bootstrap", "cuda_version",
    "extension_relative_dir", "extension_stem",
    "distribution_overrides", "library_overrides",
})
SEED_ROOT_KEYS = frozenset({
    "conda_source", "code_root", "data_root", "work_root",
})


def _text(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError("Nonempty " + label + " required")
    return value


def _relative_path(value, label):
    value = _text(value, label)
    if "\\" in value:
        raise ValueError("POSIX-relative " + label + " required")
    path = PurePosixPath(value)
    if (path.is_absolute() or str(path) != value
            or any(part in ("", ".", "..") for part in path.parts)):
        raise ValueError("Canonical POSIX-relative " + label + " required")
    return value


def _real_existing(value, label, directory=False):
    if directory and not os.path.isdir(value):
        raise ValueError(label + " is not a directory")
    if not directory and not os.path.isfile(value):
        raise ValueError(label + " is not a regular file")
    resolved = os.path.realpath(value)
    if not os.path.isabs(resolved):
        raise ValueError("Absolute " + label + " required")
    return resolved


def _inside(path, root):
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


def _load_seed(path):
    raw = Path(path).read_bytes()
    if len(raw) > MAX_SEED_BYTES:
        raise ValueError("Collection seed is too large")
    seed = _strict_json(raw)
    seed = _exact_object(seed, SEED_KEYS, "collection seed")
    if seed["contract"] != SEED_CONTRACT:
        raise ValueError("Unsupported collection seed contract")

    roots = _exact_object(seed["roots"], SEED_ROOT_KEYS, "seed roots")
    normalized_roots = {}
    for key in ("conda_source", "code_root", "data_root", "work_root"):
        normalized_roots[key] = _canonical_absolute(roots[key], key)

    bootstrap = seed["bootstrap"]
    if not isinstance(bootstrap, list) or not bootstrap:
        raise ValueError("Nonempty bootstrap seed required")
    normalized_bootstrap = []
    names = set()
    for row in bootstrap:
        row = _exact_object(row, {"name", "relative_path"}, "bootstrap seed")
        name = _text(row["name"], "bootstrap module")
        if any(not part.isidentifier() for part in name.split(".")):
            raise ValueError("Invalid bootstrap module name")
        if name in names:
            raise ValueError("Duplicate bootstrap module")
        names.add(name)
        normalized_bootstrap.append(dict(
            name=name,
            relative_path=_relative_path(
                row["relative_path"], "bootstrap path")))

    overrides = {
        "distribution_overrides": seed["distribution_overrides"],
        "library_overrides": seed["library_overrides"],
    }
    if not isinstance(overrides["distribution_overrides"], dict):
        raise ValueError("Distribution overrides must be an object")
    if not isinstance(overrides["library_overrides"], dict):
        raise ValueError("Library overrides must be an object")
    for key, value in overrides["distribution_overrides"].items():
        _text(key, "distribution override import root")
        _text(value, "distribution override")
    for soname, value in overrides["library_overrides"].items():
        _text(soname, "shared-library soname")
        _canonical_absolute(value, "shared-library override")

    return dict(
        contract=SEED_CONTRACT,
        roots=normalized_roots,
        bootstrap=normalized_bootstrap,
        cuda_version=_text(seed["cuda_version"], "CUDA version"),
        extension_relative_dir=_relative_path(
            seed["extension_relative_dir"], "extension directory"),
        extension_stem=_text(seed["extension_stem"], "extension stem"),
        **overrides)


def build_plan(seed, prefix=None, purelib=None, platlib=None,
               ext_suffix=None):
    """Return the exact plan consumed by the stdlib-only observation collector."""
    if seed.get("contract") != SEED_CONTRACT:
        raise ValueError("Invalid collection seed contract")
    prefix = _real_existing(
        sys.prefix if prefix is None else prefix,
        "Python environment root", directory=True)
    purelib = _real_existing(
        sysconfig.get_paths()["purelib"] if purelib is None else purelib,
        "purelib root", directory=True)
    platlib = _real_existing(
        sysconfig.get_paths()["platlib"] if platlib is None else platlib,
        "platlib root", directory=True)
    site_packages = []
    for value in (purelib, platlib):
        if not _inside(value, prefix):
            raise ValueError("Site-packages root escapes environment root")
        if value not in site_packages:
            site_packages.append(value)
    if not site_packages:
        raise ValueError("Nonempty site-packages roots required")

    roots = seed["roots"]
    code_root = _real_existing(
        roots["code_root"], "code root", directory=True)
    data_root = _real_existing(
        roots["data_root"], "data root", directory=True)
    work_root = _real_existing(
        roots["work_root"], "work root", directory=True)
    conda_source = _real_existing(
        roots["conda_source"], "conda source")
    if len({code_root, data_root, work_root}) != 3:
        raise ValueError("Code, data and work roots must be distinct")

    bootstrap = []
    for row in seed["bootstrap"]:
        candidate = os.path.realpath(os.path.join(
            code_root, *PurePosixPath(row["relative_path"]).parts))
        if not _inside(candidate, code_root):
            raise ValueError("Bootstrap path escapes code root")
        candidate = _real_existing(
            candidate, row["name"] + " bootstrap module")
        bootstrap.append(dict(name=row["name"], path=candidate))

    extension_root = os.path.realpath(os.path.join(
        code_root, *PurePosixPath(
            seed["extension_relative_dir"]).parts))
    if not _inside(extension_root, code_root):
        raise ValueError("Extension directory escapes code root")
    extension_root = _real_existing(
        extension_root, "extension directory", directory=True)
    suffix = _text(
        sysconfig.get_config_var("EXT_SUFFIX") if ext_suffix is None
        else ext_suffix,
        "Python extension suffix")
    extension = os.path.realpath(os.path.join(
        extension_root, seed["extension_stem"] + suffix))
    if not _inside(extension, extension_root):
        raise ValueError("Extension artifact escapes extension directory")
    extension = _real_existing(
        extension, "native extension artifact")

    plan = dict(
        contract=PLAN_CONTRACT,
        roots=dict(
            conda_source=conda_source,
            environment_root=prefix,
            site_packages=site_packages,
            code_root=code_root,
            data_root=data_root,
            work_root=work_root),
        bootstrap=bootstrap,
        cuda_version=seed["cuda_version"],
        extension_artifact=extension,
        distribution_overrides=dict(seed["distribution_overrides"]),
        library_overrides=dict(seed["library_overrides"]))
    return plan


def write_plan(plan, output_path):
    output = Path(output_path).absolute()
    if (output.exists() or output.is_symlink()
            or any(parent.is_symlink() for parent in output.parents)
            or not output.parent.is_dir()):
        raise ValueError("Canonical fresh plan path required")
    encoded = json.dumps(
        plan, sort_keys=True, separators=(",", ":"),
        allow_nan=False).encode("ascii")
    descriptor = os.open(
        output, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(descriptor, "wb", closefd=True) as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
    except BaseException:
        output.unlink()
        raise
    return output, hashlib.sha256(encoded).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seed", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--cuda-version")
    args = parser.parse_args()
    if os.name != "posix":
        raise ValueError("Target collection plans must be built on POSIX")
    seed = _load_seed(args.seed)
    if args.cuda_version is not None:
        seed["cuda_version"] = _text(
            args.cuda_version, "CUDA version override")
    plan = build_plan(seed)
    _validate_plan(plan)
    output, sha256 = write_plan(plan, args.output)
    print("%s %s %s" % (output, sha256, time.time()))


if __name__ == "__main__":
    main()
