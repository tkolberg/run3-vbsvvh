#!/usr/bin/env python3
"""Link farm for the 2026 era: Summer24 MC serves 2026 as it serves 2025.

For each 0-lepton channel's MC (and the shared signal skim), every 2024Prompt dataset in
dataset_names_ref gets  <dataset>Summer24for2026 -> <v30 skim dir of dataset>
under SKIM_ROOT_2026 (our /blue tree; the v30 skim tree is not ours to write).
Absolute links: the jobs read the /cmsuf mount directly.

    python3 make_2026_era_links.py            # dry run
    python3 make_2026_era_links.py --apply
"""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import dataset_names_ref as ref
from make_sample_jsons import SKIM_PATH_DICT, SKIM_PATH_DICT_2026

apply = "--apply" in sys.argv
sfx = ref.MC_ERA_CLONE_SUFFIX_2026
n_new = n_ok = n_missing = 0
for ch in SKIM_PATH_DICT_2026:
    for (run, kind), dst in SKIM_PATH_DICT_2026[ch].items():
        if kind == "data": continue
        src = SKIM_PATH_DICT[ch][(run, kind)]
        have = set(os.listdir(src))
        base = [d["dataset_name"] for d in ref.datasets[("run3", kind)] if d["year"] == "2024Prompt"]
        for ds in base:
            if ds not in have:
                n_missing += 1
                continue
            target = os.path.realpath(os.path.join(src, ds))
            link = os.path.join(dst, ds + sfx)
            if os.path.islink(link) and os.readlink(link) == target:
                n_ok += 1
                continue
            n_new += 1
            if apply:
                os.makedirs(dst, exist_ok=True)
                os.symlink(target, link)
        print(f"{ch} {kind}: {src} -> {dst}")
print(f"links new {n_new}{'' if apply else ' (dry run)'}, already ok {n_ok}, "
      f"2024Prompt datasets not in this skim {n_missing}")
