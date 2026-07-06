#!/usr/bin/env python3
"""Build the dust jacket PDF for the IngramSpark jacketed hardcover.

Usage: python build-jacket.py

Output: epub/believing-into-god-jacket.pdf

Layout (left to right): bleed | back flap | fold | back cover | spine |
front cover | fold | front flap | bleed. Formulas from the IngramSpark
File Creation Guide (dust jacket section):
  cover panel = trim + 0.4375in wide, trim + 0.25in tall
  flap 3.25in, folds 0.25in, bleed 0.125in all around

!!! SPINE_WIDTH is a DRAFT estimate until the Cover Template Generator
email arrives; set it to the template's exact spine value and rebuild.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ------------------------------------------------------------ parameters
SPINE_WIDTH = 0.886  # inches -- DRAFT: 254pp / 350ppi + 0.16 case allowance.
                     # REPLACE with the exact value from the IngramSpark
                     # cover template, then rebuild.

TRIM_W, TRIM_H = 6.0, 9.0
PANEL_W = TRIM_W + 0.4375          # 6.4375
PANEL_H = TRIM_H + 0.25            # 9.25
FLAP_W = 3.25
FOLD_W = 0.25
BLEED = 0.125

PAGE_W = 2 * BLEED + 2 * FLAP_W + 2 * FOLD_W + 2 * PANEL_W + SPINE_WIDTH
PAGE_H = 2 * BLEED + PANEL_H

ISBN = "9798234138699"
TITLE = "Believing into God"
SUBTITLE = "Aquinas, Aristotle, and the\nDenaturation of Christian Faith"
AUTHOR = "Xavier Ortiz Monasterio"
IMPRINT = "MONASTERIO BOOKS"

ROOT = Path(__file__).parent
OUTPUT = ROOT / "epub" / "believing-into-god-jacket.pdf"
BARCODE_SVG = ROOT / "epub" / "_barcode.svg"

PANDOC = "C:/Users/jorge.000/AppData/Local/Pandoc/pandoc.exe"
TYPST = "C:/Users/jorge.000/AppData/Local/Microsoft/WinGet/Links/typst.exe"

# ------------------------------------------------------------ jacket copy
FRONT_FLAP = """Did Thomas Aquinas baptize Aristotle — or did Aristotle quietly denature Christian faith?

In this book, left unpublished at his death, Xavier Ortiz Monasterio argues that the medieval synthesis celebrated as the triumph of faith and reason in fact transformed faith into something the Church Fathers would not have recognized: assent to propositions rather than the whole person's consent to God.

Reading Aquinas against Bonaventure, Anselm, and the resisters of the thirteenth century, Monasterio traces how the Bible — a fundamentally narrative book — was recast as a collection of statements fit for Aristotelian science, and what was lost in that translation. The argument anticipates Hans Frei's "eclipse of biblical narrative" and grounds it a full five centuries earlier.

The manuscript's final three chapters, reconstructed from the author's notes, complete the argument as he projected it."""

BACK_FLAP = """Xavier Ortiz Monasterio (1926–2011) took his Ph.D. in philosophy at the University of Paris and taught for thirty-four years at the University of Dayton. He is the author of To Be Human: An Introductory Experiment in Philosophy (Paulist Press, 1985) and of essays on Camus, Sartre, and the philosophy of faith. He worked on this book through the 1990s; it is published here for the first time.

Edited by Jorge Monasterio.

The complete archive of the author's papers — essays, course materials, and this manuscript in its original form — is free to read at
argw.com/xavier

Permanently preserved at #text(hyphenate: false)[github.com/jmonasterio/xavier-o-monasterio]"""

BACK_COVER_QUOTE = """“The Bible and the Summa are books of totally different literary genres. Nonetheless, supposedly, the subject matter of both is divine revelation. The question is whether in the shift from one genre to the other divine revelation remains the same — or whether, on the contrary, it undergoes a substantive change, a change affecting its very nature.”"""


# ------------------------------------------------------------ EAN-13 barcode
def ean13_svg(digits: str) -> str:
    """Render an EAN-13 barcode as SVG (module = 0.013in, height 0.8in)."""
    assert len(digits) == 13 and digits.isdigit()
    L = {"0": "0001101", "1": "0011001", "2": "0010011", "3": "0111101",
         "4": "0100011", "5": "0110001", "6": "0101111", "7": "0111011",
         "8": "0110111", "9": "0001011"}
    R = {d: L[d].translate(str.maketrans("01", "10")) for d in L}
    G = {d: R[d][::-1] for d in R}  # G = reversed R; R = inverted L
    PARITY = ["LLLLLL", "LLGLGG", "LLGGLG", "LLGGGL", "LGLLGG",
              "LGGLLG", "LGGGLL", "LGLGLG", "LGLGGL", "LGGLGL"]
    first, left, right = digits[0], digits[1:7], digits[7:]
    bits = "101"
    for d, p in zip(left, PARITY[int(first)]):
        bits += L[d] if p == "L" else G[d]
    bits += "01010"
    for d in right:
        bits += R[d]
    bits += "101"
    module = 0.013  # inches
    height = 0.8
    pad = 12 * module  # EAN quiet zones (>= 11 modules left, 7 right)
    bar_w = len(bits) * module
    width = bar_w + 2 * pad
    rects = []
    x = pad
    for b in bits:
        if b == "1":
            rects.append(
                f'<rect x="{x:.4f}in" y="0" width="{module:.4f}in" height="{height}in" fill="black"/>')
        x += module
    text = (f'<text x="{width / 2:.3f}in" y="{height + 0.15:.3f}in" '
            f'text-anchor="middle" font-family="Helvetica, Arial, sans-serif" '
            f'font-size="8pt">ISBN {digits[:3]}-{digits[3]}-{digits[4:7]}-{digits[7:12]}-{digits[12]}</text>')
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width:.3f}in" '
            f'height="{height + 0.26:.3f}in">'
            f'<rect width="100%" height="100%" fill="white"/>{"".join(rects)}{text}</svg>')


def esc(s: str) -> str:
    """Escape for a typst string/content context."""
    return s.replace("\\", "\\\\").replace('"', '\\"')


def para_blocks(text: str) -> str:
    """Markdown-ish paragraphs to typst content."""
    out = []
    for p in text.split("\n\n"):
        out.append("#par[" + p.replace("\n", " ") + "]")
    return "\n#v(0.6em)\n".join(out)


GSWIN = "C:/Users/jorge.000/scoop/shims/gswin64c.exe"


def to_device_cmyk(pdf: Path) -> None:
    """Strip ICC profiles; convert all color to DeviceCMYK (IngramSpark color)."""
    tmp = pdf.with_suffix(".gs.pdf")
    subprocess.run(
        [GSWIN, "-o", str(tmp), "-sDEVICE=pdfwrite",
         "-dPDFSETTINGS=/prepress", "-dCompatibilityLevel=1.4",
         "-sColorConversionStrategy=CMYK", "-dProcessColorModel=/DeviceCMYK",
         "-dDownsampleColorImages=false", "-dDownsampleGrayImages=false",
         "-dDownsampleMonoImages=false", "-dAutoRotatePages=/None",
         str(pdf)],
        check=True,
    )
    tmp.replace(pdf)


def main() -> int:
    BARCODE_SVG.write_text(ean13_svg(ISBN), encoding="utf-8")

    x_back_flap = BLEED
    x_back_cover = x_back_flap + FLAP_W + FOLD_W
    x_spine = x_back_cover + PANEL_W
    x_front_cover = x_spine + SPINE_WIDTH
    x_front_flap = x_front_cover + PANEL_W + FOLD_W
    y_top = BLEED

    doc = f"""
#set page(width: {PAGE_W}in, height: {PAGE_H}in, margin: 0in, fill: rgb("faf8f5"))
#set text(font: "Georgia", fill: rgb("2c2c2c"))
#set par(justify: true, leading: 0.65em)

#let accent = rgb("6b3410")

// ---------------- back flap ----------------
#place(dx: {x_back_flap}in + 0.25in, dy: {y_top}in + 0.55in,
  block(width: {FLAP_W}in - 0.5in, text(size: 9pt)[
    #set par(justify: false)
    {para_blocks(BACK_FLAP)}
  ]))

// ---------------- back cover ----------------
#place(dx: {x_back_cover}in + 0.75in, dy: {y_top}in + 0.9in,
  block(width: {PANEL_W}in - 1.5in)[
    #set text(size: 11.5pt)
    #set par(justify: false)
    #text(size: 9pt, tracking: 0.12em, fill: accent)[PHILOSOPHY · RELIGION]
    #v(0.5in)
    #text(style: "italic")[{esc(BACK_COVER_QUOTE)}]
    #v(0.3in)
    #align(right, text(size: 10pt)[— from Chapter 1])
  ])
#place(dx: {x_back_cover + PANEL_W - 2.4}in, dy: {y_top + PANEL_H - 1.55}in,
  image("{BARCODE_SVG.name}", width: 1.75in))

// ---------------- spine ----------------
#place(dx: {x_spine}in, dy: {y_top}in,
  block(width: {SPINE_WIDTH}in, height: {PANEL_H}in)[
    #set text(size: 11pt)
    #place(center + top, dy: 0.55in, rotate(90deg, origin: center, reflow: true,
      text(tracking: 0.08em)[MONASTERIO]))
    #place(center + horizon, rotate(90deg, origin: center, reflow: true,
      text(weight: "bold", tracking: 0.06em)[BELIEVING INTO GOD]))
    #place(center + bottom, dy: -0.45in, rotate(90deg, origin: center, reflow: true,
      text(size: 7.5pt, tracking: 0.1em)[{IMPRINT}]))
  ])

// ---------------- front cover ----------------
#place(dx: {x_front_cover}in, dy: {y_top}in,
  block(width: {PANEL_W}in, height: {PANEL_H}in)[
    #align(center)[
      #v(1.5in)
      #text(size: 34pt, weight: "bold")[{esc(TITLE)}]
      #v(0.35in)
      #line(length: 1.6in, stroke: 1pt + accent)
      #v(0.35in)
      #text(size: 14pt, style: "italic")[{SUBTITLE.replace(chr(10), " \\ ")}]
      #v(2.1in)
      #text(size: 17pt)[{esc(AUTHOR)}]
    ]
  ])

// ---------------- front flap ----------------
#place(dx: {x_front_flap}in + 0.25in, dy: {y_top}in + 0.55in,
  block(width: {FLAP_W}in - 0.5in, text(size: 9pt)[
    #set par(justify: false)
    {para_blocks(FRONT_FLAP)}
    #v(1em)
    #align(right, text(size: 8pt)[Jacket design: Monasterio Books])
  ]))
"""
    src = ROOT / "epub" / "_jacket.typ"
    src.write_text(doc, encoding="utf-8")
    result = subprocess.run([TYPST, "compile", str(src), str(OUTPUT)])
    if result.returncode != 0:
        return result.returncode
    to_device_cmyk(OUTPUT)

    print(f"Wrote {OUTPUT} ({OUTPUT.stat().st_size // 1024} KB)")
    print(f"Page: {PAGE_W:.3f}in x {PAGE_H:.3f}in (spine {SPINE_WIDTH}in DRAFT)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
