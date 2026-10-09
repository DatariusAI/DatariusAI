"""Open every app in apps.json with a headless browser and save a screenshot of each."""
import json
import os
import re
import sys

from playwright.sync_api import sync_playwright

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from keep_awake import hf_url, streamlit_state  # noqa: E402

OUT = sys.argv[1] if len(sys.argv) > 1 else "shots"
APPS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps.json"), encoding="utf-8"))


def slug(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def main():
    os.makedirs(OUT, exist_ok=True)
    index = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1366, "height": 850}, device_scale_factor=1)
        for app in APPS["streamlit"]:
            name, url = app["name"], app["url"]
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=90_000)
                page.wait_for_timeout(5_000)
                btn = page.query_selector("button:has-text('Yes, get this app back up')")
                if btn:
                    btn.click()
                state, _ = streamlit_state(page)
                page.wait_for_timeout(6_000)
            except Exception as exc:
                state = f"error: {exc}"[:80]
            f = f"st-{slug(name)}.png"
            page.screenshot(path=os.path.join(OUT, f))
            index.append({"kind": "streamlit", "name": name, "url": url, "file": f, "state": state})
            print(state, url, flush=True)
        for sp in APPS["huggingface"]:
            url = hf_url(sp["id"])
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=120_000)
                page.wait_for_timeout(20_000)
                state = "ok"
            except Exception as exc:
                state = f"error: {exc}"[:80]
            f = f"hf-{slug(sp['id'])}.png"
            page.screenshot(path=os.path.join(OUT, f))
            index.append({"kind": "huggingface", "name": sp["name"], "id": sp["id"], "url": url,
                          "page": f"https://huggingface.co/spaces/DatariusAI/{sp['id']}", "file": f, "state": state})
            print(state, url, flush=True)
        browser.close()
    json.dump(index, open(os.path.join(OUT, "index.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
