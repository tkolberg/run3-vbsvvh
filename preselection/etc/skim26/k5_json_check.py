"""K5: each 2026 MC JSON (Summer24for2026) must equal its Summer24for2025 twin in file
count, sumw and xsec, with year 2026 and lumi 25.79; data JSONs list every skim file.
Usage (from preselection/etc): python skim26/k5_json_check.py
"""
import glob, json, os, sys
bad = 0; n = {"mc": 0, "data": 0}
for p in sorted(glob.glob("input_sample_jsons_2026/run3/*/*/*.json")):
    d = json.load(open(p)); (name, s), = d["samples"].items(); md = s["metadata"]
    if md["year"] != "2026" or abs(md["lumi"] - 25.79) > 1e-9:
        bad += 1; print("ERA", p, md["year"], md["lumi"])
    if md["kind"] == "data":
        n["data"] += 1
        ddir = os.path.dirname(os.path.join(md["local_prefix"], s["files"][0]))
        on_disk = len([f for f in os.listdir(ddir) if f.startswith("output_") and f.endswith(".root")])
        if len(s["files"]) != on_disk:
            bad += 1; print("DATA FILES", p, len(s["files"]), on_disk)
        continue
    n["mc"] += 1
    # twin JSON is named <year>_<shortname>.json; same shortname, year 2025
    b = os.path.basename(p)
    twin = os.path.join(os.path.dirname(p).replace("input_sample_jsons_2026", "input_sample_jsons"), "2025_" + b[len("2026_"):])
    if not os.path.exists(twin):
        bad += 1; print("NO TWIN", twin); continue
    t = json.load(open(twin)); (_, ts), = t["samples"].items(); tm = ts["metadata"]
    if len(s["files"]) != len(ts["files"]) or abs(md["sumw"] - tm["sumw"]) > 1e-6 * abs(tm["sumw"]) or md["xsec"] != tm["xsec"]:
        bad += 1; print("TWIN DIFF", os.path.basename(p), len(s["files"]), len(ts["files"]), md["sumw"], tm["sumw"])
print("K5 JSON CHECK", "PASS" if not bad else f"FAIL {bad}", n)
sys.exit(1 if bad else 0)
