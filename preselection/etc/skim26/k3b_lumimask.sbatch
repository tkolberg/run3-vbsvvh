#!/bin/bash
#SBATCH --job-name=skim26_k3b_mask
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=2
#SBATCH --mem=4gb
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/skim26_smoke/logs/k3b_%j.log
# K3b: lumi-mask positive control. K4 task 1 skims runs 401614-401625, all below
# the first golden run (401630): the 2026 preselection must keep 0 of its events.
set -uo pipefail
T=/home/tkolberg.fsu/vbs/wt/skim26-rdf
O=/blue/avery/tkolberg.fsu/vbs/samples/skim/skim26_smoke/k3b
IN=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/Run3_Data_v15_2026_0Lep2FJ/JetMET0_Run2026A-PromptReco-v1_NANOAOD/output_1.root
echo "=== skim26 K3b lumi-mask control | job $SLURM_JOB_ID | tree $(git -C $T rev-parse --short HEAD)$(git -C $T diff --quiet || echo +dirty) | $(date -Is)"
rm -rf $O && mkdir -p $O
cd $T && source setup.sh >/dev/null 2>&1 && cd preselection
make -j2 > $O/make.log 2>&1 || { echo "BUILD FAILED"; exit 2; }
python3 - <<PY
import json
md = {"kind": "data", "year": "2026", "xsec": 1.0, "lumi": 25.79, "shortname": "JetMET", "do_ewk_corr": 0, "local_prefix": "", "sumw": 0.0}
json.dump({"samples": {"JetMET0_Run2026A-PromptReco-v1_NANOAOD": {"trees": ["Events"], "files": ["$IN"], "metadata": md}}}, open("$O/in.json", "w"))
PY
( while sleep 10; do echo "[hb] $(date +%T) outputs $(find $O/out -name '*.root' 2>/dev/null | wc -l)"; done ) & HB=$!
python3 run_rdf.py -i $O/in.json -p "" -o $O/out -n mask -c 0lep_2FJ -m local -r 3 -j 2 --store-hlt > $O/rdf.log 2>&1; rc=$?
kill $HB
f=$(find $O/out -name '*.root' | head -1)
nin=$(python3 -c "import ROOT;print(ROOT.TFile.Open('$IN').Get('Events').GetEntries())")
nout=$( [ -n "$f" ] && python3 -c "import ROOT;t=ROOT.TFile.Open('$f').Get('Events');print(t.GetEntries() if t else 0)" || echo 0)
echo "rdf rc=$rc input $nin events (all non-golden) -> output $nout"
[ $rc -eq 0 ] && [ "$nout" = "0" ] && echo "K3b PASS" || { echo "K3b FAIL"; tail -20 $O/rdf.log; exit 1; }
