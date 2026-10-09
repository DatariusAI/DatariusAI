"""Build the Graphite-theme badge images for the profile README.

Neutral dark chips; each tool keeps its brand colour only as a small dot.
Run: python scripts/make_chips.py   (writes into assets/)
"""
import os

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
CHIP_BG, CHIP_LINE, CHIP_TEXT, LABEL = "#21262d", "#30363d", "#c9d1d9", "#8b949e"
FONT = "-apple-system,BlinkMacSystemFont,'Segoe UI',Helvetica,Arial,sans-serif"

# approximate glyph widths at 13px for layout
NARROW, WIDE = set("ijlI.,:'·|!()[] "), set("mwMW@")


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;")


def text_w(s, size=13):
    w = 0.0
    for ch in s:
        w += 0.30 if ch in NARROW else 0.82 if ch in WIDE else 0.66 if ch.isupper() else 0.56
    return w * size


def chip(x, y, label, dot):
    w = text_w(label) + 34
    return w, (f'<rect x="{x+.5:.1f}" y="{y+.5}" width="{w-1:.1f}" height="27" rx="6" fill="{CHIP_BG}" stroke="{CHIP_LINE}"/>'
               f'<circle cx="{x+14:.1f}" cy="{y+14}" r="4.5" fill="{dot}"/>'
               f'<text x="{x+25:.1f}" y="{y+18.5}" fill="{CHIP_TEXT}" font-family="{FONT}" font-size="13">{esc(label)}</text>')


def save(name, w, h, body):
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h}" viewBox="0 0 {w:.0f} {h}" '
           f'role="img">{body}</svg>')
    open(os.path.join(OUT, name), "w").write(svg)


def single(name, label, dot):
    w, body = chip(0, 0, label, dot)
    save(name, w + 1, 29, body)


STACK = [
    ("AI & ML", [("Python", "#3776AB"), ("PyTorch", "#EE4C2C"), ("TensorFlow", "#FF6F00"), ("Keras", "#D00000"),
                 ("scikit-learn", "#F7931E"), ("Hugging Face", "#FFD21E")]),
    ("LLMs & Agentic AI", [("OpenAI", "#74AA9C"), ("Anthropic Claude", "#CC785C"), ("LangChain", "#1C9C7C")]),
    ("MLOps & Cloud", [("Microsoft Azure", "#0078D4"), ("Google Cloud", "#4285F4"), ("AWS", "#FF9900"), ("Docker", "#2496ED"),
                       ("GitHub Actions", "#2088FF"), ("MLflow", "#0194E2"), ("FastAPI", "#009688"), ("Microsoft Fabric", "#8E44AD")]),
    ("Data & Tools", [("SQL", "#E38C00"), ("BigQuery", "#669DF6"), ("JavaScript", "#F7DF1E"), ("React", "#61DAFB"), ("Node.js", "#339933")]),
]


def stack():
    W, gap, y, body = 900, 8, 0, ""
    for title, items in STACK:
        body += (f'<text x="0" y="{y+14}" fill="{LABEL}" font-family="{FONT}" font-size="12" font-weight="600" '
                 f'letter-spacing=".04em">{esc(title.upper())}</text>')
        y, x = y + 22, 0
        for label, dot in items:
            w = text_w(label) + 34
            if x + w > W:
                x, y = 0, y + 36
            _, c = chip(x, y, label, dot)
            body += c
            x += w + gap
        y += 46
    save("tech-stack.svg", W, y - 10, body)


# Where each Tech Stack badge leads: official docs, or my own hub for each cloud.
HUB = "https://github.com/DatariusAI/"
LINKS = {
    "Python": "https://docs.python.org/3/", "PyTorch": "https://pytorch.org/docs/stable/",
    "TensorFlow": "https://www.tensorflow.org/learn", "Keras": "https://keras.io/",
    "scikit-learn": "https://scikit-learn.org/stable/", "Hugging Face": "https://huggingface.co/docs",
    "OpenAI": "https://platform.openai.com/docs", "Anthropic Claude": "https://docs.claude.com/",
    "LangChain": "https://github.com/langchain-ai/langchain", "Microsoft Azure": HUB + "Azure-AI-Hub",
    "Google Cloud": HUB + "Google-Cloud-AI-Hub", "AWS": HUB + "AWS-AI-Hub", "Docker": "https://docs.docker.com/",
    "GitHub Actions": "https://docs.github.com/actions", "MLflow": "https://mlflow.org/docs/latest/",
    "FastAPI": "https://fastapi.tiangolo.com/", "Microsoft Fabric": "https://learn.microsoft.com/fabric/",
    "SQL": "https://cloud.google.com/bigquery/docs/introduction-sql", "BigQuery": "https://cloud.google.com/bigquery/docs",
    "JavaScript": "https://developer.mozilla.org/docs/Web/JavaScript", "React": "https://react.dev/",
    "Node.js": "https://nodejs.org/docs/latest/api/",
}


def slug(s):
    return "".join(c.lower() if c.isalnum() else "-" for c in s).strip("-").replace("--", "-")


def stack_markdown():
    """One clickable badge per tool, grouped by category."""
    os.makedirs(os.path.join(OUT, "stack"), exist_ok=True)
    md = []
    for title, items in STACK:
        md.append(f"<sub><b>{esc(title.upper())}</b></sub><br/>")
        row = []
        for label, dot in items:
            f = f"stack/{slug(label)}.svg"
            single(f, label, dot)
            row.append(f'<a href="{LINKS[label]}" title="{esc(label)}"><img src="assets/{f}?v=1" alt="{esc(label)}" height="29"/></a>')
        md.append("\n".join(row) + "<br/><br/>")
    return "\n".join(md)


os.makedirs(OUT, exist_ok=True)
single("chip-linkedin.svg", "LinkedIn", "#0A66C2")
single("chip-youtube.svg", "YouTube · @DatariusAI", "#FF0000")
single("chip-discord-dsgn.svg", "Discord · Data Science Global Network", "#5865F2")
single("chip-discord-cqf.svg", "Discord · CQF Quant Finance Hub", "#5865F2")
# stack()  # replaced by one clickable chip per tool (stack_markdown)
snippet = stack_markdown()
open(os.path.join(OUT, "stack", "README-snippet.md"), "w").write(snippet)
print("chips written")
