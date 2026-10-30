#!/bin/bash
#SBATCH --job-name=skim26_k5_check
#SBATCH --time=03:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#SBATCH --requeue
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/logs/k5check_%j.log
# K5 post-run check over the six 2026 preselection task dirs (k5_check.py). Read-only.
echo "=== skim26 K5 check | job $SLURM_JOB_ID | $(date -Is)"
( while sleep 10; do echo "[hb] $(date +%T) k5 check running"; done ) & HB=$!
/home/tkolberg.fsu/envs/vbs-coffea/bin/python /home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/etc/skim26/k5_check.py \
    $(ls -d /home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/slurm/jobs/merged_*_r3_2026_*)
RC=$?; kill $HB
echo "=== skim26 K5 check done rc=$RC $(date -Is)"
exit $RC
