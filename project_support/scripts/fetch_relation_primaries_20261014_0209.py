"""Fetch only publisher primary-paper pages, preserving verified bytes."""
from datetime import datetime, timezone
import hashlib
from html.parser import HTMLParser
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
TOKEN = "66fa1e81aec94d5eb10265ea533669ac"
owner = json.loads((ROOT / "pipeline/headless/.foreground.lockdir/owner.json").read_text())
assert owner["token"] == TOKEN and owner["thread_id"] == os.environ["CODEX_THREAD_ID"]
DEST = ROOT / "pipeline/references/relation_primary_20261014_0209"
DEST.mkdir(parents=True, exist_ok=True)


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.href = None
        self.text = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.href = dict(attrs).get("href")
            self.text = []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data)

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            self.links.append((self.href, " ".join(" ".join(self.text).split())))
            self.href = None


def get(url):
    request = urllib.request.Request(url, headers={"User-Agent": "Research reference audit"})
    with urllib.request.urlopen(request, timeout=25) as stream:
        return stream.read(), stream.geturl()


rows, errors = [], []
for year in (2023, 2025):
    url = "https://openaccess.thecvf.com/CVPR" + str(year) + "?day=all"
    try:
        data, actual = get(url)
        parser = Links()
        parser.feed(data.decode("utf-8"))
        found = [(href, title) for href, title in parser.links
                 if ".html" in href and any(term in title.lower() for term in (
                     "ns3d", "explicit text-decoupling",
                     "constraint satisfaction"))]
        for href, title in found:
            page_url = urllib.request.urljoin(actual, href)
            page, actual_page = get(page_url)
            filename = Path(href).name
            with (DEST / filename).open("xb") as stream:
                stream.write(page)
            links = Links()
            links.feed(page.decode("utf-8"))
            pdfs = [urllib.request.urljoin(actual_page, link)
                    for link, text in links.links if link.endswith(".pdf")
                    and "_paper.pdf" in link]
            record = {
                "title": title, "publisher_page": actual_page,
                "page_path": (DEST / filename).relative_to(ROOT).as_posix(),
                "page_sha256": hashlib.sha256(page).hexdigest(),
                "paper_pdf_urls": pdfs}
            if pdfs:
                pdf, pdf_url = get(pdfs[0])
                assert pdf.startswith(b"%PDF"), "Publisher did not return PDF"
                name = Path(urllib.parse.urlparse(pdf_url).path).name
                with (DEST / name).open("xb") as stream:
                    stream.write(pdf)
                record.update(pdf_path=(DEST / name).relative_to(ROOT).as_posix(),
                              pdf_sha256=hashlib.sha256(pdf).hexdigest(),
                              pdf_url=pdf_url)
            rows.append(record)
    except Exception as exc:
        errors.append({"index": url, "error": repr(exc)})
result = {"tick_token": TOKEN, "observed_at": datetime.now(timezone.utc).isoformat(),
          "primary_papers": rows, "errors": errors,
          "scope": "Verified primary publisher content only. Retrieval is not proof of whole-mechanism novelty."}
with (DEST / "manifest.json").open("x") as stream:
    json.dump(result, stream, indent=2)
    stream.write("\n")
print(json.dumps(result, indent=2))
