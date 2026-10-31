#!/usr/bin/env python3
"""K7 gap 3 check. mode 'jsons OUT': one 2026 signal skim file as year 2026 and,
as control, the same file as 2025. mode 'check OUT': read the RDF outputs and
assert 2026 has no b-tag JES/JER companion branches while 2025 keeps them, and
both keep the coarse b-tag weights."""
import glob, json, os, sys
import uproot

SIG = "/home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/merged_jsons/merged_0lep_1FJ_met_r3_2026_sig_20261029235128424575.json"
mode, out = sys.argv[1], sys.argv[2]
if mode == "jsons":
    d = json.load(open(SIG))["samples"]
    name = sorted(d)[0]
    s = d[name]
    one = dict(s, files=s["files"][:1])
    os.makedirs(out, exist_ok=True)
    json.dump({"samples": {name: one}}, open(f"{out}/sig26.json", "w"), indent=1)
    n25 = name.replace("Summer24for2026", "Summer24for2025")
    m25 = dict(one["metadata"], year="2025", lumi=110.84)
    json.dump({"samples": {n25: dict(one, metadata=m25)}}, open(f"{out}/sig25.json", "w"), indent=1)
    print("jsons:", name, one["files"][0])
    sys.exit(0)

rc = 0
for tag, expect_comp in (("sig26", False), ("sig25", True)):
    files = glob.glob(f"{out}/out_{tag}/**/*.root", recursive=True)
    if not files:
        print(f"[{tag}] no output"); rc = 1; continue
    keys = set(uproot.open(files[0])["Events"].keys())
    comp = sorted(k for k in keys if k.startswith("weightsyst_jes") or k == "weightsyst_jer")
    coarse = [k for k in ("weightsyst_btag_HF_correlated", "weightsyst_btag_LF_correlated") if k in keys]
    jes_kin = sum(k.startswith("Jet_pt_jes") for k in keys)
    ok = (bool(comp) == expect_comp) and len(coarse) == 2 and jes_kin > 0
    rc |= not ok
    print(f"[{tag}] {'PASS' if ok else 'FAIL'} companions={len(comp)} {comp[:3]} "
          f"coarse={coarse} Jet_pt_jes*={jes_kin}")
sys.exit(rc)
