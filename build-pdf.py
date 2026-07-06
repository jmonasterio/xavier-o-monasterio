#!/usr/bin/env python3
"""Build the print interior PDF (6in x 9in) for IngramSpark.

Usage: python build-pdf.py

Output: epub/believing-into-god-interior.pdf

Layout: half title, title page, copyright, note on the text, contents,
then chapters 1-11, each opening on a recto (right-hand) page.
Front matter is unpaginated; the body is numbered from 1.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

TITLE = "Believing into God"
SUBTITLE = "Aquinas, Aristotle, and the Denaturation of Christian Faith"
AUTHOR = "Xavier Ortiz Monasterio"
EDITOR = "Jorge Monasterio"
IMPRINT = "Monasterio Books"
PUB_YEAR = "2026"
FONT = "Georgia"

ROOT = Path(__file__).parent
MANUSCRIPT = ROOT / "xavier-papers-organized" / "book-manuscript"
FRONT_MATTER = ROOT / "epub" / "front-matter.md"
OUTPUT = ROOT / "epub" / "believing-into-god-interior.pdf"

PANDOC = "C:/Users/jorge.000/AppData/Local/Pandoc/pandoc.exe"
TYPST = "C:/Users/jorge.000/AppData/Local/Microsoft/WinGet/Links/typst.exe"

CHAPTERS = [MANUSCRIPT / f"chapter-{n}.md" for n in range(1, 12)]

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
EMDASH_RE = re.compile(r"(?<!-)--(?!-)")

PREAMBLE = f"""\
#let horizontalrule = align(center, v(0.5em) + line(length: 30%, stroke: 0.5pt) + v(0.5em))
#set page(width: 6in, height: 9in, numbering: "1",
  margin: (inside: 0.875in, outside: 0.625in, top: 0.75in, bottom: 0.75in))
#set text(size: 11pt, font: "{FONT}")
#set par(justify: true, leading: 0.7em, first-line-indent: 1.2em)
#show heading.where(level: 1): it => {{
  pagebreak(to: "odd", weak: true)
  v(1in)
  set align(center)
  set text(size: 16pt, weight: "bold")
  it.body
  v(0.4in)
}}
#show heading.where(level: 2): set text(size: 12pt)

// ---------------- half title ----------------
#page(numbering: none)[
  #v(2.5in)
  #align(center, text(size: 16pt, weight: "bold")[{TITLE}])
]
#pagebreak(to: "odd", weak: true)

// ---------------- title page ----------------
#page(numbering: none)[
  #v(1.8in)
  #align(center)[
    #text(size: 22pt, weight: "bold")[{TITLE}]
    #v(0.25in)
    #text(size: 13pt, style: "italic")[{SUBTITLE}]
    #v(0.8in)
    #text(size: 14pt)[{AUTHOR}]
    #v(0.2in)
    #text(size: 11pt)[Edited by {EDITOR}]
    #v(1.6in)
    #text(size: 11pt)[{IMPRINT} · {PUB_YEAR}]
  ]
]

// ---------------- front matter (unpaginated, not in contents) ----------------
#set heading(outlined: false)
"""

CONTENTS_AND_BODY_SWITCH = """
// ---------------- contents ----------------
#pagebreak(to: "odd", weak: true)
#v(1in)
#align(center, text(size: 16pt, weight: "bold")[Contents])
#v(0.4in)
#outline(title: none, depth: 1)

// ---------------- body: chapters in contents ----------------
#set heading(outlined: true)
"""


def md_to_typst(markdown: str) -> str:
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "part.md"
        out = Path(tmp) / "part.typ"
        src.write_text(markdown, encoding="utf-8")
        subprocess.run(
            [PANDOC, str(src), "-f", "markdown+smart", "-t", "typst", "-o", str(out)],
            check=True,
        )
        return out.read_text(encoding="utf-8")


GSWIN = "C:/Users/jorge.000/scoop/shims/gswin64c.exe"


def to_device_gray(pdf: Path) -> None:
    """Strip ICC profiles; convert all color to DeviceGray (IngramSpark B&W)."""
    tmp = pdf.with_suffix(".gs.pdf")
    subprocess.run(
        [GSWIN, "-o", str(tmp), "-sDEVICE=pdfwrite",
         "-dPDFSETTINGS=/prepress", "-dCompatibilityLevel=1.4",
         "-sColorConversionStrategy=Gray", "-dProcessColorModel=/DeviceGray",
         "-dDownsampleColorImages=false", "-dDownsampleGrayImages=false",
         "-dDownsampleMonoImages=false", "-dAutoRotatePages=/None",
         str(pdf)],
        check=True,
    )
    tmp.replace(pdf)


def load_chapter(path: Path) -> str:
    text = FRONTMATTER_RE.sub("", path.read_text(encoding="utf-8"), count=1)
    return EMDASH_RE.sub("\u2014", text.strip())


def main() -> int:
    front = md_to_typst(FRONT_MATTER.read_text(encoding="utf-8"))
    body = md_to_typst("\n\n".join(load_chapter(p) for p in CHAPTERS))

    doc = PREAMBLE + front + CONTENTS_AND_BODY_SWITCH + body
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "interior.typ"
        src.write_text(doc, encoding="utf-8")
        result = subprocess.run([TYPST, "compile", str(src), str(OUTPUT)])
        if result.returncode != 0:
            return result.returncode
    to_device_gray(OUTPUT)

    raw = OUTPUT.read_bytes()
    counts = re.findall(rb"/Type\s*/Pages[^>]*?/Count\s+(\d+)", raw)
    pages = max(int(c) for c in counts) if counts else 0
    print(f"Wrote {OUTPUT} ({len(raw) // 1024} KB, {pages} pages)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
