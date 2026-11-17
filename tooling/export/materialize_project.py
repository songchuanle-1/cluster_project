"""Restore the original project folder layout in a new destination, without running it."""
from __future__ import annotations
import argparse
import errno
import json
import os
from pathlib import Path, PurePosixPath
import shutil
import subprocess


def tracked_entries(repo: Path) -> list[dict]:
    result = subprocess.run(
        ["git", "-C", str(repo), "ls-files", "--stage", "-z"],
        capture_output=True, check=True,
    )
    entries = []
    for record in result.stdout.split(b"\0"):
        if not record:
            continue
        header, name = record.split(b"\t", 1)
        mode, oid, stage = header.decode("ascii").split()
        if stage != "0":
            raise SystemExit("Unmerged Git index entries must be resolved before materializing.")
        entries.append({"mode": mode, "oid": oid, "name": name.decode("utf8", errors="surrogateescape")})
    gitlinks = [entry["name"] for entry in entries if entry["mode"] == "160000"]
    if gitlinks:
        raise SystemExit("Gitlink source must be flattened or supplied before materializing: " + ", ".join(gitlinks))
    unsupported = [entry["name"] for entry in entries if entry["mode"] not in {"100644", "100755", "120000"}]
    if unsupported:
        raise SystemExit("Unsupported Git modes: " + ", ".join(unsupported))
    return entries


def destination_path(name: str) -> Path:
    rel = PurePosixPath(name)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        raise SystemExit("Unsafe tracked path: " + name)
    if rel.parts[0] == "project_support":
        return Path(*rel.parts[1:])
    if rel.parts[0] in {"docs", "experiments", "provenance", "tooling"} or name == "README.md":
        # The export README links to these handoff directories.
        return Path("handoff", *rel.parts)
    return Path("Cluster", *rel.parts)


def restore_link(link_target: bytes, target: Path, *, target_is_directory: bool) -> str:
    """Preserve links; Windows privilege failures get an explicit Git placeholder."""
    try:
        os.symlink(os.fsdecode(link_target), target, target_is_directory=target_is_directory)
        return "symlink"
    except (OSError, NotImplementedError) as exc:
        privilege_error = isinstance(exc, NotImplementedError) or (
            getattr(exc, "winerror", None) in {5, 50, 1314}
            or getattr(exc, "errno", None) in {errno.EACCES, errno.EPERM, errno.ENOTSUP}
        )
        if os.name != "nt" or not privilege_error:
            raise
        # Exclusive creation also protects against a destination appearing mid-run.
        with target.open("xb") as stream:
            stream.write(link_target)
        return "windows_git_placeholder_symlink_privilege_unavailable"


def materialize(repo: Path, destination: Path) -> dict:
    # lexists rejects dangling links too, before resolve can hide their presence.
    if os.path.lexists(destination):
        raise SystemExit("Destination must not exist; original files will not be overwritten.")
    dest = destination.resolve()
    if repo == dest or repo in dest.parents or dest in repo.parents:
        raise SystemExit("Destination must be separate from the export repository.")
    entries = tracked_entries(repo)  # All gitlinks fail before destination creation.
    targets = {}
    prepared = []
    for entry in entries:
        name = entry["name"]
        rel = destination_path(name)
        key = os.path.normcase(str(rel))
        if key in targets:
            raise SystemExit("Mapped destination collision: " + name)
        targets[key] = name
        source = repo / Path(*PurePosixPath(name).parts)
        entry = dict(entry, relative_target=rel, source=source)
        if entry["mode"] == "120000":
            raw_target = subprocess.run(
                ["git", "-C", str(repo), "cat-file", "blob", entry["oid"]],
                capture_output=True, check=True,
            ).stdout
            if not raw_target or b"\0" in raw_target:
                raise SystemExit("Invalid symlink target: " + name)
            if source.is_symlink():
                actual = os.fsencode(os.readlink(source))
            elif source.is_file():
                actual = source.read_bytes()
            else:
                raise SystemExit("Missing symlink or Git placeholder: " + name)
            if actual != raw_target:
                raise SystemExit("Symlink worktree target differs from Git index: " + name)
            entry["link_target"] = raw_target
            # Existing file targets need the file flag; directory aliases and
            # unresolved targets retain directory-link semantics on Windows.
            entry["target_is_directory"] = not (source.parent / os.fsdecode(raw_target)).is_file()
        elif source.is_symlink() or not source.is_file():
            raise SystemExit("Expected regular tracked source file: " + name)
        prepared.append(entry)
    for entry in prepared:
        for parent in entry["relative_target"].parents:
            if os.path.normcase(str(parent)) in targets:
                raise SystemExit("Mapped file/link is a parent of another tracked target: " + entry["name"])

    dest.mkdir(parents=True)
    count = 0
    links = []
    # Copy regular files explicitly; never hand a directory link to copy2.
    for entry in sorted(prepared, key=lambda item: item["mode"] == "120000"):
        target = dest / entry["relative_target"]
        target.parent.mkdir(parents=True, exist_ok=True)
        if entry["mode"] == "120000":
            storage = restore_link(
                entry["link_target"], target,
                target_is_directory=entry["target_is_directory"],
            )
            links.append({
                "source": entry["name"], "destination": entry["relative_target"].as_posix(),
                "link_target": entry["link_target"].decode("utf8", errors="surrogateescape"),
                "target_is_directory": entry["target_is_directory"], "storage": storage,
            })
        else:
            if os.path.lexists(target):
                raise SystemExit("Refusing to overwrite mapped target: " + str(target))
            shutil.copy2(entry["source"], target)
            count += 1
    return {
        "destination": str(dest), "files_copied": count,
        "symlink_entries_preserved": len(links), "symlink_results": links,
        "windows_git_placeholder_count": sum(item["storage"] != "symlink" for item in links),
        "code_root": str(dest / "Cluster"),
        "handoff_readme": str(dest / "handoff/README.md") if "README.md" in {item["name"] for item in entries} else None,
        "git_history": "Kept in the original clone; this generated layout is a file snapshot.",
        "training_started": False,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    repo = args.repo.resolve()
    print(json.dumps(materialize(repo, args.destination.absolute()), ensure_ascii=False))


if __name__ == "__main__":
    main()
