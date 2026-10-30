#!/bin/bash
#SBATCH --job-name=skim26_k5_jsons
#SBATCH --time=01:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4gb
#SBATCH --requeue
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/logs/k5_jsons_%j.log
# K5: 2026 sample JSONs (SKIM_PATH_SET=2026): JetMET data from our skim, Summer24for2026 MC
# from the link farm. Writes etc/input_sample_jsons_2026/ only; requeue-safe (rewrites all).
set -uo pipefail
T=/home/tkolberg.fsu/vbs/wt/skim26-rdf
echo "=== skim26 K5 sample JSONs | job $SLURM_JOB_ID | tree $(git -C $T rev-parse --short HEAD)$(git -C $T diff --quiet || echo +dirty) | $(date -Is)"
cd $T/preselection/etc
( while sleep 10; do echo "[hb] $(date +%T) jsons written $(find input_sample_jsons_2026 -name '*.json' 2>/dev/null | wc -l)"; done ) & HB=$!
SKIM_PATH_SET=2026 /home/tkolberg.fsu/envs/vbs-coffea/bin/python make_sample_jsons.py > $T/preselection/etc/skim26/k5_jsons.out 2>&1; rc=$?
kill $HB
grep -E 'WARNING|Error|Traceback|Writing' skim26/k5_jsons.out | head -40
echo "=== skim26 K5 JSONs done rc=$rc jsons $(find input_sample_jsons_2026 -name '*.json' | wc -l) $(date -Is)"
exit $rc
