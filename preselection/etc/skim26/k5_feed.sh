#!/bin/bash
# K5: feed the two 1,241-task background preselection arrays into avery-b in slices,
# since avery-b caps a user at 3000 submitted jobs (MaxSubmitPU) shared with other work.
# Each slice is a real .sbatch (array.sbatch with its --array line replaced), submitted
# through qos-route --burst. Logs "[feed] ..." lines; ids to $LOG.ids.
# Usage: k5_feed.sh <array.sbatch> [<array.sbatch> ...]
set -uo pipefail
SLICE=200; MARGIN=50; CAP=3000
LOG=/blue/avery/tkolberg.fsu/vbs/samples/skim/VBSVVH_skim_2026/tasks/logs/k5_feed.log
for A in "$@"; do
  D=$(dirname $A); N=$(grep -o -- '--array=0-[0-9]*' $A | cut -d- -f3)
  for (( lo=0; lo<=N; lo+=SLICE )); do
    hi=$(( lo+SLICE-1 < N ? lo+SLICE-1 : N ))
    S=$D/slice_${lo}_${hi}.sbatch
    sed "s/^#SBATCH --array=0-$N\$/#SBATCH --array=$lo-$hi/" $A > $S
    while :; do
      used=$(squeue -u $USER -q avery-b -h -r 2>/dev/null | wc -l)
      [ $(( CAP - used )) -ge $(( hi-lo+1+MARGIN )) ] && break
      echo "[feed] $(date +%T) waiting: avery-b submitted $used/$CAP, next slice $(basename $D | cut -c8-40) $lo-$hi" >> $LOG
      sleep 300
    done
    id=$(cd $D && qos-route --burst $(basename $S) 2>&1 | tail -1)
    echo "[feed] $(date +%T) $(basename $D | cut -c8-40) $lo-$hi -> $id" >> $LOG
    [[ "$id" =~ ^[0-9]+$ ]] && echo "$(basename $D) $lo-$hi $id" >> $LOG.ids || { echo "[feed] submit failed, retry in 300 s" >> $LOG; sleep 300; lo=$(( lo-SLICE )); }
  done
done
echo "[feed] $(date +%T) all slices submitted" >> $LOG
