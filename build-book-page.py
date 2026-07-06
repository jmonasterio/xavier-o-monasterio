#!/usr/bin/env python3
"""Build a single-page web edition of the book manuscript.

Usage: python build-book-page.py

Output: site/book.html (self-contained; no JS dependencies)

Assembles epub/front-matter.md + chapters 1-11, renders to HTML via
pandoc, and wraps the result in a reading layout that matches the
archive site's palette.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TITLE = "Believing into God"
SUBTITLE = "Aquinas, Aristotle, and the Denaturation of Christian Faith"
AUTHOR = "Xavier Ortiz Monasterio"
EDITOR = "Edited by Jorge Monasterio"

ROOT = Path(__file__).parent
MANUSCRIPT = ROOT / "xavier-papers-organized" / "book-manuscript"
FRONT_MATTER = ROOT / "epub" / "front-matter.md"
OUTPUT = ROOT / "site" / "book.html"

PANDOC = "C:/Users/jorge.000/AppData/Local/Pandoc/pandoc.exe"

CHAPTERS = [MANUSCRIPT / f"chapter-{n}.md" for n in range(1, 12)]

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
EMDASH_RE = re.compile(r"(?<!-)--(?!-)")
H1_RE = re.compile(r'<h1[^>]*\bid="([^"]+)"[^>]*>(.*?)</h1>', re.DOTALL)
HEADING_ATTRS_RE = re.compile(r"^(#{1,2} .+?)\s*\{[^}]*\}\s*$", re.MULTILINE)

TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title} | {author}</title>
<meta name="description" content="{title}: {subtitle}. By {author}.">
<style>
:root {{
    --bg-primary: #faf8f5;
    --bg-secondary: #f0ebe3;
    --text-primary: #2c2c2c;
    --text-secondary: #5a5a5a;
    --accent: #8b4513;
    --border: #d0c8bc;
    --font-mono: 'Courier New', Courier, monospace;
    --font-serif: Georgia, 'Times New Roman', serif;
}}
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{
    font-family: var(--font-serif);
    font-size: 18px;
    line-height: 1.75;
    color: var(--text-primary);
    background: var(--bg-primary);
}}
.top-nav {{
    background: var(--bg-secondary);
    border-bottom: 1px solid var(--border);
    padding: 0 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 48px;
    position: sticky;
    top: 0;
    z-index: 100;
    font-family: var(--font-mono);
}}
.site-title {{
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: var(--text-secondary);
}}
.top-nav a {{
    font-size: 12px;
    color: var(--text-secondary);
    text-decoration: none;
    padding: 0.5rem 1rem;
}}
.top-nav a:hover {{ color: var(--accent); }}
main {{ max-width: 38em; margin: 0 auto; padding: 3rem 1.5rem 6rem; }}
.title-block {{ text-align: center; margin: 3rem 0 4rem; }}
.title-block h1 {{ font-size: 2rem; font-weight: bold; }}
.title-block .subtitle {{ font-style: italic; color: var(--text-secondary); margin-top: 0.75rem; }}
.title-block .author {{ margin-top: 2rem; font-size: 1.15rem; }}
.title-block .editor {{ margin-top: 0.5rem; font-size: 0.9rem; color: var(--text-secondary); }}
nav.contents {{
    border: 1px solid var(--border);
    background: var(--bg-secondary);
    padding: 1.5rem 2rem;
    margin: 3rem 0;
}}
nav.contents h2 {{ font-size: 1rem; margin-bottom: 0.75rem; }}
nav.contents ol {{ list-style: none; }}
nav.contents li {{ margin: 0.3rem 0; }}
nav.contents a {{ color: var(--text-primary); text-decoration: none; }}
nav.contents a:hover {{ color: var(--accent); }}
nav.contents .fm {{ color: var(--text-secondary); font-size: 0.9rem; }}
article h1 {{
    font-size: 1.5rem;
    text-align: center;
    margin: 5rem 0 2rem;
    padding-top: 3rem;
    border-top: 1px solid var(--border);
}}
article h2 {{ font-size: 1.15rem; margin: 2.5rem 0 1rem; }}
article p {{ margin: 0 0 0.2rem; text-indent: 1.5em; }}
article h1 + p, article h2 + p, article hr + p, article blockquote + p {{ text-indent: 0; }}
article blockquote {{
    margin: 1.5rem 2rem;
    color: var(--text-secondary);
    font-size: 0.95em;
}}
article hr {{ border: none; text-align: center; margin: 2rem 0; }}
article hr::after {{ content: "* * *"; color: var(--text-secondary); }}
article em {{ font-style: italic; }}
a {{ color: var(--accent); }}
.back-to-top {{
    display: block;
    text-align: center;
    margin-top: 4rem;
    font-family: var(--font-mono);
    font-size: 12px;
}}
@media (max-width: 600px) {{ body {{ font-size: 16px; }} main {{ padding-top: 1.5rem; }} }}
</style>
</head>
<body>
<nav class="top-nav">
    <span class="site-title">Xavier Ortiz Monasterio</span>
    <span><a href="index.html">&larr; Archive</a></span>
</nav>
<main id="top">
<header class="title-block">
    <h1>{title}</h1>
    <p class="subtitle">{subtitle}</p>
    <p class="author">{author}</p>
    <p class="editor">{editor}</p>
</header>
<nav class="contents">
<h2>Contents</h2>
<ol>
{toc}
</ol>
</nav>
<article>
{body}
</article>
<a class="back-to-top" href="#top">back to top</a>
</main>
</body>
</html>
"""


def load_chapter(path: Path) -> str:
    text = FRONTMATTER_RE.sub("", path.read_text(encoding="utf-8"), count=1)
    return EMDASH_RE.sub("\u2014", text.strip())


def main() -> int:
    parts = [HEADING_ATTRS_RE.sub(r"\1", FRONT_MATTER.read_text(encoding="utf-8"))]
    parts += [load_chapter(p) for p in CHAPTERS]
    combined = "\n\n".join(parts)

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "book.md"
        out = Path(tmp) / "book.html"
        src.write_text(combined, encoding="utf-8")
        subprocess.run(
            [PANDOC, str(src), "-f", "markdown+smart", "-t", "html",
             "--wrap=none", "-o", str(out)],
            check=True,
        )
        body = out.read_text(encoding="utf-8")

    toc_items = []
    for anchor, heading in H1_RE.findall(body):
        text = re.sub(r"<[^>]+>", "", heading)
        cls = ' class="fm"' if not text.startswith("Chapter") else ""
        toc_items.append(f'<li{cls}><a href="#{anchor}">{text}</a></li>')

    html = TEMPLATE.format(
        title=TITLE,
        subtitle=SUBTITLE,
        author=AUTHOR,
        editor=EDITOR,
        toc="\n".join(toc_items),
        body=body,
    )
    OUTPUT.write_text(html, encoding="utf-8")
    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
