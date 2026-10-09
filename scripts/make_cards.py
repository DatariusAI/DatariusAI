"""Build the profile stats cards as SVG files.

Runs in GitHub Actions with GITHUB_TOKEN. Uses only public data:
  * REST: the user's public, non-fork repositories, their stars and languages
  * GraphQL: the public contribution calendar (for totals and streaks)
Writes stats.svg and languages.svg into the folder given as the first argument.
Standard library only.
"""
import datetime as dt
import json
import os
import sys
import urllib.request

USER = os.environ.get("CARD_USER", "DatariusAI")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = sys.argv[1] if len(sys.argv) > 1 else "cards"

# Graphite palette (GitHub dark), to match the rest of the profile page
BG, BORDER, TITLE, TEXT, ACCENT, MUTED = "#161b22", "#30363d", "#e6edf3", "#c9d1d9", "#58a6ff", "#8b949e"
LANG_COLORS = {
    "Python": "#3572A5", "Jupyter Notebook": "#DA5B0B", "TypeScript": "#3178c6", "JavaScript": "#f1e05a",
    "HTML": "#e34c26", "CSS": "#663399", "Shell": "#89e051", "Go": "#00ADD8", "R": "#198CE7",
    "Dockerfile": "#384d54", "C++": "#f34b7d", "Java": "#b07219", "SQL": "#e38c00",
}
SKIP_LANGS = {"HTML", "CSS", "Shell"}
CARD_H = 200  # both cards share one size so they line up side by side


def api(url, body=None):
    headers = {"User-Agent": "DatariusAI-cards", "Accept": "application/vnd.github+json"}
    if TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, headers=headers)
    with urllib.request.urlopen(req, timeout=40) as r:
        return json.loads(r.read())


def public_repos():
    repos, page = [], 1
    while True:
        batch = api(f"https://api.github.com/users/{USER}/repos?per_page=100&type=owner&page={page}")
        repos += batch
        if len(batch) < 100:
            return [r for r in repos if not r["fork"] and not r["private"]]
        page += 1


def contribution_days():
    q = """query($login:String!){user(login:$login){contributionsCollection{
      contributionCalendar{totalContributions weeks{contributionDays{date contributionCount}}}}}}"""
    data = api("https://api.github.com/graphql", {"query": q, "variables": {"login": USER}})
    cal = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    days = [d for w in cal["weeks"] for d in w["contributionDays"]]
    return cal["totalContributions"], days


def streaks(days):
    today = dt.date.today().isoformat()
    longest = run = 0
    for d in days:
        run = run + 1 if d["contributionCount"] > 0 else 0
        longest = max(longest, run)
    current = 0
    for d in reversed(days):
        if d["date"] == today and d["contributionCount"] == 0:
            continue  # today is not over yet
        if d["contributionCount"] > 0:
            current += 1
        else:
            break
    return current, longest


def card(width, height, title, body):
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="{title}">
<style>
.t{{font:600 18px 'Segoe UI',Ubuntu,sans-serif;fill:{TITLE}}}
.l{{font:400 14px 'Segoe UI',Ubuntu,sans-serif;fill:{TEXT}}}
.v{{font:700 14px 'Segoe UI',Ubuntu,sans-serif;fill:{ACCENT}}}
.s{{font:400 11px 'Segoe UI',Ubuntu,sans-serif;fill:{MUTED}}}
</style>
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="8" fill="{BG}" stroke="{BORDER}"/>
<text x="24" y="36" class="t">{title}</text>
{body}
</svg>"""


def stats_svg(repos, total, langs):
    hubs = sum(1 for r in repos if r["name"].startswith("AI-in-") or r["name"].endswith("-AI-Hub")
               or r["name"] in ("Mathematics-for-AI", "Cloud-Landing-Zones", "AI-Cybersecurity", "AI-Systems-and-Platforms"))
    rows = [("Public repositories", len(repos)), ("Public contributions (last 12 months)", f"{total:,}"),
            ("Daily-refreshed AI hubs", hubs), ("Languages used", langs)]
    body = ""
    for i, (label, value) in enumerate(rows):
        y = 70 + i * 26
        body += (f'<g class="row" style="animation-delay:{i*120}ms">'
                 f'<circle cx="30" cy="{y-5}" r="4" fill="{ACCENT}"/>'
                 f'<text x="44" y="{y}" class="l">{label}</text>'
                 f'<text x="400" y="{y}" class="v" text-anchor="end">{value}</text></g>')
    body += f'<text x="24" y="{70 + len(rows)*26 + 4}" class="s">Updated {dt.date.today():%d %b %Y}</text>'
    return card(425, CARD_H, "GitHub stats", body)


def language_totals(repos):
    totals = {}
    for r in repos:
        try:
            for lang, size in api(r["languages_url"]).items():
                if lang not in SKIP_LANGS:
                    totals[lang] = totals.get(lang, 0) + size
        except Exception as exc:
            print("languages failed:", r["name"], exc)
    return totals


def languages_svg(totals):
    grand = sum(totals.values()) or 1
    top = [kv for kv in sorted(totals.items(), key=lambda kv: kv[1], reverse=True) if kv[1] / grand >= 0.005][:6]
    whole = sum(v for _, v in top) or 1
    x, bar = 24, ""
    for lang, size in top:
        w = 377 * size / whole
        bar += f'<rect x="{x:.1f}" y="56" width="{w:.1f}" height="10" fill="{LANG_COLORS.get(lang, ACCENT)}"/>'
        x += w
    bar = f'<clipPath id="c"><rect x="24" y="56" width="377" height="10" rx="5"/></clipPath><g clip-path="url(#c)">{bar}</g>'
    items = ""
    for i, (lang, size) in enumerate(top):
        cx, cy = 30 + (i % 2) * 190, 96 + (i // 2) * 26
        items += (f'<g class="row" style="animation-delay:{i*120}ms">'
                  f'<circle cx="{cx}" cy="{cy-5}" r="5" fill="{LANG_COLORS.get(lang, ACCENT)}"/>'
                  f'<text x="{cx+12}" y="{cy}" class="l">{lang} <tspan class="s">{100*size/whole:.1f}%</tspan></text></g>')
    return card(425, CARD_H, "Most used languages", bar + items)


def main():
    os.makedirs(OUT, exist_ok=True)
    repos = public_repos()
    total, days = contribution_days()
    totals = language_totals(repos)
    open(os.path.join(OUT, "stats.svg"), "w").write(stats_svg(repos, total, len(totals)))
    open(os.path.join(OUT, "languages.svg"), "w").write(languages_svg(totals))
    print(f"{len(repos)} repos, {total} contributions, {len(totals)} languages")


if __name__ == "__main__":
    main()
