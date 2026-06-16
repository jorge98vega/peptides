#!/bin/bash
# Lanza trabajos WHAM 2D encadenados por SLURM propagando en la dirección indicada.
# Uso: ./run_all_wham2d.sh INPUT FIXEDWINDOW WINDOW LIMIT DIRECTION [OLD_JOB_ID]
#   INPUT        : nombre base del sistema (e.g. 1t8s_1Cl_WAT)
#   FIXEDWINDOW  : índice de la coordenada fija
#   WINDOW       : ventana inicial
#   LIMIT        : última ventana del eje libre
#   DIRECTION    : both | next | prev | none
#   OLD_JOB_ID   : (opcional) ID SLURM del que depende este trabajo
#
# Ejemplo — windows 10_1 a 10_49, empezando en 10_25 hacia ambos lados:
#   ./run_all_wham2d.sh 1t8s_1Cl_WAT 10 25 49 both

INPUT=$1
FIXEDWINDOW=$2
WINDOW=$3
LIMIT=$4
DIRECTION=$5
OLD_JOB_ID=$6
wd=$(pwd)

cp ${wd}/${INPUT}.top ${wd}/MD_wham2d.sh ${wd}/run_wham2d.sh ${wd}/windows/wham_${FIXEDWINDOW}_${WINDOW}/
cd ${wd}/windows/wham_${FIXEDWINDOW}_${WINDOW}/
echo "Window ${FIXEDWINDOW}_${WINDOW} - Direction: ${DIRECTION}"

if [[ -z $OLD_JOB_ID ]]; then
    JOB_ID=$(sbatch -J "wham_${FIXEDWINDOW}_${WINDOW}" run_wham2d.sh $INPUT $FIXEDWINDOW $WINDOW 1 8000 $DIRECTION | awk '{print $4}')
else
    JOB_ID=$(sbatch -J "wham_${FIXEDWINDOW}_${WINDOW}" -d afterok:${OLD_JOB_ID} run_wham2d.sh $INPUT $FIXEDWINDOW $WINDOW 1 8000 $DIRECTION | awk '{print $4}')
fi
echo "Job $JOB_ID"

cd $wd

if [[ $DIRECTION == "both" ]] || [[ $DIRECTION == "prev" ]]; then
    if [[ $WINDOW -gt 1 ]]; then
        ./run_all_wham2d.sh $INPUT $FIXEDWINDOW $((WINDOW-1)) $LIMIT prev $JOB_ID
    fi
fi
if [[ $DIRECTION == "both" ]] || [[ $DIRECTION == "next" ]]; then
    if [[ $WINDOW -lt $LIMIT ]]; then
        ./run_all_wham2d.sh $INPUT $FIXEDWINDOW $((WINDOW+1)) $LIMIT next $JOB_ID
    fi
fi
# direction=none: no recursion
