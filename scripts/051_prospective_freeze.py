"""P1 — freeze the T0 snapshot for the prospective registry (PREREGISTRATION.md §11.14, A-45).

Every open TESS candidate's evidence trail is frozen here, as it stands at T0. The registry then
predicts those candidates' TFOPWG dispositions from this frozen text alone, and scores the
predictions only against dispositions assigned later. ExoFOP is a live archive, so **this
snapshot cannot be re-created after the fact**. Back up `data/prospective/` and
`data/prospective.duckdb` once the persist stage has run.

Stages (default: all four, in order; `--stage NAME` runs one):

    toi      ExoFOP bulk TOI table + NEA `toi` (TAP) -> data/prospective/raw/  (sha256 recorded)
    pull     ExoFOP notes for every TIC carrying an open (PC/APC) or labelled (CP/KP/FP/FA) TOI
             -> data/prospective/obsnotes/<tic>.json, cache-first
    verify   re-fetch every cached-empty TIC once (028's rule: a header-only answer twice = empty)
    persist  data/prospective.duckdb: toi_t0, notes_raw_t0, notes_text_t0, train_t0, predict_t0,
             freeze_manifest; and research/data/prospective_freeze_manifest.json

Everything that decides *what the text is* is imported unchanged from the published pipeline,
so the prospective corpus is built exactly as the TESS corpus was:
  * `scripts/01_ingest.py`        fetch_exofop, fetch_tap, TOI_COLS, the label mapping
  * `scripts/028_obsnotes_pull.py` fetch_raw (throttle-aware), plain (HTML -> text), the sentinel
    check, TFOPWG, and the per-TIC concatenation rule (observer notes, ascending Lastmod)
No other module's globals are written from here (defect 34).

Run:  .venv/bin/python scripts/051_prospective_freeze.py            # all stages (~20 min, $0)
      .venv/bin/python scripts/051_prospective_freeze.py --stage persist
Idempotent: yes, cache-first. Raw files and per-TIC notes are never re-downloaded once cached,
so a re-run reproduces the same snapshot and the same checksums. There is deliberately NO
--refresh flag: a re-pull would be a different T0, and A-45 pins this one by checksum.
"""
import argparse
import concurrent.futures as cf
import datetime
import hashlib
import importlib.util
import json
import pathlib
import sys
import time

import duckdb
import pandas as pd

ROOT = pathlib.Path(__file__).resolve().parent.parent
PDIR = ROOT / "data" / "prospective"
RAW = PDIR / "raw"
CACHE = PDIR / "obsnotes"
DB = ROOT / "data" / "prospective.duckdb"
MANIFEST = ROOT / "research" / "data" / "prospective_freeze_manifest.json"
STAMP = PDIR / "freeze_times.json"      # pull start/end, written once, never overwritten


def _load(name: str, file: str):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / file)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


ing = _load("ingest01", "01_ingest.py")
obs = _load("obsnotes028", "028_obsnotes_pull.py")

POSITIVE, NEGATIVE, OPEN = {"CP", "KP"}, {"FP", "FA"}, {"PC", "APC"}
NUMERIC = ["pl_orbper", "pl_trandep", "pl_trandurh", "pl_rade",
           "st_tmag", "st_teff", "st_rad", "st_logg"]


def sha256_bytes(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def frame_digest(df: pd.DataFrame) -> str:
    """sha256(to_csv)[:16], the project's matrix-checksum convention (HANDOFF, PROVENANCE)."""
    return sha256_bytes(df.to_csv(index=False).encode())[:16]


def now() -> str:
    return datetime.datetime.now(datetime.UTC).isoformat(timespec="seconds")


# --------------------------------------------------------------------------- stages

def stage_toi() -> int:
    RAW.mkdir(parents=True, exist_ok=True)
    ex_p, nea_p = RAW / "exofop_toi_T0.csv", RAW / "nea_toi_T0.csv"
    fresh = not (ex_p.exists() and nea_p.exists())
    ing.fetch_exofop(ex_p, refresh=False)
    ing.fetch_tap(nea_p, f"select {ing.TOI_COLS} from toi", refresh=False)
    if fresh:
        (RAW / "toi_fetched_utc.txt").write_text(now() + "\n")
    for p in (ex_p, nea_p):
        print(f"toi     : {p.relative_to(ROOT)}  {p.stat().st_size:,} bytes  "
              f"sha256 {sha256_bytes(p.read_bytes())[:16]}")
    return 0


def toi_frame() -> pd.DataFrame:
    """ExoFOP x NEA `toi`, joined exactly as scripts/01_ingest.py joins them."""
    ex = pd.read_csv(RAW / "exofop_toi_T0.csv", low_memory=False)
    nea = pd.read_csv(RAW / "nea_toi_T0.csv", low_memory=False)
    ex = ex.rename(columns={"TIC ID": "tic_id", "TOI": "toi", "Comments": "comment",
                            "TFOPWG Disposition": "tfopwg_disp_exofop",
                            "TESS Disposition": "tess_disp",
                            "Date TOI Alerted (UTC)": "date_toi_alerted",
                            "Date TOI Updated (UTC)": "date_toi_updated",
                            "Date Modified": "date_modified"})
    ex["toi"] = pd.to_numeric(ex["toi"], errors="coerce")
    nea["toi"] = pd.to_numeric(nea["toi"], errors="coerce")
    keep = ["tic_id", "toi", "tfopwg_disp_exofop", "tess_disp", "Sectors",
            "date_toi_alerted", "date_toi_updated", "date_modified"]
    df = ex[keep].merge(nea.drop(columns=["tid", "sectors"]), on="toi", how="inner",
                        validate="one_to_one")
    disp = df["tfopwg_disp"].fillna("")
    df["y"] = pd.Series(pd.NA, index=df.index, dtype="Int64")
    df.loc[disp.isin(POSITIVE), "y"] = 1
    df.loc[disp.isin(NEGATIVE), "y"] = 0
    df["is_open"] = disp.isin(OPEN)
    return df.sort_values("toi").reset_index(drop=True)


def target_tics() -> list[int]:
    df = toi_frame()
    keep = df[df.y.notna() | df.is_open]
    return sorted({int(t) for t in keep.tic_id})


def fetch_cached(tic: int) -> tuple[list[dict], bool]:
    """028's fetch_raw into THIS script's cache. 028's own cache and globals are untouched."""
    hit = CACHE / f"{tic}.json"
    if hit.exists():
        return json.loads(hit.read_text()), True
    recs = obs.fetch_raw(tic)
    obs.cache_write(hit, recs)
    return recs, False


def stage_pull(workers: int, sentinel_every: int) -> int:
    tics = target_tics()
    todo = [t for t in tics if not (CACHE / f"{t}.json").exists()]
    print(f"pull    : {len(tics):,} TIC total, {len(tics) - len(todo):,} cached, "
          f"{len(todo):,} to fetch, {workers} workers")
    if not todo:
        return 0
    if not STAMP.exists():
        STAMP.parent.mkdir(parents=True, exist_ok=True)
        STAMP.write_text(json.dumps({"pull_started_utc": now()}, indent=1))

    obs.check_sentinel("start")
    if obs.ABORT.is_set():
        print("\n".join(obs._abort_reason), file=sys.stderr)
        return 2
    t0, done, net, empties, failures = time.time(), 0, 0, 0, []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(fetch_cached, t): t for t in todo}
        for fut in cf.as_completed(futs):
            tic = futs[fut]
            done += 1
            try:
                recs, cached = fut.result()
            except obs.BadSchema as e:
                print(f"ABORT: {e}", file=sys.stderr)
                obs.ABORT.set()
                break
            except Exception as e:  # noqa: BLE001
                if obs.ABORT.is_set():
                    break
                failures.append((tic, f"{type(e).__name__}: {e}"))
                continue
            net += not cached
            empties += not recs
            if net and sentinel_every and net % sentinel_every == 0:
                obs.check_sentinel(f"after {net} fetches")
                if obs.ABORT.is_set():
                    break
            if done % 250 == 0 or done == len(todo):
                el = time.time() - t0
                print(f"  {done:,}/{len(todo):,}  {empties} empty  {len(failures)} failed  "
                      f"{done / el:.1f}/s", flush=True)
        if obs.ABORT.is_set():
            for f in futs:
                f.cancel()
    if obs.ABORT.is_set():
        print("\nABORTED:\n" + "\n".join(obs._abort_reason), file=sys.stderr)
        return 2
    print(f"pull    : {(time.time() - t0) / 60:.1f} min, {net:,} fetched, {empties:,} with no "
          f"notes, {len(failures)} failed")
    if failures:
        for tic, err in failures[:20]:
            print(f"    FAILED TIC {tic}: {err}", file=sys.stderr)
        return 1
    return 0


def stage_verify(workers: int) -> int:
    tics = target_tics()
    empty = [t for t in tics if (CACHE / f"{t}.json").exists()
             and json.loads((CACHE / f"{t}.json").read_text()) == []]
    print(f"verify  : re-fetching {len(empty):,} cached-empty TIC")
    if not empty:
        return 0
    obs.check_sentinel("verify start")
    if obs.ABORT.is_set():
        print("\n".join(obs._abort_reason), file=sys.stderr)
        return 2
    flipped, failed = [], []
    with cf.ThreadPoolExecutor(max_workers=workers) as ex:
        futs = {ex.submit(obs.fetch_raw, t): t for t in empty}
        for fut in cf.as_completed(futs):
            tic = futs[fut]
            try:
                recs = fut.result()
            except Exception as e:  # noqa: BLE001
                failed.append((tic, str(e)))
                continue
            if recs:
                obs.cache_write(CACHE / f"{tic}.json", recs)
                flipped.append(tic)
    obs.check_sentinel("verify end")
    print(f"verify  : {len(flipped)} of {len(empty):,} came back non-empty, {len(failed)} failed")
    if obs.ABORT.is_set():
        return 2
    if not flipped and not failed:
        stamp = json.loads(STAMP.read_text()) if STAMP.exists() else {}
        if "pull_verified_utc" not in stamp:
            stamp["pull_verified_utc"] = now()
            STAMP.write_text(json.dumps(stamp, indent=1))
    return 1 if (flipped or failed) else 0


def stage_persist() -> int:
    toi = toi_frame()
    tics = target_tics()
    missing = [t for t in tics if not (CACHE / f"{t}.json").exists()]
    if missing:
        print(f"persist : ABORT, {len(missing)} TIC not pulled (e.g. {missing[:5]})",
              file=sys.stderr)
        return 2

    raw, bad_group = [], {}
    for tic in tics:
        for i, r in enumerate(json.loads((CACHE / f"{tic}.json").read_text())):
            g = r.get("Groupname")
            if g is not None and g != obs.TFOPWG:
                bad_group.setdefault(g, []).append(tic)
            raw.append(dict(tic_id=tic, seq=i, note_id=r.get("ID"), username=r.get("Username"),
                            groupname=g, tag_id=r.get("TAG ID"), lastmod=r.get("Lastmod"),
                            notes_html=r.get("notes"), notes_text=obs.plain(r.get("notes") or ""),
                            is_tfopwg=(g == obs.TFOPWG)))
    if bad_group:  # A-10: the corpus definition is Groupname IS NULL
        print(f"persist : ABORT, Groupname outside {{'tfopwg', NULL}}: {sorted(bad_group)}",
              file=sys.stderr)
        return 2
    rawdf = pd.DataFrame(raw)

    # The per-TIC observer text, built exactly as 028's persist stage builds it.
    o = rawdf[~rawdf.is_tfopwg].copy()
    o["_sort"] = o.lastmod.fillna("9999")
    o = o.sort_values(["tic_id", "_sort", "seq"], kind="stable")
    text = o.groupby("tic_id").agg(
        n_notes_obs=("notes_text", "size"), n_authors=("username", "nunique"),
        text=("notes_text", lambda s: " ".join(x for x in s if x))).reset_index()
    text["n_chars"] = text.text.str.len()
    text = text[text.n_chars > 0]
    text = text.merge(rawdf.groupby("tic_id").size().rename("n_notes_all").reset_index(),
                      on="tic_id", how="left")
    text["last_obs_note"] = text.tic_id.map(o.groupby("tic_id").lastmod.max())

    joined = toi.merge(text.rename(columns={"text": "notes"}), on="tic_id", how="inner")
    train = joined[joined.y.notna()].sort_values("toi").reset_index(drop=True)
    pred = joined[joined.is_open].sort_values("toi").reset_index(drop=True)
    # A TIC that also carries a labelled TOI at T0: the S2a-style sensitivity arm (A-45 45.6).
    pred["tic_has_labelled_toi"] = pred.tic_id.isin(set(toi[toi.y.notna()].tic_id))

    files = sorted(CACHE.glob("*.json"), key=lambda p: int(p.stem))
    manifest_lines = "\n".join(f"{p.stem} {sha256_bytes(p.read_bytes())}" for p in files)
    stamp = json.loads(STAMP.read_text()) if STAMP.exists() else {}
    man = {
        "registration": "PREREGISTRATION.md §11.14 (A-45)",
        "persisted_utc": now(),
        "toi_fetched_utc": (RAW / "toi_fetched_utc.txt").read_text().strip()
        if (RAW / "toi_fetched_utc.txt").exists() else None,
        **stamp,
        "raw_sha256": {p.name: sha256_bytes(p.read_bytes())
                       for p in sorted(RAW.glob("*.csv"))},
        "obsnotes_cache_files": len(files),
        "obsnotes_manifest_sha256": sha256_bytes(manifest_lines.encode()),
        "notes_parsed": len(rawdf),
        "groupname_domain": {"tfopwg": int(rawdf.is_tfopwg.sum()),
                             "null": int(rawdf.groupname.isna().sum())},
        "toi_rows_joined": len(toi),
        "disposition_counts": toi.tfopwg_disp.fillna("<blank>").value_counts().to_dict(),
        "tic_targeted": len(tics),
        "tic_with_observer_text": int(len(text)),
        "train_t0": {"rows": len(train), "tic": int(train.tic_id.nunique()),
                     "base_rate": float(train.y.mean()), "sha16": frame_digest(train)},
        "predict_t0": {"rows": len(pred), "tic": int(pred.tic_id.nunique()),
                       "tic_shared_with_labelled": int(pred.tic_has_labelled_toi.sum()),
                       "sha16": frame_digest(pred)},
        "open_tois_total": int(toi.is_open.sum()),
        "open_tois_with_observer_text": len(pred),
        "digest_convention": "sha16 = sha256(DataFrame.to_csv(index=False))[:16], rows by toi",
    }

    con = duckdb.connect(str(DB))
    for name, frame in [("toi_t0", toi), ("notes_raw_t0", rawdf), ("notes_text_t0", text),
                        ("train_t0", train), ("predict_t0", pred)]:
        con.register("_f", frame)
        con.execute(f"create or replace table {name} as select * from _f")
        con.unregister("_f")
    mdf = pd.DataFrame([{"key": k, "value": json.dumps(v)} for k, v in man.items()])
    con.register("_m", mdf)
    con.execute("create or replace table freeze_manifest as select * from _m")
    con.close()

    MANIFEST.parent.mkdir(parents=True, exist_ok=True)
    MANIFEST.write_text(json.dumps(man, indent=2) + "\n")
    w = 30
    for k in ["toi_rows_joined", "tic_targeted", "tic_with_observer_text", "notes_parsed",
              "open_tois_total", "open_tois_with_observer_text"]:
        print(f"{k:<{w}}: {man[k]:,}")
    print(f"{'train_t0':<{w}}: {man['train_t0']}")
    print(f"{'predict_t0':<{w}}: {man['predict_t0']}")
    print(f"{'obsnotes manifest sha256':<{w}}: {man['obsnotes_manifest_sha256']}")
    print(f"\nwrote {DB.relative_to(ROOT)} and {MANIFEST.relative_to(ROOT)}")
    print("BACK UP data/prospective/ and data/prospective.duckdb: this snapshot cannot be re-pulled.")
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--stage", choices=["toi", "pull", "verify", "persist"])
    ap.add_argument("--workers", type=int, default=5)
    ap.add_argument("--sentinel-every", type=int, default=200)
    a = ap.parse_args()
    if a.stage in (None, "toi"):
        if stage_toi():
            return 1
    if a.stage in (None, "pull"):
        rc = stage_pull(a.workers, a.sentinel_every)
        if rc:
            return rc
    if a.stage in (None, "verify"):
        rc = stage_verify(a.workers)
        if rc == 2 or (rc and a.stage is None):
            print("verify flipped or failed some TIC: re-run until it flips nothing, "
                  "then run --stage persist", file=sys.stderr)
            return rc
    if a.stage in (None, "persist"):
        return stage_persist()
    return 0


if __name__ == "__main__":
    sys.exit(main())
