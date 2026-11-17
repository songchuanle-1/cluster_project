"""N1 literature probe: candidate-competition / instance-discrimination evidence.

Read-only arXiv API queries. Writes a small manifest for the novelty record.
No production code, dataset, checkpoint, queue or training change.
"""
import json
import time
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from pathlib import Path

OUT = Path("D:/project/cluster_project/pipeline/reports/litprobe_competition_20260911-2207")
NS = {"a": "http://www.w3.org/2005/Atom"}
QUERIES = [
    'all:"3D visual grounding" AND all:"candidate ranking"',
    'all:"visual grounding" AND all:"hard negative"',
    'all:"referring expression" AND all:"instance discrimination"',
    'all:"proposal ranking" AND all:"object detection"',
    'all:"visual grounding" AND all:"contrastive" AND all:"ranking"',
    'all:"3D visual grounding" AND all:"distractor"',
]


def query(q, maxr=8):
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode(
        {"search_query": q, "start": 0, "max_results": maxr, "sortBy": "relevance"})
    raw = urllib.request.urlopen(url, timeout=30).read()
    root = ET.fromstring(raw)
    out = []
    for e in root.findall("a:entry", NS):
        out.append({
            "title": " ".join(e.find("a:title", NS).text.split()),
            "arxiv_id": e.find("a:id", NS).text.split("/abs/")[-1],
            "published": e.find("a:published", NS).text[:10],
            "summary": " ".join(e.find("a:summary", NS).text.split())[:700],
        })
    return out


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    results = {}
    for q in QUERIES:
        try:
            results[q] = query(q)
        except Exception as exc:  # network is best-effort; record the gap
            results[q] = [{"error": repr(exc)}]
        time.sleep(3)
    payload = {"probe": "n1_competition_litprobe", "queries": results}
    (OUT / "arxiv_probe.json").write_text(json.dumps(payload, indent=2), encoding="utf-8")
    for q, hits in results.items():
        print("###", q)
        for h in hits:
            if "error" in h:
                print("  ERR", h["error"])
            else:
                print(" -", h["published"], h["arxiv_id"], h["title"])


if __name__ == "__main__":
    main()
