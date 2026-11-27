# PDF to EPUB benchmark

Eight PDF to EPUB converters on five hard PDFs, scored by a script. This repo holds the PDFs, the scores, the scripts that made them and our own EPUBs, so you can check the numbers or add a tool.

Made by [StriveStrat](https://strivestrat.com). **We also make [epubwise.com](https://epubwise.com/?ref=github), one of the tools scored here, so read the numbers with that in mind.** Where others did as well or better, the tables show it.

The write-up with pictures: [epubwise.com/best-pdf-to-epub-converter](https://epubwise.com/best-pdf-to-epub-converter?ref=github).

## The files

All five are in the public domain in the United States. They were picked because they are hard.

| File | Pages | Why it is hard | Source |
|---|---|---|---|
| `tom_sawyer_1876` | 300 | A scan with an old OCR text layer, changing running heads, 150 illustrations | [Internet Archive](https://archive.org/details/adventuresoftoms00twaiiala) |
| `tom_sawyer_ch2_image_only` | 7 | Chapter II of the same scan, rendered as pictures: no text at all. We made this one | from the file above |
| `cia_psychology_of_intelligence_analysis` | 214 | Made on a computer: parts, footnotes, figures, and a font whose map breaks "ff" and "fi" | [CIA](https://www.cia.gov/resources/csi/books-monographs/psychology-of-intelligence-analysis-2/) |
| `irs_pub501_2025` | 31 | Three narrow columns, tables, hidden printer's notes on every page | [IRS](https://www.irs.gov/publications/p501) |
| `scientific_american_1882-12-09` | 16 | Three and four columns only 2 to 4 points apart, tiny print | [Internet Archive](https://archive.org/details/scientific-american-1882-12-09) |

SHA-256 sums are in [CHECKSUMS.txt](CHECKSUMS.txt).

## Results

Run on 2 to 5 November 2026, free plans and default settings; epubwise's row was run again on the live site on 11 November. Full tables: [results/scores.csv](results/scores.csv) and [results/reading-order-1882-magazine.csv](results/reading-order-1882-magazine.csv).

Share of the PDF's words kept, in percent:

| Tool | Tom Sawyer | Chapter II, pictures only | CIA book | IRS booklet | 1882 magazine |
|---|---|---|---|---|---|
| **epubwise** (ours) | 99.7 | 97.5 | 99.9 | 99.5 | 95.9 |
| Calibre 9.13 | pictures | pictures | 96.0 | 95.6 | 89.0 |
| CloudConvert | stopped | pictures | 96.0 | 95.6 | stopped |
| Convertio | pictures | pictures | 94.8 | 96.2 | 94.0 |
| FreeConvert | stopped | pictures | 96.0 | 95.6 | 89.0 |
| online-convert.com | stopped | pictures | 96.0 | 95.6 | 89.0 |
| PDF24 Tools | 99.7 | pictures | 93.7 | 98.3 | 92.1 |
| TinyWow | stopped | pictures | 94.8 | 96.2 | 94.0 |

"pictures" means the EPUB held page pictures and no text. "stopped" means the free plan's time limit or our 20-minute wait ended it; the note is in the CSV.

Words alone don't make a readable book. The CSV also has, for every file: clutter left in the text, words split at line ends, paragraphs cut mid-sentence, contents entries and EPUBCheck errors.

**Reading order in the 1882 magazine** (is each line of a column followed by the next line of that column?): epubwise 94.0%, PDF24 51.5%, Convertio and TinyWow 7.4%, Calibre, FreeConvert and online-convert.com 4.9%.

What to know before you use this:

- Five files is a small sample, and we chose them. Try your own PDFs before you pick a tool.
- We have used these files to find and fix faults in epubwise. The other tools were run as they are.
- EPUBs from five of the six websites name Calibre as the program that made them. FreeConvert and online-convert.com scored exactly like the Calibre desktop app on every file they finished.
- The words are counted against the PDF's own text layer. For the two scans that layer is old OCR with mistakes of its own, so 100% is not possible, and a tool that re-reads the page may be marked down for being right.
- The CIA book's fonts give "ff", "fi" and "Th" as their first letter only, so its own text layer says "efort" and "Te". Its words are counted from [a word list](inputs/cia_psychology_of_intelligence_analysis.words.csv) read with those letters put right, using the names the fonts give the joined letters. Counting against the raw layer would reward the mistake.
- Tools change. These are the versions of early November 2026.

## Check it

```
pip install -r requirements.txt
python scripts/measure.py          # every EPUB in outputs/, all measures but EPUBCheck
python scripts/column_order.py     # the magazine's reading order
```

On our files this prints epubwise's numbers above. **To add a tool**, convert the five PDFs, save the results as `outputs/<tool>/<file name>.epub` and run the scripts again. EPUB errors come from [EPUBCheck](https://www.w3.org/publishing/epubcheck/) 5.4.

## What is not here

- epubwise's engine (it isn't open source; you can run the PDFs through [the site](https://epubwise.com/?ref=github), 10 files a day without an account).
- The other tools' EPUBs. Make them yourself with the files above; please respect each tool's terms.

## Corrections

Found a wrong number, or a tool scored unfairly? Open an issue with the file and what you got.

## Licence

MIT for our scripts and tables (see [LICENSE](LICENSE)). The PDFs are in the public domain; the licence doesn't cover them. Product names belong to their owners.
