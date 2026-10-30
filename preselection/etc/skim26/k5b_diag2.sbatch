#!/bin/bash
#SBATCH --job-name=skim26_k5b_diag
#SBATCH --time=02:00:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=8gb
#SBATCH --requeue
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/logs/k5b_diag2_%j.log
# K5b: 0lep_1FJ_met data excess diagnostic (k5b_diag2.py), preselection level. Requeue-safe.
O=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/k5b
echo "=== skim26 K5b detector-localisation diagnostic | job $SLURM_JOB_ID | $(date -Is)"
/home/tkolberg.fsu/envs/vbs-coffea/bin/python -u /home/tkolberg.fsu/vbs/wt/skim26-rdf/preselection/etc/skim26/k5b_diag2.py $O
RC=$?
echo "=== skim26 K5b diagnostic done rc=$RC $(date -Is)"
exit $RC
