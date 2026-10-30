"""K5b second measurement: is the 0lep_1FJ_met 2026 data excess detector-localised?

0lep_1FJ_met data with met_pt > 250 GeV (preselection level, no analysis region), per fb^-1:
  * met_phi in 36 bins, 2026 / 2025;
  * leading good AK4 jet (highest jet_pt; jet_* is not pT-ordered) in eta x phi cells,
    2026 vs 2025 x lumi; cells ranked by Poisson pull.
A uniform 2026/2025 ratio in phi and over the jet map points at a global cause (trigger,
pileup); spikes or hot cells point at detector regions not covered by the 2026 veto map.
Usage: python k5b_diag2.py <outdir>   (writes k5b_diag2.json, k5b_diag2.png)
"""
import glob, json, os, sys
import numpy as np, uproot
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
L = {"2026": 25.79, "2025": 110.15}
DIRS = {"2026": "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_1FJ_met_r3_2026_data/JetMET*",
        "2025": "/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/0lep_1FJ_met_v30_r3_data/JetMET*Run2025*"}
PHI = np.linspace(-np.pi, np.pi, 37); ETA = np.linspace(-5, 5, 41); JPHI = np.linspace(-np.pi, np.pi, 33)
h = {}
for yr, pat in DIRS.items():
    hp = np.zeros(36); hj = np.zeros((40, 32))
    files = sorted(f for d in glob.glob(pat) for f in glob.glob(f"{d}/*.root"))
    for i, f in enumerate(files):
        a = uproot.open(f)["Events"].arrays(["passes_0lep_1FJ_met_nom", "met_pt", "met_phi", "jet_pt", "jet_eta", "jet_phi"], library="ak")
        a = a[(a["passes_0lep_1FJ_met_nom"] == 1) & (a["met_pt"] > 250)]
        hp += np.histogram(np.asarray(a["met_phi"]), PHI)[0]
        import awkward as ak
        has = ak.num(a["jet_pt"]) > 0; b = a[has]; j = ak.argmax(b["jet_pt"], axis=1, keepdims=True)
        hj += np.histogram2d(np.asarray(ak.flatten(b["jet_eta"][j])), np.asarray(ak.flatten(b["jet_phi"][j])), [ETA, JPHI])[0]
        if i % 50 == 0: print(f"[diag2] {yr} {i}/{len(files)} files", flush=True)
    h[yr] = (hp, hj)
s = L["2026"] / L["2025"]
p6, p5 = h["2026"][0], h["2025"][0] * s
j6, j5 = h["2026"][1], h["2025"][1] * s
tot = j6.sum() / j5.sum()                      # global excess, divided out of the cell pulls
with np.errstate(divide="ignore", invalid="ignore"):
    rphi = p6 / p5
    pull = (j6 - tot * j5) / np.sqrt(j6 + tot**2 * h["2025"][1] * s**2)
res = {"global_ratio_met250": round(float(tot), 3),
       "met_phi_ratio": [round(float(x), 3) for x in rphi],
       "met_phi_chi2_ndf_flat": round(float(np.nansum((p6 - tot * p5)**2 / (p6 + tot**2 * h["2025"][0] * s**2))) / 35, 2)}
idx = np.dstack(np.unravel_index(np.argsort(-np.nan_to_num(pull).ravel()), pull.shape))[0][:10]
res["hot_cells"] = [{"eta": [float(ETA[i]), float(ETA[i + 1])], "phi": [round(float(JPHI[k]), 2), round(float(JPHI[k + 1]), 2)],
                     "n2026": int(j6[i, k]), "n2025_scaled": round(float(j5[i, k]), 1), "pull": round(float(pull[i, k]), 1)} for i, k in idx]
res["excess_in_top10_cells_frac"] = round(float(sum(j6[i, k] - tot * j5[i, k] for i, k in idx) / max(j6.sum() - j5.sum(), 1)), 3)
fig, ax = plt.subplots(1, 2, figsize=(13, 4.5))
ax[0].step(0.5 * (PHI[1:] + PHI[:-1]), rphi, where="mid"); ax[0].axhline(tot, ls="--", color="k")
ax[0].set_xlabel("MET $\\phi$ (MET > 250 GeV)"); ax[0].set_ylabel("2026 / 2025 per fb$^{-1}$")
m = ax[1].pcolormesh(ETA, JPHI, pull.T, cmap="RdBu_r", vmin=-8, vmax=8); fig.colorbar(m, ax=ax[1], label="pull vs global ratio")
ax[1].set_xlabel("leading jet $\\eta$"); ax[1].set_ylabel("leading jet $\\phi$")
fig.tight_layout(); fig.savefig(f"{OUT}/k5b_diag2.png", dpi=110)
json.dump(res, open(f"{OUT}/k5b_diag2.json", "w"), indent=1)
print("[diag2]", json.dumps({k: v for k, v in res.items() if k != "met_phi_ratio"}))
print("[diag2] met_phi ratio:", res["met_phi_ratio"])
