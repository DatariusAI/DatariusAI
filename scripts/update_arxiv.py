"""Refresh the 'Fresh from arXiv' list in README.md.

Queries the public arXiv API for the newest papers on large language
models and AI agents, then rewrites the block between the
ARXIV:START and ARXIV:END markers. Standard library only.
"""
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

README = "README.md"
MAX_RESULTS = 6
QUERY = (
    '(cat:cs.CL OR cat:cs.AI OR cat:cs.LG) AND '
    '(ti:"large language model" OR ti:LLM OR ti:agent OR ti:agentic)'
)
NS = {"a": "http://www.w3.org/2005/Atom"}


def fetch_entries():
    params = urllib.parse.urlencode({
        "search_query": QUERY,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": MAX_RESULTS,
    })
    url = "https://export.arxiv.org/api/query?" + params
    req = urllib.request.Request(url, headers={"User-Agent": "DatariusAI-readme-bot"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        root = ET.fromstring(resp.read())
    rows = []
    for e in root.findall("a:entry", NS):
        title = " ".join(e.find("a:title", NS).text.split())
        link = e.find("a:id", NS).text.strip().replace("http://", "https://")
        link = re.sub(r"v\d+$", "", link)
        date = e.find("a:published", NS).text[:10]
        authors = [a.find("a:name", NS).text for a in e.findall("a:author", NS)]
        who = authors[0] + (" et al." if len(authors) > 1 else "") if authors else ""
        title = title.replace("|", "-").replace("[", "(").replace("]", ")")
        rows.append(f"- [{title}]({link}) · {who} · {date}")
    return rows


def main():
    rows = fetch_entries()
    if not rows:
        print("No entries returned; leaving README unchanged.")
        return
    with open(README, encoding="utf-8") as f:
        text = f.read()
    block = "<!-- ARXIV:START -->\n" + "\n".join(rows) + "\n<!-- ARXIV:END -->"
    new = re.sub(r"<!-- ARXIV:START -->.*?<!-- ARXIV:END -->", block, text, flags=re.S)
    if new != text:
        with open(README, "w", encoding="utf-8") as f:
            f.write(new)
        print(f"Updated {len(rows)} papers.")
    else:
        print("No change.")


if __name__ == "__main__":
    main()
