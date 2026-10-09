"""Visit every public Streamlit app and Hugging Face Space, wake any that sleep,
and record whether each one actually works.

Streamlit Community Cloud sleeps apps after 12 hours without traffic and says
"to keep your app awake, simply visit your app". Free Hugging Face Spaces also
sleep when idle and wake on a visit. This script is that visit, run on a schedule.

Writes status.json and STATUS.md into the folder given as the first argument.
"""
import datetime as dt
import json
import os
import sys

from playwright.sync_api import sync_playwright

OUT = sys.argv[1] if len(sys.argv) > 1 else "status"
APPS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "apps.json"), encoding="utf-8"))

ERROR_MARKERS = ["Traceback", "ModuleNotFoundError", "Error running app", "This app has encountered an error",
                 "Runtime error", "Build error", "Oh no.", "Application error"]
SLEEP_MARKERS = ["gone to sleep", "Zzzz", "This Space is sleeping", "is currently sleeping"]


def hf_url(space):
    return "https://" + ("datariusai-" + space).lower().replace("_", "-").replace(".", "-") + ".hf.space/"


def page_text(page):
    texts = [page.inner_text("body")] if page.query_selector("body") else []
    for frame in page.frames[1:]:
        try:
            texts.append(frame.inner_text("body"))
        except Exception:
            pass
    return "\n".join(texts)


def check(page, url, kind):
    page.goto(url, wait_until="domcontentloaded", timeout=90_000)
    page.wait_for_timeout(8_000)
    woke = False
    if kind == "streamlit":
        button = page.query_selector("button:has-text('Yes, get this app back up')")
        if button:
            button.click()
            woke = True
            page.wait_for_timeout(60_000)  # cold start
    text = page_text(page)
    if kind == "hf" and any(m in text for m in SLEEP_MARKERS):
        woke = True
        page.wait_for_timeout(60_000)
        text = page_text(page)
    if any(m in text for m in ERROR_MARKERS):
        state = "error"
    elif any(m in text for m in SLEEP_MARKERS):
        state = "waking"
    else:
        state = "ok"
    snippet = " ".join(text.split())[:160]
    return {"state": state, "woke": woke, "snippet": snippet}


def main():
    os.makedirs(OUT, exist_ok=True)
    results = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1280, "height": 900})
        for app in APPS["streamlit"]:
            row = {"kind": "streamlit", "name": app["name"], "url": app["url"]}
            try:
                row.update(check(page, app["url"], "streamlit"))
            except Exception as exc:
                row.update({"state": "error", "woke": False, "snippet": str(exc)[:160]})
            results.append(row)
            print(row["state"], row["url"])
        for space in APPS["huggingface"]:
            url = hf_url(space["id"])
            row = {"kind": "huggingface", "name": space["name"], "url": url,
                   "page": f"https://huggingface.co/spaces/DatariusAI/{space['id']}"}
            try:
                row.update(check(page, url, "hf"))
            except Exception as exc:
                row.update({"state": "error", "woke": False, "snippet": str(exc)[:160]})
            results.append(row)
            print(row["state"], url)
        browser.close()
    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    json.dump({"checked": stamp, "apps": results}, open(os.path.join(OUT, "status.json"), "w"), indent=2)
    icon = {"ok": "🟢", "waking": "🟡", "error": "🔴"}
    lines = [f"# App status\n\nChecked {stamp}. Runs every 6 hours.\n", "| | App | Platform | Note |", "|---|---|---|---|"]
    for r in results:
        note = "woken up" if r["woke"] else ""
        if r["state"] == "error":
            note = r["snippet"][:90].replace("|", "/")
        lines.append(f"| {icon[r['state']]} | [{r['name']}]({r['url']}) | {r['kind']} | {note} |")
    open(os.path.join(OUT, "STATUS.md"), "w").write("\n".join(lines) + "\n")


if __name__ == "__main__":
    main()
