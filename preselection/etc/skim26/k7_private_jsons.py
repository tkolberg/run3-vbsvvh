#!/usr/bin/env python3
"""2026 twins of the private VBS WW (lnuqq) and VZ (nunu qq) 0lep_1FJ_met backgrounds.

The v30 production runs these private Summer24 skims twice (2024Prompt and
Summer24for2025). This writes the third copy, Summer24for2026, from the 2025
JSONs: same files, same xsec and sumw, year 2026, lumi 25.79 (the 2026 MC stamp,
make_sample_jsons LUMI_DICT), sample name suffix Summer24for2026.

    python3 k7_private_jsons.py OUTDIR
writes OUTDIR/{vbsww,vbsvz}/2026_<sample>.json
"""
import glob, json, os, sys

V30 = "/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/private_jsons"
SOURCES = {"vbsww": f"{V30}/2025_*.json", "vbsvz": f"{V30}/0lep_1FJ_vbsvz_20261021/2025_*.json"}
LUMI_2026 = 25.79
OLD, NEW = "Summer24for2025", "Summer24for2026"

out = sys.argv[1]
n = 0
for tier, pattern in SOURCES.items():
    srcs = sorted(glob.glob(pattern))
    if not srcs:
        sys.exit(f"no 2025 JSONs at {pattern}")
    os.makedirs(f"{out}/{tier}", exist_ok=True)
    for src in srcs:
        d = json.load(open(src))
        samples = {}
        for name, s in d["samples"].items():
            if not name.endswith(OLD) or s["metadata"]["year"] != "2025":
                sys.exit(f"{src}: {name} is not a 2025 Summer24 clone")
            missing = [f for f in s["files"] if not os.path.exists(f)]
            if missing:
                sys.exit(f"{src}: {len(missing)} input files missing, e.g. {missing[0]}")
            meta = dict(s["metadata"], year="2026", lumi=LUMI_2026)
            samples[name[: -len(OLD)] + NEW] = dict(s, metadata=meta)
        dst = f"{out}/{tier}/" + os.path.basename(src).replace("2025_", "2026_", 1)
        json.dump({**d, "samples": samples}, open(dst, "w"), indent=1)
        for name, s in samples.items():
            n += 1
            print(f"{tier} {name} files={len(s['files'])} xsec={s['metadata']['xsec']} "
                  f"sumw={s['metadata'].get('sumw')} -> {dst}")
print(f"wrote {n} samples")
