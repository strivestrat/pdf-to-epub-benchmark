"""Measures every converter's EPUB, the same way for all.

    pip install -r requirements.txt
    python scripts/measure.py    -> a table on screen, and results/measured.json

It reads outputs/<converter>/<book>.epub and inputs/<book>.pdf. Every number comes from the files; nothing is
judged by eye. What is counted:

- words_kept: share of the source's words found in the EPUB (bag of words, words of 3+ letters).
  The source is the PDF's own text layer; for the image-only chapter it is the same pages' text
  layer in the original scan. The CIA book's fonts give a joined letter pair as one letter ("efort"
  for "effort"), so its words come from a list read with that put right:
  inputs/cia_psychology_of_intelligence_analysis.words.csv (see the README).
- clutter: running heads, page footers and printer's notes from the source that ended up in the
  reading text (patterns per book below), plus page numbers left as paragraphs between paragraphs
  of running text.
- broken_words: a word split at a line end that stayed split ("fresh- crowned").
- broken_paras: a paragraph that stops mid-sentence and the next one carries on in lower case.
- chapters: entries in the EPUB's table of contents.
- images, tables: <img>/<svg image> and <table> elements kept.
- fixed_layout: the EPUB is pinned to the PDF's pages instead of reflowing.
"""
import collections
import html
import json
import os
import re
import sys
import zipfile

import pypdfium2 as pdfium

HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))          # the repository
BOOKS = {
    # (not "THE ADVENTURES OF TOM SAWYER.", the publisher's advertisement at the back)
    "tom_sawyer_1876": {"pages": None, "page_heads": range(26, 286), "clutter": [r"(?<!OF )T ?O ?M\s+S ?A ?W ?Y ?E ?R\s*\."]},
    "tom_sawyer_ch2_image_only": {"source": "tom_sawyer_1876", "pages": range(35, 42), "page_heads": range(26, 286),
                                  "clutter": [r"(?<!OF )T ?O ?M\s+S ?A ?W ?Y ?E ?R\s*\."]},
    "cia_psychology_of_intelligence_analysis": {"pages": None, "clutter": []},
    "irs_pub501_2025": {"pages": None, "clutter": [r"Publication 501 \(2025\)\s*\d{1,2}\b", r"\b\d{1,2}\s+Publication 501 \(2025\)",
                                                   r"MUST be removed before printing"]},
    "scientific_american_1882-12-09": {"pages": None, "clutter": [r"SCIENTIFIC AMERICAN, INC", r"DECEMBER \d{1,2}[.,] ?1 ?882\. ?\]"]},
}
TERM = re.compile(r"[.!?:;”\"’')\]]\s*$|\d$")
WORD = re.compile(r"[a-z]{3,}")


# Lines of the source that are not the book's text: printer's notes hidden on every page,
# running heads and footers. They don't count as words to keep (removing them is right).
NOT_TEXT = {
    "irs_pub501_2025": [r"Fileid:", r"prints on all proofs", r"MUST be removed before printing",
                        r"Publication 501 \(2025\)\s*\d{1,2}\s*$", r"^\s*\d{1,2}\s+Publication 501 \(2025\)"],
    "tom_sawyer_1876": [r"^\s*\d*\s*T ?O ?M\s+S ?A ?W ?Y ?E ?R\s*\.?\s*\d*\s*$"],
    "tom_sawyer_ch2_image_only": [r"^\s*\d*\s*T ?O ?M\s+S ?A ?W ?Y ?E ?R\s*\.?\s*\d*\s*$"],
    "scientific_american_1882-12-09": [r"SCIENTIFIC AMERICAN, INC", r"^\s*DECEMBER \d{1,2}[.,] ?1 ?882\."],
}


def words_of(text):
    """Words of 3+ letters, with words split by a hyphen at a line end counted whole, so the
    count measures what text is there; split words are counted separately (broken_words)."""
    text = re.sub(r"(\w)[￾­‐-]\s*(\w)", r"\1\2", text)
    return collections.Counter(WORD.findall(text.lower()))


def source_words(book):
    cfg = BOOKS[book]
    listed = os.path.join(HERE, "inputs", book + ".words.csv")
    if os.path.exists(listed):                       # the CIA book (see above)
        with open(listed, encoding="utf-8") as f:
            return collections.Counter({w: int(n) for w, n in (l.strip().split(",") for l in list(f)[1:])})
    doc = pdfium.PdfDocument(os.path.join(HERE, "inputs", (cfg.get("source") or book) + ".pdf"))
    pages = cfg["pages"] or range(len(doc))
    drop = [re.compile(x) for x in NOT_TEXT.get(book, [])]
    lines = []
    for i in pages:
        ls = doc[i].get_textpage().get_text_range().splitlines()
        if cfg.get("page_heads") and i in cfg["page_heads"]:
            ls = [l for k, l in enumerate(ls) if not _page_head(k, l, ls)]
        lines.extend(ls)
    return words_of("\n".join(l for l in lines if not any(d.search(l) for d in drop)))


_NOT_A_HEAD = re.compile(r"\s*(CHAPTER|CONTENTS|PREFACE|ILLUSTRATIONS|CONCLUSION)")


def _page_head(k, line, page_lines):
    """The running head of a page of this book (from the story's first page on, "page_heads" in
    BOOKS): one of the first three lines of a page of text, short, all capitals, with or without the page number ("TOM AS A GENERAL. 35", and the
    scan's misreadings of "TOM SAWYER." such as "TOM SA WYRR."). Added 2026-11-11: until then only
    lines matching "TOM SAWYER." were left out of the source, so a converter that removed the other
    heads was marked down for it and one that left them in the text was credited with their words.
    A chapter's own heading ("CHAPTER II.") is text and stays. Read line by line on 2026-11-11:
    163 lines on the story's pages (index 26-285), all running heads but two picture captions
    that sit at the top of a page ("THE CADET", "BUSINESS TRIP."), the same for every converter."""
    t = line.strip()
    letters = re.sub(r"[^A-Za-z]", "", t)
    return (k < 3 and len([l for l in page_lines if l.strip()]) > 8 and len(t) <= 45
            and len(letters) >= 5 and letters.isupper() and not _NOT_A_HEAD.match(t))


def epub_parts(path):
    z = zipfile.ZipFile(path)
    names = z.namelist()
    opf = next((z.read(n).decode("utf8", "replace") for n in names if n.endswith(".opf")), "")
    docs = [n for n in names if n.lower().endswith((".xhtml", ".html", ".htm")) and "nav" not in os.path.basename(n).lower()]
    # reading order from the spine where possible
    ids = dict(re.findall(r'<item\b[^>]*\bid="([^"]+)"[^>]*\bhref="([^"]+)"', opf)) | {
        a: b for b, a in re.findall(r'<item\b[^>]*\bhref="([^"]+)"[^>]*\bid="([^"]+)"', opf)}
    spine = re.findall(r'<itemref\b[^>]*\bidref="([^"]+)"', opf)
    base = os.path.dirname(next((n for n in names if n.endswith(".opf")), ""))
    order = [os.path.normpath(os.path.join(base, html.unescape(ids[i]))).replace("\\", "/") for i in spine if i in ids]
    order = [n for n in order if n in names] or sorted(docs)
    bodies = [z.read(n).decode("utf8", "replace") for n in order]
    toc = 0
    for n in names:
        if n.endswith(".ncx"):
            toc = max(toc, len(re.findall(r"<navPoint\b", z.read(n).decode("utf8", "replace"))))
        elif "nav" in os.path.basename(n).lower() and n.endswith((".xhtml", ".html")):
            nav = z.read(n).decode("utf8", "replace")
            m = re.search(r'<nav\b[^>]*(?:epub:)?type="toc".*?</nav>', nav, re.S)
            toc = max(toc, len(re.findall(r"<a\b", m.group(0) if m else nav)))
    fixed = "pre-paginated" in opf or sum(b.count("position:absolute") + b.count("position: absolute") for b in bodies) > 200
    return opf, bodies, toc, fixed


def paragraphs(bodies):
    out = []
    for b in bodies:
        b = re.sub(r"<(script|style)\b.*?</\1>", "", b, flags=re.S)
        for inner in re.findall(r"<(?:p|li|td|th|h[1-6]|div)\b[^>]*>((?:(?!<(?:p|div)\b).)*?)</(?:p|li|td|th|h[1-6]|div)>", b, re.S):
            t = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", inner))).strip()
            if t:
                out.append(t)
    return out


def measure(book, path):
    opf, bodies, toc, fixed = epub_parts(path)
    paras = paragraphs(bodies)
    text = "\n".join(paras)
    src = source_words(book)
    got = words_of(text)
    kept = sum(min(n, got[w]) for w, n in src.items()) / max(1, sum(src.values()))
    clutter = sum(len(re.findall(p, text)) for p in BOOKS[book]["clutter"])
    # a page number left as a paragraph of its own between two paragraphs of running text
    # (numbers in a printed contents list are the list's own, not clutter)
    clutter += sum(1 for a, p, b in zip(paras, paras[1:], paras[2:])
                   if re.fullmatch(r"(?:\d{1,4}|[ivxlc]{1,7})", p) and len(a) > 60 and len(b) > 60)
    broken_words = len(re.findall(r"\b[a-z]{2,}[-­] [a-z]{2,}\b", text))
    broken_paras = sum(1 for a, b in zip(paras, paras[1:]) if not TERM.search(a) and b[:1].islower())
    joined = "".join(bodies)
    return {
        "words_kept": round(100 * kept, 1),
        "clutter": clutter,
        "broken_words": broken_words,
        "broken_paras": broken_paras,
        "paragraphs": len(paras),
        "chapters": toc,
        "images": len(re.findall(r"<img\b|<image\b", joined)),
        "tables": len(re.findall(r"<table\b", joined)),
        "fixed_layout": fixed,
        "size_kb": round(os.path.getsize(path) / 1024),
    }


def main():
    results = {}
    for conv in sorted(os.listdir(os.path.join(HERE, "outputs"))):
        for book in BOOKS:
            path = os.path.join(HERE, "outputs", conv, book + ".epub")
            if os.path.exists(path):
                try:
                    results.setdefault(book, {})[conv] = measure(book, path)
                except Exception as e:  # noqa: BLE001
                    results.setdefault(book, {})[conv] = {"error": repr(e)[:120]}
    json.dump(results, open(os.path.join(HERE, "results", "measured.json"), "w"), indent=1)
    for book, convs in results.items():
        print(f"\n== {book}")
        print(f"{'converter':14} {'kept%':>6} {'clutter':>7} {'brkW':>5} {'brkP':>5} {'paras':>6} {'toc':>4} {'img':>4} {'tbl':>4} fixed")
        for conv, r in convs.items():
            if "error" in r:
                print(f"{conv:14} ERROR {r['error']}")
                continue
            print(f"{conv:14} {r['words_kept']:6} {r['clutter']:7} {r['broken_words']:5} {r['broken_paras']:5} {r['paragraphs']:6} "
                  f"{r['chapters']:4} {r['images']:4} {r['tables']:4} {r['fixed_layout']}")


if __name__ == "__main__":
    sys.exit(main())
