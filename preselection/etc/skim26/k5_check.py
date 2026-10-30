"""K5 post-run check of the 2026 preselection (v30_2026), per channel and kind.

1. every job in job_list.txt has its output_<idx>.root with a readable Events tree
2. year == "2026" in every file; data runs inside the 2026 golden range
3. per file, preselected events <= skim events of its input (the RDF writes no input count)
4. data: passes_<ch>_nom events per fb^-1, 2026 vs 2025 (v30 production) -- preselection level
5. MC: sum(weight * passes_<ch>_nom) per dataset, 2026 vs 2025 twin x 25.79/110.84
Counts are preselection level only (no analysis region), so no blinding concern.
Usage: python k5_check.py [--no-ref] <task dir> [<task dir> ...]   (vbs-coffea env: uproot, numpy)
"""
import collections, glob, json, os, sys
import numpy as np, uproot
L26, L25 = 25.79, 110.84          # MC stamps (make_sample_jsons LUMI)
L25_DATA = 110.15                 # 2025 data, v30 skim (vbs_common DATA_LUMI_FB)
GOLDEN = (401624, 403937)
REF25 = {  # 2025 v30 productions with the same recipe (r3 data and bkg tiers)
    "0lep_2FJ": "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_0lep2FJ_20261001_syst/0lep_2FJ_v30_r3_*",
    "0lep_1FJ_met": "/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/0lep_1FJ_met_v30_r3_*",
}

def tally(files, flag, mc):
    n = 0.0
    for f in files:
        t = uproot.open(f)["Events"]
        if flag not in t.keys(): continue
        a = t.arrays([flag] + (["weight"] if mc else []), library="np")
        n += float(np.sum(a["weight"][a[flag] == 1])) if mc else int(np.sum(a[flag] == 1))
    return n

bad = collections.Counter()
noref = "--no-ref" in sys.argv   # structure checks only (quick test)
for task in [a for a in sys.argv[1:] if not a.startswith("--")]:
    cfgs = sorted(glob.glob(f"{task}/*/config.json"))
    sb = open(f"{task}/array.sbatch").read().split("\n")[-2].split()
    outdir, ch = sb[5], sb[6]
    per_ds = collections.defaultdict(list)
    # job_list.txt: <job dir> <sample> <job index>; single-job samples have no _<idx> dir suffix
    jobs = [l.split() for l in open(f"{task}/job_list.txt") if l.strip()]
    cfgs = [f"{task}/{d}/config.json" for d, _, _ in jobs]
    for c, (_, _, idx) in zip(cfgs, jobs):
        cfg = json.load(open(c)); (ds, s), = cfg["samples"].items()
        out = f"{outdir}/{ds}/output_{idx}.root"
        if not os.path.exists(out):
            bad["missing"] += 1; print("MISSING", out); continue
        try:
            t = uproot.open(out)["Events"]
            yr = t["year"].array(library="np", entry_stop=1)
        except Exception as e:
            bad["unreadable"] += 1; print("UNREADABLE", out, e); continue
        if t.num_entries and str(yr[0]) != "2026":
            bad["year"] += 1; print("YEAR", out, yr[0])
        if s["metadata"]["kind"] == "data" and t.num_entries:
            r = t["run"].array(library="np")
            if r.min() < GOLDEN[0] or r.max() > GOLDEN[1]:
                bad["run"] += 1; print("RUN", out, r.min(), r.max())
        nin = sum(uproot.open(f)["Events"].num_entries for f in s["files"])
        if t.num_entries > nin:
            bad["count"] += 1; print("COUNT", out, t.num_entries, nin)
        per_ds[ds].append(out)
    kind = json.load(open(cfgs[0]))["samples"].popitem()[1]["metadata"]["kind"]
    flag = [k for k in uproot.open(next(iter(per_ds.values()))[0])["Events"].keys() if k.startswith("passes_") and k.endswith("_nom")][0]
    print(f"\n{ch} {kind}: {sum(len(v) for v in per_ds.values())}/{len(cfgs)} outputs, flag {flag}")
    if noref: continue
    if kind == "data":
        n26 = sum(tally(v, flag, False) for v in per_ds.values())
        ref = [d for d in glob.glob(REF25[ch].split("_r3_")[0] + "_r3_data/JetMET*Run2025*")]
        n25 = sum(tally(glob.glob(f"{d}/*.root"), flag, False) for d in ref)
        print(f"  data per fb^-1: 2026 {n26 / L26:.1f}, 2025 {n25 / L25_DATA:.1f}, ratio {n26 / L26 / (n25 / L25_DATA):.3f}")
    else:
        for ds, v in sorted(per_ds.items()):
            twin = glob.glob(f"{REF25[ch]}/{ds.replace('Summer24for2026', 'Summer24for2025')}")
            if not twin: print(f"  {ds[:60]}: no 2025 twin"); continue
            w26 = tally(v, flag, True); w25 = tally(glob.glob(f"{twin[0]}/*.root"), flag, True) * L26 / L25
            print(f"  {ds[:60]}: 2026/2025-scaled {w26 / w25 if w25 else float('nan'):.3f}")
print("\nK5 CHECK", "PASS" if not bad else f"FAIL {dict(bad)}")
sys.exit(1 if bad else 0)
