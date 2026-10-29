#!/bin/bash
#SBATCH --job-name=skim26_k3_smoke
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=12gb
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/skim26_smoke/logs/k3_%j.log
# K3 smoke: RDF preselection with the 2026 era on (a) K2's 2026 data skims and
# (b) one Summer24 MC skim file run as year 2026 and as year 2025 (control).
# Requeue-safe: clears its own outputs on start.
set -uo pipefail
T=/home/tkolberg.fsu/vbs/wt/skim26-rdf
S=/blue/avery/tkolberg.fsu/vbs/samples/skim/skim26_smoke
O=$S/k3
echo "=== skim26 K3 RDF smoke | job ${SLURM_JOB_ID:-local} on $(hostname) | tree $(git -C $T rev-parse --short HEAD)$(git -C $T diff --quiet || echo +dirty) | $(date -Is)"
rm -rf $O && mkdir -p $O/json
cd $T && source setup.sh >/dev/null 2>&1 && cd preselection
make -j4 > $O/make.log 2>&1 || { echo "BUILD FAILED"; tail -30 $O/make.log; exit 2; }
echo "[build] ok"
python3 $T/preselection/etc/skim26/k3_jsons.py $S/k2 $O/json || exit 3
( while sleep 10; do echo "[hb] $(date +%T) rdf outputs: $(find $O/out -name '*.root' 2>/dev/null | wc -l) files, $(du -sm $O/out 2>/dev/null | cut -f1) MB"; done ) & HB=$!
rc=0
for spec in data26_0lep_2FJ:0lep_2FJ data26_0lep_1FJ_met:0lep_1FJ_met mc26_0lep_2FJ:0lep_2FJ mc25_0lep_2FJ:0lep_2FJ mc26_0lep_1FJ_met:0lep_1FJ_met; do
  n=${spec%%:*}; ch=${spec#*:}
  t0=$(date +%s)
  python3 run_rdf.py -i $O/json/$n.json -p "" -o $O/out/$n -n $n -c $ch -m local -r 3 -j 4 --store-hlt > $O/$n.log 2>&1; r=$?
  echo "[rdf] $n channel=$ch rc=$r wall=$(( $(date +%s) - t0 ))s"; [ $r -ne 0 ] && { tail -15 $O/$n.log; rc=1; }
done
kill $HB
python3 $T/preselection/etc/skim26/k3_check.py $O || rc=1
echo "=== skim26 K3 RDF smoke done rc=$rc $(date -Is)"
exit $rc
