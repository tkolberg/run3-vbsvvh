#!/bin/bash
#SBATCH --job-name=brilcalc_2223
#SBATCH --time=00:30:00
#SBATCH --cpus-per-task=1
#SBATCH --mem=4G
#SBATCH --output=/blue/avery/tkolberg.fsu/vbs/lumi_2223/brilcalc_2223_%j.log
# Luminosity of the 2022-23 v14_coverage masks; brilcalc over Frontier from HPG (Ted via bridge, 2026-11-20).
M=/blue/avery/tkolberg.fsu/vbs/run3-vbsvvh-2223pf/preselection/corrections/goldenJson/v14_coverage
O=/blue/avery/tkolberg.fsu/vbs/lumi_2223
NT=$HOME/envs/brilws/normtags/normtag_PHYSICS.json
echo "=== BRILCALC 2022-23 MASKS === host=$(hostname) start=$(date -Is) normtag=$(sha256sum $NT | cut -c1-12)"
rc=0
for m in mask_2022Re-recoBCD mask_2022Re-recoE_PromptFG mask_2023PromptC mask_2023PromptD; do
  echo "--- $m $(date +%T)"
  $HOME/envs/brilws/brilcalc.sh lumi -c hpgweb -b "STABLE BEAMS" --normtag $NT -u /fb -i $M/$m.json --output-style csv -o $O/$m.csv.tmp || rc=$?
  mv $O/$m.csv.tmp $O/$m.csv 2>/dev/null
  tail -n 4 $O/$m.csv
done
echo "=== DONE rc=$rc $(date -Is)"
exit $rc
