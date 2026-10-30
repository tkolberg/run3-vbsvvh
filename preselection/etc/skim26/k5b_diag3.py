"""K5b third measurement: is the 0lep_1FJ_met 2026 data excess a pileup effect?

Preselection level (passes_<ch>_nom), data only, no analysis region:
  * 0lep_1FJ_met, 2026 / 2025 per fb^-1 in bins of good-AK4 multiplicity (len(jet_pt))
    and of pv_npvsGood;
  * N(0lep_1FJ_met) / N(0lep_2FJ) per npv bin, 2026 and 2025 (luminosity-free).
If the excess is pileup-driven, the 1FJ_met/2FJ rate rises with npv in both years and the
2026/2025 per-npv-bin ratio is near 1: the yield excess is then the shifted npv spectrum.
Usage: python k5b_diag3.py <outdir>   (writes k5b_diag3.json)
"""
import glob, json, os, sys
import numpy as np, uproot
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
L = {"2026": 25.79, "2025": 110.15}
DIRS = {
    ("0lep_1FJ_met", "2026"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_1FJ_met_r3_2026_data/JetMET*",
    ("0lep_1FJ_met", "2025"): "/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/0lep_1FJ_met_v30_r3_data/JetMET*Run2025*",
    ("0lep_2FJ", "2026"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_2FJ_r3_2026_data/JetMET*",
    ("0lep_2FJ", "2025"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_0lep2FJ_20261001_syst/0lep_2FJ_v30_r3_data/JetMET*Run2025*",
}
NPV = np.array([0, 20, 30, 40, 50, 60, 70, 200]); NJ = np.array([0, 3, 4, 5, 6, 7, 8, 30])
h = {}
for (ch, yr), pat in DIRS.items():
    flag = f"passes_{ch}_nom"; hn = np.zeros(len(NPV) - 1); hj = np.zeros(len(NJ) - 1)
    files = sorted(f for d in glob.glob(pat) for f in glob.glob(f"{d}/*.root"))
    for i, f in enumerate(files):
        t = uproot.open(f)["Events"]
        a = t.arrays([flag, "pv_npvsGood"], library="np"); m = a[flag] == 1
        hn += np.histogram(a["pv_npvsGood"][m], NPV)[0]
        if ch == "0lep_1FJ_met":
            nj = t["jet_pt"].array(library="ak"); import awkward as ak
            hj += np.histogram(np.asarray(ak.num(nj))[m], NJ)[0]
        if i % 50 == 0: print(f"[diag3] {ch} {yr} {i}/{len(files)}", flush=True)
    h[(ch, yr)] = (hn, hj)
lab = lambda b: [f"{b[i]}-{b[i+1]}" for i in range(len(b) - 1)]
res = {}
for nm, idx, B in (("npv", 0, NPV), ("njet", 1, NJ)):
    a6, a5 = h[("0lep_1FJ_met", "2026")][idx] / L["2026"], h[("0lep_1FJ_met", "2025")][idx] / L["2025"]
    res[f"1FJmet_2026_over_2025_per_fb_vs_{nm}"] = {k: (round(float(x / y), 3) if y else None) for k, x, y in zip(lab(B), a6, a5)}
    res[f"1FJmet_frac_2026_vs_{nm}"] = {k: round(float(x / a6.sum()), 4) for k, x in zip(lab(B), a6)}
    res[f"1FJmet_frac_2025_vs_{nm}"] = {k: round(float(x / a5.sum()), 4) for k, x in zip(lab(B), a5)}
for yr in L:
    n1, n2 = h[("0lep_1FJ_met", yr)][0], h[("0lep_2FJ", yr)][0]
    res[f"N1FJmet_over_N2FJ_vs_npv_{yr}"] = {k: (round(float(x / y), 4) if y else None) for k, x, y in zip(lab(NPV), n1, n2)}
json.dump(res, open(f"{OUT}/k5b_diag3.json", "w"), indent=1)
for k, v in res.items(): print(f"[diag3] {k}: {v}")
