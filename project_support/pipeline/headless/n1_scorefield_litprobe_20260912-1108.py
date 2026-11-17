"""N1 literature probe for candidate-specific score-field mechanisms.

Read-only OpenAlex API queries. The output is an abstract-level boundary
screen, not a novelty approval and not a mechanism admission.
"""
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path


OUT = Path(
    "D:/project/cluster_project/pipeline/reports/"
    "litprobe_scorefield_20260912-1108"
)
QUERIES = [
    '"3D visual grounding" candidate scoring',
    '"3D visual grounding" mask scoring',
    '"3D visual grounding" same-category distractor',
    '"3D visual grounding" query classification mask',
    '"referred object" candidate selection 3D',
    '"language grounding" score field 3D',
    '"instance discrimination" visual grounding 3D',
    '"mask-conditioned" visual grounding',
]


def query(search_query, max_results=8):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode(
        {
            "search": search_query,
            "per-page": max_results,
        }
    )
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": (
                "cluster-project-n1-literature-probe/1.0 "
                "(mailto:research-pipeline@example.invalid)"
            )
        },
    )
    raw = urllib.request.urlopen(request, timeout=20).read()
    payload = json.loads(raw)
    results = []
    for entry in payload.get("results", []):
        inverted = entry.get("abstract_inverted_index") or {}
        positions = {}
        for word, indexes in inverted.items():
            for index in indexes:
                positions[index] = word
        abstract = " ".join(positions[index] for index in sorted(positions))
        results.append(
            {
                "title": entry.get("title") or "",
                "openalex_id": entry.get("id") or "",
                "doi": entry.get("doi") or "",
                "published": str(entry.get("publication_year") or ""),
                "summary": abstract[:900],
            }
        )
    return results


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for search_query in QUERIES:
        for attempt in range(3):
            try:
                results[search_query] = query(search_query)
                break
            except Exception as exc:  # Network failures are recorded as gaps.
                if attempt == 2:
                    results[search_query] = [{"error": repr(exc)}]
                else:
                    time.sleep(5 * (attempt + 1))
        time.sleep(3)

    payload = {
        "probe": "n1_scorefield_litprobe",
        "created": "2026-09-12T11:12:00+08:00",
        "source": "OpenAlex",
        "queries": results,
    }
    (OUT / "openalex_probe.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    for search_query, hits in results.items():
        print("###", search_query)
        for hit in hits:
            if "error" in hit:
                print("  ERR", hit["error"])
            else:
                print(
                    " -",
                    hit["published"],
                    hit.get("doi") or hit["openalex_id"],
                    hit["title"],
                )


if __name__ == "__main__":
    main()
