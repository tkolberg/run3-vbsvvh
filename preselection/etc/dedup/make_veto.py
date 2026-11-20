"""Per-file veto lists for data skims that hold the same event more than once.

A data skim built from two CRAB tasks of one dataset can carry every event of
their overlap twice, split across output files that land in different RDF
jobs. A first-seen filter inside one job cannot see the other copy, so the
choice of which copy survives is made here, once, over the whole dataset:
the copy in the first file (sorted path order) is kept, every later copy is
vetoed. RDF reads <veto_dir>/<input file basename>.u64 and drops those events
(utils.cpp: applyDedupVeto).

Key packing (must match utils.h: dedupKey): (run - 355000) << 50 | lumi << 37 | event,
with run in [355000, 371383], lumi < 8192, event < 2**37. Out-of-range keys abort.

usage: make_veto.py <out_dir> <skim_dir> [<skim_dir> ...]
"""
import glob, os, sys, time
import numpy as np
import uproot

RUN0, RUN_BITS, LUMI_BITS, EVT_BITS = 355000, 14, 13, 37


def pack(run, lumi, evt):
    run = run.astype(np.int64) - RUN0
    if run.min() < 0 or run.max() >= 1 << RUN_BITS or lumi.max() >= 1 << LUMI_BITS or evt.max() >= 1 << EVT_BITS:
        raise SystemExit(f"key out of range: run {run.min()+RUN0}-{run.max()+RUN0} lumi<= {lumi.max()} event<= {evt.max()}")
    return (run.astype(np.uint64) << np.uint64(LUMI_BITS + EVT_BITS)) | (lumi.astype(np.uint64) << np.uint64(EVT_BITS)) | evt.astype(np.uint64)


def main(out, dirs):
    t0 = time.time(); last = 0
    files = sorted(f for d in dirs for f in glob.glob(f"{d}/output_*.root"))
    names = [os.path.basename(f) for f in files]
    if len(set(names)) != len(names):
        raise SystemExit("two skim dirs share an output basename; give one dataset per call")
    keys, fidx = [], []
    for i, f in enumerate(files):
        with uproot.open(f) as F:
            a = F["Events"].arrays(["run", "luminosityBlock", "event"], library="np")
        keys.append(pack(a["run"], a["luminosityBlock"], a["event"])); fidx.append(np.full(len(keys[-1]), i, np.int32))
        if time.time() - last > 10:
            last = time.time(); print(f"heartbeat files_read={i+1}/{len(files)} events={sum(map(len, keys))} t={int(last-t0)}s", flush=True)
    k = np.concatenate(keys); fi = np.concatenate(fidx)
    first = np.zeros(len(k), bool); first[np.unique(k, return_index=True)[1]] = True
    # a file never holds two copies itself (audit: same_file 0); if it did, the later row is vetoed by key
    # in its own file too, so check it rather than assume it
    os.makedirs(out, exist_ok=True)
    n_veto = 0
    for i, f in enumerate(files):
        sel = (fi == i)
        v = np.unique(k[sel & ~first])
        if np.intersect1d(v, k[sel & first]).size:
            raise SystemExit(f"{f}: same event twice inside one file; a key veto would drop both")
        if v.size:
            v.astype("<u8").tofile(f"{out}/{names[i]}.u64"); n_veto += v.size
    # for each vetoed file, the file holding most of the kept copies (used to pick test pairs)
    order = np.argsort(k, kind="stable"); ks = k[order]; fs = fi[order]
    starts = np.r_[0, np.flatnonzero(np.diff(ks)) + 1]
    keeper = np.repeat(fs[starts], np.diff(np.r_[starts, len(ks)]))
    pairs = {}
    for a, b in zip(fs[keeper != fs], keeper[keeper != fs]):
        pairs.setdefault(int(a), {}).setdefault(int(b), 0); pairs[int(a)][int(b)] += 1
    with open(f"{out}/pairs.txt", "w") as P:
        for a, d in sorted(pairs.items()):
            b, c = max(d.items(), key=lambda x: x[1])
            P.write(f"{files[a]} {files[b]} {c} {int((fi == a).sum())}\n")
    n = len(k); u = int(first.sum())
    print(f"dedup files={len(files)} events={n} unique={u} vetoed={n_veto} ({n_veto/max(1,n):.4%}) "
          f"files_with_veto={len(glob.glob(out+'/*.u64'))} out={out}", flush=True)
    assert n - u == n_veto


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2:])
