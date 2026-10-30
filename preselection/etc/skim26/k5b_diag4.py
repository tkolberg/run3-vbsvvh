"""K5b fourth measurement: efficiency of the 0lep_1FJ_met trigger per year.

The 0lep_2FJ data ntuples carry no MET-trigger requirement and store the HLT bits, so
among their preselected events, per bin of offline met_pt, the fraction firing
HLT_PFMETNoMu120_PFMHTNoMu120_IDTight measures that path's efficiency on a jet-dominated
sample, 2026 vs 2025 (and per 2026 era). A plateau lower in 2025 than in 2026 by ~1.3
explains the 0lep_1FJ_met excess. Preselection level only: no analysis region.
Usage: python k5b_diag4.py <outdir>   (writes k5b_diag4.json)
"""
import glob, json, os, re, sys
import numpy as np, uproot
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
HLT = "HLT_PFMETNoMu120_PFMHTNoMu120_IDTight"
DIRS = {"2026": "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_2FJ_r3_2026_data/JetMET*",
        "2025": "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_0lep2FJ_20261001_syst/0lep_2FJ_v30_r3_data/JetMET*Run2025*"}
B = np.array([0, 100, 150, 200, 250, 300, 400, 600, 2000])
res = {}
for yr, pat in DIRS.items():
    per = {}
    for d in sorted(glob.glob(pat)):
        era = re.search(r"Run20\d\d([A-Z])", d).group(1)
        num, den = per.setdefault(era, (np.zeros(len(B) - 1), np.zeros(len(B) - 1)))
        for f in glob.glob(f"{d}/*.root"):
            t = uproot.open(f)["Events"]
            if HLT not in t.keys(): continue
            a = t.arrays(["passes_0lep_2FJ_nom", "met_pt", HLT], library="np"); m = a["passes_0lep_2FJ_nom"] == 1
            den += np.histogram(a["met_pt"][m], B)[0]; num += np.histogram(a["met_pt"][m & (a[HLT] == 1)], B)[0]
        print(f"[diag4] {yr} {os.path.basename(d)}", flush=True)
    tn = sum(v[0] for v in per.values()); td = sum(v[1] for v in per.values())
    eff = lambda n, d: {f"{B[i]}-{B[i+1]}": [round(float(n[i] / d[i]), 4), round(float(np.sqrt(n[i] * (d[i] - n[i]) / d[i]**3)), 4), int(d[i])] if d[i] else None for i in range(len(d))}
    res[yr] = {"all": eff(tn, td), **{e: eff(*v) for e, v in sorted(per.items())}}
json.dump(res, open(f"{OUT}/k5b_diag4.json", "w"), indent=1)
for yr in res:
    for e, v in res[yr].items(): print(f"[diag4] {yr} {e}: {v}")
