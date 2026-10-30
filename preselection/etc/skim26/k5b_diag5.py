"""K5b fifth measurement: is the 2026 MET tail an xy offset of the offline PuppiMET?

MET-phi corrections are off in every year (corrections.cpp applyMETPhiCorrections is
commented out), so a 2026-only detector offset reaches met_pt unchanged. Per year and era:
  * mean (MEx, MEy) of trigger-free 0lep_2FJ data in the MET < 100 GeV bulk (the offset);
  * 0lep_2FJ per-fb^-1 MET spectra before and after subtracting that era's offset;
  * 0lep_1FJ_met per-fb^-1 counts vs met_phi (12 bins) and the same mean (MEx, MEy).
Reading: if the 2026/2025 2FJ ratio at 100-250 GeV (1.26-1.46 raw) returns to ~1 after the
subtraction, the excess is a 2026 MET xy offset. Preselection level only: no analysis region.
Usage: python k5b_diag5.py <outdir>   (writes k5b_diag5.json)
"""
import glob, json, os, re, sys
import numpy as np, uproot
OUT = sys.argv[1]; os.makedirs(OUT, exist_ok=True)
L = {"2026": 25.79, "2025": 110.15}
DIRS = {
    ("0lep_2FJ", "2026"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_2FJ_r3_2026_data/JetMET*",
    ("0lep_2FJ", "2025"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_0lep2FJ_20261001_syst/0lep_2FJ_v30_r3_data/JetMET*Run2025*",
    ("0lep_1FJ_met", "2026"): "/blue/avery/tkolberg.fsu/vbs/samples/run3-vbsvvh/v30_2026/0lep_1FJ_met_r3_2026_data/JetMET*",
    ("0lep_1FJ_met", "2025"): "/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/0lep_1FJ_met_v30_r3_data/JetMET*Run2025*",
}
B = np.array([0, 50, 100, 150, 200, 250, 300, 400, 600, 2000]); PB = np.linspace(-np.pi, np.pi, 13)


def load(ch, pat):
    """Per era: arrays of (mex, mey) for nominal-passing events."""
    per = {}
    for d in sorted(glob.glob(pat)):
        era = re.search(r"Run20\d\d([A-Z])", d).group(1)
        for f in glob.glob(f"{d}/*.root"):
            a = uproot.open(f)["Events"].arrays([f"passes_{ch}_nom", "met_pt", "met_phi"], library="np")
            m = a[f"passes_{ch}_nom"] == 1
            pt, ph = a["met_pt"][m], a["met_phi"][m]
            per.setdefault(era, []).append(np.c_[pt * np.cos(ph), pt * np.sin(ph)])
        print(f"[diag5] {ch} {os.path.basename(d)}", flush=True)
    return {e: np.concatenate(v) for e, v in per.items()}


res = {"offset": {}, "2FJ_raw": {}, "2FJ_corr": {}, "1FJmet_phi": {}, "1FJmet_offset": {}}
off = {}
for yr in L:
    xy = load("0lep_2FJ", DIRS[("0lep_2FJ", yr)])
    raw = np.zeros(len(B) - 1); cor = np.zeros(len(B) - 1)
    for e, v in xy.items():
        pt = np.hypot(*v.T); bulk = v[pt < 100]
        o = bulk.mean(0); off[(yr, e)] = o
        res["offset"][f"{yr} {e}"] = [round(float(o[0]), 3), round(float(o[1]), 3), int(len(bulk))]
        raw += np.histogram(pt, B)[0]; cor += np.histogram(np.hypot(*(v - o).T), B)[0]
    res["2FJ_raw"][yr] = (raw / L[yr]).tolist(); res["2FJ_corr"][yr] = (cor / L[yr]).tolist()
    xy1 = load("0lep_1FJ_met", DIRS[("0lep_1FJ_met", yr)])
    allv = np.concatenate(list(xy1.values()))
    res["1FJmet_phi"][yr] = (np.histogram(np.arctan2(allv[:, 1], allv[:, 0]), PB)[0] / L[yr]).tolist()
    res["1FJmet_offset"][yr] = {e: [round(float(x), 2) for x in v.mean(0)] + [int(len(v))] for e, v in xy1.items()}
json.dump(res, open(f"{OUT}/k5b_diag5.json", "w"), indent=1)
for k in ("2FJ_raw", "2FJ_corr"):
    r = np.array(res[k]["2026"]) / np.array(res[k]["2025"])
    print(f"[diag5] {k} 2026/2025 per MET bin {B.tolist()}: {np.round(r, 3).tolist()}")
print(f"[diag5] 1FJ_met 2026/2025 vs phi: {np.round(np.array(res['1FJmet_phi']['2026']) / np.array(res['1FJmet_phi']['2025']), 3).tolist()}")
print(f"[diag5] offsets (2FJ bulk, GeV): {res['offset']}")
print(f"[diag5] 1FJ_met mean (MEx, MEy): {res['1FJmet_offset']}")
