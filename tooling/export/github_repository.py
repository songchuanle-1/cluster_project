"""Use existing GitHub credentials in memory; report repository metadata only."""
from __future__ import annotations
import argparse
from datetime import datetime, timezone
import json
import os
from pathlib import Path
import subprocess
import urllib.error
import urllib.request

HERE = Path(__file__).resolve().parent


def credential() -> str:
    value = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if value:
        return value
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GCM_INTERACTIVE="never")
    proc = subprocess.run(
        ["git", "credential", "fill"],
        input="protocol=https\nhost=github.com\n\n",
        text=True, capture_output=True, timeout=40, env=env,
    )
    if proc.returncode:
        raise RuntimeError("No noninteractive GitHub credential available.")
    fields = dict(line.split("=", 1) for line in proc.stdout.splitlines() if "=" in line)
    if not fields.get("password"):
        raise RuntimeError("Existing GitHub credential has no credential value.")
    return fields["password"]


def request(token: str, path: str, data: dict | None = None):
    body = None if data is None else json.dumps(data).encode("utf8")
    req = urllib.request.Request(
        "https://api.github.com" + path, data=body,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "cluster-project-handoff",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as response:
            return response.status, json.load(response)
    except urllib.error.HTTPError as exc:
        # Do not echo arbitrary server bodies or request headers.
        return exc.code, {}


def safe_repo(repo: dict) -> dict:
    return {key: repo.get(key) for key in (
        "id", "full_name", "html_url", "clone_url", "private", "default_branch",
        "size", "created_at", "pushed_at", "archived",
    )}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["inspect", "create", "verify"])
    parser.add_argument("--name", default="cluster_project")
    args = parser.parse_args()
    if not all(c.isalnum() or c in "-_." for c in args.name):
        raise SystemExit("Invalid repository name.")
    token = credential()
    status, profile = request(token, "/user")
    if status != 200 or profile.get("login") != "songchuanle-1":
        raise SystemExit("Authenticated GitHub identity did not match audited account.")
    login = profile["login"]
    path = f"/repos/{login}/{args.name}"
    status, repo = request(token, path)
    result = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "mode": args.mode, "account": login, "http_status": status,
        "credentials_printed": False,
    }
    if args.mode == "create":
        if status == 404:
            status, repo = request(token, "/user/repos", {
                "name": args.name,
                "description": "Cluster 3D visual grounding code, experiment inventory and server migration handover (2026-11-17).",
                "private": True, "auto_init": False, "has_issues": True,
            })
            result.update(http_status=status, created=(status == 201))
        else:
            result["created"] = False
        if status not in (200, 201) or repo.get("private") is not True:
            raise SystemExit("Private destination creation/verification failed; no push attempted.")
    if status in (200, 201):
        result["repository"] = safe_repo(repo)
    elif status != 404:
        raise SystemExit(f"GitHub repository query failed with HTTP {status}.")
    if args.mode == "verify" and status == 200:
        status_branches, branches = request(token, path + "/branches?per_page=100")
        result["branches_http_status"] = status_branches
        if status_branches == 200:
            result["branches"] = [
                {"name": b["name"], "sha": b["commit"]["sha"]} for b in branches
            ]
            export = Path("D:/project/cluster_github_export_20261117")
            git = ["git", "-c", "safe.directory=" + export.as_posix(), "-C", str(export)]
            local_refs = dict(
                line.split(" ", 1)
                for line in subprocess.check_output(
                    git + ["for-each-ref", "--format=%(refname:short) %(objectname)", "refs/heads"],
                    text=True, encoding="utf8",
                ).splitlines()
            )
            remote_refs = {row["name"]: row["sha"] for row in result["branches"]}
            result["all_local_refs_match"] = local_refs == remote_refs
            result["main_sha"] = remote_refs.get("main")
            if result["main_sha"]:
                tree_status, tree = request(token, path + "/git/trees/" + result["main_sha"] + "?recursive=1")
                result["tree_http_status"] = tree_status
                result["tree_truncated"] = tree.get("truncated")
                if tree_status == 200 and not tree.get("truncated"):
                    remote_tree = {
                        row["path"]: (row["mode"], row["sha"])
                        for row in tree["tree"] if row["type"] == "blob"
                    }
                    local_tree = {}
                    raw = subprocess.check_output(git + ["ls-tree", "-r", "-z", "HEAD"])
                    for entry in raw.decode("utf8").split("\0"):
                        if not entry:
                            continue
                        info, filename = entry.split("\t", 1)
                        mode, kind, object_id = info.split(" ")
                        if kind == "blob":
                            local_tree[filename] = (mode, object_id)
                    result["github_blob_files"] = len(remote_tree)
                    result["main_tree_matches_local"] = remote_tree == local_tree
            result["verified"] = (
                repo.get("private") is True and repo.get("default_branch") == "main"
                and result.get("all_local_refs_match") is True
                and result.get("main_tree_matches_local") is True
            )
    destination = HERE / ("github_repository." + args.mode + ".json")
    destination.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf8")
    if args.mode == "verify":
        print(json.dumps({key: result.get(key) for key in (
            "checked_at", "account", "verified", "main_sha", "all_local_refs_match",
            "github_blob_files", "main_tree_matches_local", "tree_truncated",
        )}, ensure_ascii=False))
        if result.get("verified") is not True:
            raise SystemExit(1)
    else:
        print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
