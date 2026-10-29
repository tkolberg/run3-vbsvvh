"""K3 smoke inputs: one-file sample JSONs for the 2026 era (and a 2025 control)."""
import json, os, sys
k2, out = sys.argv[1], sys.argv[2]
V30 = "/cmsuf/data/store/user/phchang/skim/VBSVVH_skim_v30"
TT = "TTto4Q_TuneCP5_13p6TeV_powheg-pythia8_RunIII2024Summer24NanoAODv15-150X_mcRun3_2024_realistic_v2-v2_NANOAODSIM"
LUMI = {"2026": 25.79, "2025": 110.84}

def write(name, ds, f, kind, year, short):
    assert os.path.exists(f), f
    md = {"kind": kind, "year": year, "xsec": 1.0, "lumi": LUMI[year], "shortname": short,
          "do_ewk_corr": 0, "local_prefix": "", "sumw": 0.0 if kind == "data" else 1.0}
    json.dump({"samples": {ds: {"trees": ["Events"], "files": [f], "metadata": md}}},
              open(f"{out}/{name}.json", "w"), indent=1)
    print("json", name, year, f)

for ch, tag in (("0lep_2FJ", "0Lep2FJ"), ("0lep_1FJ_met", "0Lep1FJ")):
    write(f"data26_{ch}", "JetMET0_Run2026B-PromptReco-v1_NANOAOD", f"{k2}/head26_{tag}_out.root", "data", "2026", "JetMET")
    mc = f"{V30}/Run3_Bkg_v15_v30_{tag}/{TT}/output_1.root"
    write(f"mc26_{ch}", TT + "Summer24for2026", mc, "bkg", "2026", "TTto4Q_TuneCP5_13p6TeV")
    write(f"mc25_{ch}", TT + "Summer24for2025", mc, "bkg", "2025", "TTto4Q_TuneCP5_13p6TeV")
