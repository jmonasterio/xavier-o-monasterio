#!/usr/bin/env python3
"""Build an EPUB of Xavier's book manuscript from the markdown chapters.

Usage: python build-epub.py

Output: epub/believing-into-god.epub

Edit the metadata constants below (TITLE, SUBTITLE, etc.) and
epub/front-matter.md to adjust the front of the book. To add a cover,
set COVER_IMAGE to a JPEG/PNG path.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

# ---------------------------------------------------------------- metadata
TITLE = "Believing into God"
SUBTITLE = "Aquinas, Aristotle, and the Denaturation of Christian Faith"
AUTHOR = "Xavier Ortiz Monasterio"
EDITOR = "Jorge Monasterio"
PUB_DATE = "2026"
LANG = "en"
COVER_IMAGE = None  # e.g. "epub/cover.jpg"

ROOT = Path(__file__).parent
MANUSCRIPT = ROOT / "xavier-papers-organized" / "book-manuscript"
FRONT_MATTER = ROOT / "epub" / "front-matter.md"
OUTPUT = ROOT / "epub" / "believing-into-god.epub"

PANDOC = "C:/Users/jorge.000/AppData/Local/Pandoc/pandoc.exe"

CHAPTERS = [MANUSCRIPT / f"chapter-{n}.md" for n in range(1, 12)]

FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n", re.DOTALL)
# Xavier used "--" as an em dash; convert (but leave "---" alone).
EMDASH_RE = re.compile(r"(?<!-)--(?!-)")


def load_chapter(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    text = FRONTMATTER_RE.sub("", text, count=1)  # strip provenance YAML
    text = EMDASH_RE.sub("\u2014", text)
    return text.strip()


def main() -> int:
    missing = [p for p in CHAPTERS if not p.exists()]
    if missing:
        print(f"Missing chapters: {missing}", file=sys.stderr)
        return 1

    parts = [FRONT_MATTER.read_text(encoding="utf-8")]
    parts += [load_chapter(p) for p in CHAPTERS]
    combined = "\n\n".join(parts) + "\n"

    metadata = "\n".join(
        [
            "---",
            f'title: "{TITLE}"',
            f'subtitle: "{SUBTITLE}"',
            f'author: "{AUTHOR}"',
            "contributor:",
            f'  - role: editor',
            f'    text: "{EDITOR}"',
            f'date: "{PUB_DATE}"',
            f"lang: {LANG}",
            'rights: "Text (c) the Estate of Xavier Ortiz Monasterio.'
            ' Editorial matter and reconstructed chapters 9-11'
            ' (c) 2026 Jorge Monasterio."',
            "---",
            "",
        ]
    )

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "book.md"
        src.write_text(metadata + combined, encoding="utf-8")

        cmd = [
            PANDOC,
            str(src),
            "-f", "markdown+smart",
            "-o", str(OUTPUT),
            "--toc",
            "--toc-depth=1",
            "--split-level=1",
            "--epub-title-page=true",
        ]
        if COVER_IMAGE:
            cmd += ["--epub-cover-image", str(ROOT / COVER_IMAGE)]

        result = subprocess.run(cmd)
        if result.returncode != 0:
            return result.returncode

    size = OUTPUT.stat().st_size
    print(f"Wrote {OUTPUT} ({size / 1024:.0f} KB)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
