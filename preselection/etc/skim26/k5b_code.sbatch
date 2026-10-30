#!/bin/bash
#SBATCH --job-name=skim26_k5b_code
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=12gb
#SBATCH --requeue
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/logs/k5b_code_%j.log
# K5b: is the 0lep_1FJ_met 2026/2025 data excess a code difference? Run our RDF tree
# (skim26/era2026) on the 2025 JetMET0 Run2025B skim files and compare passes_0lep_1FJ_met_nom
# with the 2025 reference production on the same inputs. Preselection level only.
set -uo pipefail
T=/home/tkolberg.fsu/vbs/wt/skim26-rdf
O=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/k5b_code
REF=/cmsuf/data/store/user/mmazza/vbsvvh/rdf/v30/0lep_1FJ_met_20261021_syst/0lep_1FJ_met_v30_r3_data/JetMET0_Run2025B-PromptReco-v1_NANOAOD
echo "=== skim26 K5b code-difference test | job $SLURM_JOB_ID | tree $(git -C $T rev-parse --short HEAD) | $(date -Is)"
rm -rf $O && mkdir -p $O
cd $T && source setup.sh >/dev/null 2>&1 && cd preselection
make -j4 > $O/make.log 2>&1 || { echo "BUILD FAILED"; tail -20 $O/make.log; exit 2; }
( while sleep 10; do echo "[hb] $(date +%T) outputs $(find $O/out -name '*.root' 2>/dev/null | wc -l)"; done ) & HB=$!
python3 run_rdf.py -i etc/input_sample_jsons/run3/data/0lep_1FJ/2025_JetMET0_Run2025B-PromptReco-v1_NANOAOD.json \
    -p /cmsuf/data/store/user/phchang/skim/ -o $O/out -n code -c 0lep_1FJ_met -m local -r 3 -j 4 --store-hlt > $O/rdf.log 2>&1; rc=$?
kill $HB; echo "[rdf] rc=$rc"; [ $rc -ne 0 ] && { tail -20 $O/rdf.log; exit 1; }
python3 - $O/out $REF <<'PY'
import glob, sys, ROOT
def n(pat):
    tot = 0
    for f in glob.glob(pat, recursive=True):
        t = ROOT.TFile.Open(f).Get("Events")
        if t: tot += t.GetEntries("passes_0lep_1FJ_met_nom==1")
    return tot
ours, ref = n(sys.argv[1] + "/**/*.root"), n(sys.argv[2] + "/*.root")
print(f"[code] 2025B JetMET0 passes_0lep_1FJ_met_nom: ours {ours}, reference {ref}, ratio {ours / ref if ref else float('nan'):.3f}")
PY
echo "=== skim26 K5b code test done $(date -Is)"
