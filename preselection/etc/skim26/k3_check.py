"""K3 smoke checks on the RDF outputs (preselection level only, no analysis region).

data: year == 2026 for every event; every (run, LS) in the 2026 golden JSON;
      how many input events sat in non-golden LS (the mask's test population).
mc:   the same input run as 2026 and as 2025: leading-jet pT must differ
      (different JEC/JER tables), the control that the 2026 row is read.
"""
import glob, json, sys
import numpy as np, uproot
O = sys.argv[1]
G = json.load(open("/home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/corrections/goldenJson/Cert_Collisions2026_401624_403937_golden.json"))
def golden(r, l):
    return np.array([any(a <= y <= b for a, b in G.get(str(x), [])) for x, y in zip(r, l)], dtype=bool)
def arrays(name, br):
    fs = sorted(glob.glob(f"{O}/out/{name}/**/*.root", recursive=True))
    if not fs: return None
    return uproot.concatenate([f + ":Events" for f in fs], br, library="ak")
ok = True
for ch in ("0lep_2FJ", "0lep_1FJ_met"):
    fs = sorted(glob.glob(f"{O}/out/data26_{ch}/**/*.root", recursive=True))
    if not fs:
        print(f"data26 {ch}: NO OUTPUT"); ok = False; continue
    keys = set(uproot.open(fs[0])["Events"].keys())
    br = ["run", "luminosityBlock"] + (["year"] if "year" in keys else [])
    a = arrays(f"data26_{ch}", br)
    bad = int((~golden(np.asarray(a.run), np.asarray(a.luminosityBlock))).sum())
    years = sorted(set(np.asarray(a.year).tolist())) if "year" in keys else "no year branch"
    inp = list(json.load(open(f"{O}/json/data26_{ch}.json"))["samples"].values())[0]["files"][0]
    t = uproot.open(inp)["Events"].arrays(["run", "luminosityBlock"], library="np")
    ng = int((~golden(t["run"], t["luminosityBlock"])).sum())
    print(f"data26 {ch}: out {len(a)} events, years {years}, non-golden in output {bad}; "
          f"input {len(t['run'])} events of which {ng} non-golden")
    print(f"  HLT branches {sum(k.startswith('HLT_') for k in keys)}, Jet_jecFactor {'Jet_jecFactor' in keys}")
    ok &= bad == 0 and (years == "no year branch" or years == ["2026"])
for ch in ("0lep_2FJ", "0lep_1FJ_met"):
    a6 = arrays(f"mc26_{ch}", ["event", "luminosityBlock", "Jet_pt"])
    a5 = arrays(f"mc25_{ch}", ["event", "luminosityBlock", "Jet_pt"]) if ch == "0lep_2FJ" else None
    if a6 is None:
        print(f"mc26 {ch}: NO OUTPUT"); ok = False; continue
    if a5 is None:
        print(f"mc26 {ch}: out {len(a6)} events"); continue
    def lead(a):
        m = np.asarray([len(x) > 0 for x in a.Jet_pt])
        return {(int(l), int(e)): float(p[0]) for l, e, p in zip(a.luminosityBlock[m], a.event[m], a.Jet_pt[m])}
    d6, d5 = lead(a6), lead(a5)
    com = d6.keys() & d5.keys()
    diff = sum(abs(d6[k] - d5[k]) > 1e-3 * d5[k] for k in com)
    print(f"mc {ch}: out 2026 {len(a6)} / 2025 {len(a5)} events; leading-jet pT differs in {diff}/{len(com)} common events")
    ok &= len(com) > 0 and diff > 0
print("K3 CHECK", "PASS" if ok else "FAIL")
sys.exit(0 if ok else 1)
