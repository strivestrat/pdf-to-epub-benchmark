"""Do a page's columns come out in reading order? A words-kept score can't see this: every word
can be present while lines of different articles are mixed together.

Each column of the 1882 magazine is walked top to bottom in the PDF's own text layer. For every
two neighbouring lines, the last two words of the upper and the first two of the lower must sit
side by side in the EPUB. Only pairs whose four words are all in that EPUB are scored, so a
converter that re-reads the scan by its own OCR isn't marked down for reading words differently.

    python scripts/column_order.py            # every converter in outputs/
    python scripts/column_order.py file.epub  # one file

Needs PyMuPDF (requirements.txt).
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the repository
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(HERE)
import pymupdf  # noqa: E402
import measure as m  # noqa: E402

BOOK = "scientific_american_1882-12-09"
# Column edges read off each page by eye and by the coverage of its lines. Pages 0 and 12 are
# left out: page 0 is a cover, and page 12 changes grid halfway down.
GRID = {1: (281, 508), 2: (285, 512), 5: (282, 510), 6: (284, 512), 9: (284, 511), 11: (222, 396, 568), 13: (222, 398, 570)}
WORD = re.compile(r"[a-z]{2,}")


def words(text):
    return WORD.findall(text.lower())


def pairs():
    doc = pymupdf.open(os.path.join("inputs", BOOK + ".pdf"))
    out = []
    for i, gut in GRID.items():
        edges = (0,) + gut + (doc[i].rect.width,)
        cols = [[] for _ in gut + (0,)]
        wide = min(b - a for a, b in zip(gut, gut[1:]))      # a column's width, from the inner gutters
        for b in doc[i].get_text("dict")["blocks"]:
            for ln in b.get("lines", []):
                t = "".join(s["text"] for s in ln["spans"]).strip()
                x0, y0, x1, _y1 = ln["bbox"]
                # a whole printed line only: a piece of one isn't followed by the next line
                if x1 - x0 < 0.88 * wide or t[-1:] in "-\u00ad\ufffe\uffbe" or len(words(t)) < 4:
                    continue
                for c in range(len(cols)):
                    if edges[c] - 3 <= x0 and x1 <= edges[c + 1] + 3:
                        cols[c].append((y0, t))
        for c in cols:
            c.sort()
            for (ya, a), (yb, b) in zip(c, c[1:]):
                if 6 <= yb - ya <= 15:
                    out.append((i, tuple(words(a)[-2:]), tuple(words(b)[:2])))
    return out


def score(path, ps):
    """A stored line can stop a word or two short of the printed line's end ("the conti" / "nent"),
    so the lower line may start up to two words after the upper one ends."""
    seq = words(re.sub(r"<[^>]+>", " ", " ".join(m.epub_parts(path)[1])))
    at = {}
    for k in range(len(seq) - 1):
        at.setdefault((seq[k], seq[k + 1]), []).append(k)
    known = [(a, b) for _i, a, b in ps if a in at and b in at]
    good = sum(1 for a, b in known if any(0 <= y - x - 2 <= 2 for x in at[a] for y in at[b]))
    return good, len(known)


if __name__ == "__main__":
    ps = pairs()
    print("line pairs in the source:", len(ps))
    if len(sys.argv) > 1:
        g, n = score(sys.argv[1], ps)
        print(f"{100 * g / max(1, n):.1f}%  ({g} of {n})")
    else:
        for c in sorted(os.listdir("outputs")):
            p = os.path.join("outputs", c, BOOK + ".epub")
            if os.path.exists(p):
                g, n = score(p, ps)
                print(f"{c:18} {100 * g / max(1, n):5.1f}%  ({g} of {n})")
