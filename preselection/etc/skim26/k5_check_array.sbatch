#!/bin/bash
#SBATCH --job-name=skim26_k5_check
#SBATCH --array=0,2,3,5
#SBATCH --time=04:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#SBATCH --requeue
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/logs/k5check_%A_%a.log
# K5 post-run check, one 2026 preselection task dir per array task (k5_check.py). Read-only.
T=($(ls -d /home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/slurm/jobs/merged_*_r3_2026_*))
D=${T[$SLURM_ARRAY_TASK_ID]}
echo "=== skim26 K5 check | job ${SLURM_ARRAY_JOB_ID}_${SLURM_ARRAY_TASK_ID} | $(basename $D) | $(date -Is)"
( while sleep 10; do echo "[hb] $(date +%T) k5 check $(basename $D | cut -c8-40) running"; done ) & HB=$!
/home/tkolberg.fsu/envs/vbs-coffea/bin/python -u /home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/etc/skim26/k5_check.py $D
RC=$?; kill $HB
echo "=== skim26 K5 check done rc=$RC $(date -Is)"
exit $RC
