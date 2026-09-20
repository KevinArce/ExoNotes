"""Reconnaissance on `download_obsnotes` before pre-registering it as the corpus.

PLAN.md §2.2 proposed this corpus on a 30-TIC sample but recorded only summary statistics
and never measured the `Master Disp:` leakage channel it warns about. The corpus decision
now rests on those numbers, so they get reproduced here, with the leakage quantified.

Run:  .venv/bin/python scripts/027_obsnotes_recon.py [n_per_class]
Idempotent: yes. Per-TIC responses are cached under data/cache/obsnotes/, so a re-run does
no network I/O and the same TIC sample (seeded) reproduces exactly.
"""
import json
import pathlib
import re
import statistics
import sys
import time

import duckdb

ROOT = pathlib.Path(__file__).resolve().parent.parent
CACHE = ROOT / "data" / "cache" / "obsnotes"
OUT = ROOT / "research" / "data"
N_PER_CLASS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
SEED = 20260920

# The disposition is written into tfopwg notes verbatim. These are the leakage probes.
MASTER_DISP = re.compile(r"(?i)master\s*disp\s*:\s*([A-Z]{1,3})")
ANY_DISP = re.compile(r"(?i)\b(?:master|phot|spec)\s*disp\s*:")
TAG = re.compile(r"<[^>]+>")


def fetch(tic: int, tries: int = 3):
    """Cached per-TIC obsnotes fetch. Returns list-of-dicts, or None on hard failure."""
    CACHE.mkdir(parents=True, exist_ok=True)
    hit = CACHE / f"{tic}.json"
    if hit.exists():
        return json.loads(hit.read_text()), True
    import etta  # imported late so a cached run needs no network stack
    last = None
    for attempt in range(tries):
        try:
            df = etta.download_obsnotes(tic=int(tic))
            recs = df.astype(str).to_dict("records")
            hit.write_text(json.dumps(recs, indent=1))
            return recs, False
        except Exception as e:  # noqa: BLE001 - any transport failure is retryable here
            last = e
            time.sleep(2 ** attempt)
    sys.stderr.write(f"  TIC {tic}: giving up after {tries} tries -> {type(last).__name__}\n")
    return None, False


def plain(html: str) -> str:
    return re.sub(r"\s+", " ", TAG.sub(" ", html or "")).strip()


def main():
    con = duckdb.connect(str(ROOT / "data" / "exonotes.duckdb"), read_only=True)
    con.execute(f"select setseed({(SEED % 1000) / 1000})")
    tics = []
    for y in (1, 0):
        tics += [(r[0], y) for r in con.execute(
            "select distinct tic_id from analysis_set where y=? order by random() limit ?",
            [y, N_PER_CLASS]).fetchall()]

    rows, failed = [], 0
    for tic, y in tics:
        recs, cached = fetch(tic)
        if recs is None:
            failed += 1
            continue
        notes = [plain(r.get("notes", "")) for r in recs]
        groups = [str(r.get("Groupname", "")).lower() for r in recs]
        text = " ".join(notes)
        disp = MASTER_DISP.search(text)
        # A note belongs to the TFOPWG summary iff Groupname == 'tfopwg'. Everything else is
        # an observer note: Groupname comes back as 'nan' for those, but Username is a real
        # person (everett, latham, furlan, ...). Treating 'nan' as tfopwg -- as the first
        # version of this script did -- wrongly reports zero observer notes.
        non_tfop = [n for n, g in zip(notes, groups) if g != "tfopwg"]
        rows.append(dict(
            tic=int(tic), y=y, n_notes=len(recs), chars=len(text),
            chars_non_tfopwg=sum(len(n) for n in non_tfop), n_non_tfopwg=len(non_tfop),
            has_master_disp=bool(disp), master_disp=disp.group(1).upper() if disp else None,
            has_any_disp=bool(ANY_DISP.search(text)),
            obs_has_disp=bool(ANY_DISP.search(" ".join(non_tfop))),
            obs_has_master=bool(MASTER_DISP.search(" ".join(non_tfop))),
            has_html=any("<" in (r.get("notes") or "") and ">" in (r.get("notes") or "") for r in recs),
            lastmods=[r.get("Lastmod") for r in recs], cached=cached))

    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"obsnotes_recon_{time.strftime('%Y-%m-%d')}.json"
    path.write_text(json.dumps(rows, indent=2))

    n = len(rows)
    withnotes = [r for r in rows if r["n_notes"]]
    print(f"sampled {n} TIC ({failed} hard failures) · {sum(r['cached'] for r in rows)} from cache")
    print(f"coverage      : {len(withnotes)}/{n} TIC have >=1 note   ({100*len(withnotes)/n:.0f}%)")
    print(f"notes / TIC   : median {statistics.median(r['n_notes'] for r in rows):.0f}  "
          f"mean {statistics.mean(r['n_notes'] for r in rows):.1f}  max {max(r['n_notes'] for r in rows)}")
    print(f"chars / TIC   : median {statistics.median(r['chars'] for r in rows):.0f}  "
          f"(TOI Comments median = 30)")
    print(f"HTML present  : {sum(r['has_html'] for r in rows)}/{n}")
    med_y1 = statistics.median([r["n_notes"] for r in rows if r["y"] == 1])
    med_y0 = statistics.median([r["n_notes"] for r in rows if r["y"] == 0])
    print(f"note-count vs label : median {med_y1:.0f} (y=1) vs {med_y0:.0f} (y=0)   <- leakage channel")

    print("\n--- LEAKAGE: explicit disposition text inside the notes ---")
    md = [r for r in withnotes if r["has_master_disp"]]
    ad = [r for r in withnotes if r["has_any_disp"]]
    print(f"'Master Disp:' present : {len(md)}/{len(withnotes)} TIC with notes  ({100*len(md)/max(len(withnotes),1):.0f}%)")
    print(f"any '*Disp:' present   : {len(ad)}/{len(withnotes)} TIC with notes  ({100*len(ad)/max(len(withnotes),1):.0f}%)")
    if md:
        agree = sum((r["master_disp"] in ("CP", "KP")) == (r["y"] == 1) for r in md)
        print(f"Master Disp agrees with the label on {agree}/{len(md)} TIC  "
              f"({100*agree/len(md):.0f}%)  <- this string IS the label")
        from collections import Counter
        print(f"  values: {dict(Counter(r['master_disp'] for r in md))}")

    print("\n--- observer notes separable from the tfopwg summary? ---")
    nz = [r for r in withnotes if r["n_non_tfopwg"]]
    print(f"TIC with >=1 observer note   : {len(nz)}/{len(withnotes)}")
    if nz:
        print(f"  observer chars / TIC, median : {statistics.median(r['chars_non_tfopwg'] for r in nz):.0f}")
        print(f"  observer notes / TIC, median : {statistics.median(r['n_non_tfopwg'] for r in nz):.0f}")
        leak = sum(r["obs_has_disp"] for r in nz)
        print(f"  observer text containing '*Disp:' : {leak}/{len(nz)}   <- residual leakage after dropping tfopwg")
    print(f"\nraw -> {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
