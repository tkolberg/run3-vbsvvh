"""K5b first measurement: why 0lep_1FJ_met data is 1.30x 2025 per fb^-1 (0lep_2FJ: 1.01).

From the existing preselection outputs (events with passes_<ch>_nom), 2026 vs 2025 data:
  * per-fb^-1 spectra of met_pt, met_uncorrPt (no JEC propagation) and pv_npvsGood;
  * per run, N(0lep_1FJ_met) / N(0lep_2FJ), a luminosity-free rate.
Reading the result: an excess near the MET threshold that vanishes in met_uncorrPt
points at JEC / type-1 MET; an excess in the tail at MET filters; a few runs at the menu;
flat at trigger or pileup (with npv shifted). Preselection level only: no analysis region.
Writes k5b_diag.json and k5b_diag.png in <outdir>.
Usage: python k5b_diag.py <outdir>
"""
import collections, glob, json, os, sys
import numpy as np, uproot
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
L = {"2026": 25.79, "2025": 110.15}
DIRS = {
    ("0lep_1FJ_met", "2026"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_1FJ_met_r3_2026_data/JetMET*",
    ("0lep_1FJ_met", "2025"): "/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/0lep_1FJ_met_v30_r3_data/JetMET*Run2025*",
    ("0lep_2FJ", "2026"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_2FJ_r3_2026_data/JetMET*",
    ("0lep_2FJ", "2025"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_0lep2FJ_20261001_syst/0lep_2FJ_v30_r3_data/JetMET*Run2025*",
}
BINS = {"met_pt": np.r_[0:400:20, 400, 500, 700, 1000], "met_uncorrPt": np.r_[0:400:20, 400, 500, 700, 1000],
        "pv_npvsGood": np.arange(0, 101, 4)}
hist = {}; runs = {}
for (ch, yr), pat in DIRS.items():
    flag = f"passes_{ch}_nom"; h = {v: np.zeros(len(b) - 1) for v, b in BINS.items()}; r = collections.Counter()
    files = sorted(f for d in glob.glob(pat) for f in glob.glob(f"{d}/*.root"))
    for i, f in enumerate(files):
        a = uproot.open(f)["Events"].arrays([flag, "run"] + (list(BINS) if ch == "0lep_1FJ_met" else []), library="np")
        m = a[flag] == 1
        for run, n in zip(*np.unique(a["run"][m], return_counts=True)): r[int(run)] += int(n)
        if ch == "0lep_1FJ_met":
            for v, b in BINS.items(): h[v] += np.histogram(np.clip(a[v][m], b[0], b[-1] - 1e-6), b)[0]
        if i % 50 == 0: print(f"[diag] {ch} {yr} {i}/{len(files)} files", flush=True)
    hist[(ch, yr)] = h; runs[(ch, yr)] = r
res = {"per_fb": {f"{c} {y}": sum(runs[(c, y)].values()) / L[y] for c, y in DIRS}}
res["ratio_1FJmet_over_2FJ"] = {y: sum(runs[("0lep_1FJ_met", y)].values()) / sum(runs[("0lep_2FJ", y)].values()) for y in L}
res["per_run_2026"] = {str(k): [runs[("0lep_1FJ_met", "2026")][k], runs[("0lep_2FJ", "2026")].get(k, 0)]
                       for k in sorted(runs[("0lep_1FJ_met", "2026")])}
fig, ax = plt.subplots(1, 4, figsize=(20, 4.5))
for i, (v, b) in enumerate(BINS.items()):
    c = 0.5 * (b[1:] + b[:-1]); w = np.diff(b)
    h6, h5 = hist[("0lep_1FJ_met", "2026")][v] / L["2026"], hist[("0lep_1FJ_met", "2025")][v] / L["2025"]
    ax[i].step(c, h6 / w, where="mid", label="2026"); ax[i].step(c, h5 / w, where="mid", label="2025")
    ax[i].set_yscale("log"); ax[i].set_xlabel(v); ax[i].set_ylabel("events / fb$^{-1}$ / unit"); ax[i].legend()
    with np.errstate(divide="ignore", invalid="ignore"):
        res[f"ratio_{v}"] = {f"{b[j]:g}-{b[j+1]:g}": round(float(h6[j] / h5[j]), 3) if h5[j] else None for j in range(len(c))}
rr = res["per_run_2026"]; ks = [k for k in rr if rr[k][1] > 0]
ax[3].plot([int(k) for k in ks], [rr[k][0] / rr[k][1] for k in ks], ".", label="2026 per run")
ax[3].axhline(res["ratio_1FJmet_over_2FJ"]["2025"], color="C1", label="2025 average")
ax[3].set_xlabel("run"); ax[3].set_ylabel("N(0lep_1FJ_met) / N(0lep_2FJ)"); ax[3].legend()
fig.tight_layout(); fig.savefig(f"{OUT}/k5b_diag.png", dpi=110)
json.dump(res, open(f"{OUT}/k5b_diag.json", "w"), indent=1)
print("[diag] per fb^-1", {k: round(v, 1) for k, v in res["per_fb"].items()})
print("[diag] 1FJ_met/2FJ", {k: round(v, 4) for k, v in res["ratio_1FJmet_over_2FJ"].items()})
for v in BINS: print(f"[diag] 2026/2025 {v}:", res[f"ratio_{v}"])
