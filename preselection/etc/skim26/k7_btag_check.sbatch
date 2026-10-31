#!/bin/bash
#SBATCH --job-name=skim26_k7_btag
#SBATCH --time=01:30:00
#SBATCH --cpus-per-task=4
#SBATCH --mem=12gb
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/skim26_smoke/logs/k7_btag_%j.log
# K7 gap 3: build the skim26/k7-gaps RDF and run one 2026 signal file with --systs
# as 2026 and as 2025; 2026 must carry no b-tag JES/JER companions. Requeue-safe.
set -uo pipefail
T=/home/tkolberg.fsu/vbs/wt/skim26-k7-rdf
O=/blue/avery/tkolberg.fsu/vbs/samples/skim/skim26_smoke/k7
echo "=== skim26 K7 b-tag companion check | job ${SLURM_JOB_ID:-local} on $(hostname) | tree $(git -C $T rev-parse --short HEAD)$(git -C $T diff --quiet || echo +dirty) | $(date -Is)"
rm -rf $O && mkdir -p $O
cd $T && source setup.sh >/dev/null 2>&1 && cd preselection
( while sleep 10; do echo "[hb] $(date +%T) objects built $(find build -name '*.o' 2>/dev/null | wc -l), rdf outputs $(find $O -name '*.root' 2>/dev/null | wc -l)"; done ) & HB=$!
make -j4 > $O/make.log 2>&1 || { kill $HB; echo "BUILD FAILED"; tail -30 $O/make.log; exit 2; }
echo "[build] ok"
python3 etc/skim26/k7_btag_check.py jsons $O || { kill $HB; exit 3; }
rc=0
for n in sig26 sig25; do
  t0=$(date +%s)
  python3 run_rdf.py -i $O/$n.json -p "" -o $O/out_$n -n $n -c 0lep_1FJ_met -m local -r 3 -j 4 --systs > $O/$n.log 2>&1; r=$?
  echo "[rdf] $n rc=$r wall=$(( $(date +%s) - t0 ))s"; [ $r -ne 0 ] && { tail -15 $O/$n.log; rc=1; }
done
kill $HB
python3 etc/skim26/k7_btag_check.py check $O || rc=1
echo "=== skim26 K7 b-tag companion check done rc=$rc $(date -Is)"
exit $rc
