#!/bin/bash
# Usage: wham2d.sh <input> <Nsteps1> <start1> <step1> <2rk1> <col1> <Nsteps2> <start2> <step2> <2rk2> <col2> <last>
#   input   : dump file base name (files expected as <input>_<i>_<j>_rst_1.dump)
#   Nsteps1 : number of windows in dim 1 (loop runs 1..Nsteps1)
#   start1  : center of the first window in dim 1
#   step1   : step per window in dim 1 (use negative value for decreasing centers)
#   2rk1    : force constant x2 for dim 1 written to meta.dat (= 2 * rk from rst.dat)
#   col1    : column index of the dim 1 rst coordinate in the dump file (= 2 is the 1st coordinate)
#   Nsteps2 : number of windows in dim 2 (loop runs 1..Nsteps2)
#   start2  : center of the first window in dim 2
#   step2   : step per window in dim 2 (use negative value for decreasing centers)
#   2rk2    : force constant x2 for dim 2 written to meta.dat
#   col2    : column index of the dim 2 rst coordinate in the dump file
#   last    : number of trailing rows to keep from each dump

if [ "$#" -ne 12 ]; then
    echo "Usage: $0 <input> <Nsteps1> <start1> <step1> <2rk1> <col1> <Nsteps2> <start2> <step2> <2rk2> <col2> <last>"
    exit 1
fi

INPUT=$1
NSTEPS1=$2
START1=$3
STEP1=$4
TWO_RK1=$5
COL1=$6
NSTEPS2=$7
START2=$8
STEP2=$9
TWO_RK2=${10}
COL2=${11}
LAST=${12}

LAST_CENTER1=$(echo "scale=3; $START1 + ($NSTEPS1-1)*$STEP1" | bc)
LAST_CENTER2=$(echo "scale=3; $START2 + ($NSTEPS2-1)*$STEP2" | bc)

if (( $(echo "$START1 < $LAST_CENTER1" | bc -l) )); then
    HIST_MIN1=$START1; HIST_MAX1=$LAST_CENTER1
else
    HIST_MIN1=$LAST_CENTER1; HIST_MAX1=$START1
fi

if (( $(echo "$START2 < $LAST_CENTER2" | bc -l) )); then
    HIST_MIN2=$START2; HIST_MAX2=$LAST_CENTER2
else
    HIST_MIN2=$LAST_CENTER2; HIST_MAX2=$START2
fi

rm -rf meta.dat
touch meta.dat

for i in $(seq 1 $NSTEPS1); do
    b1=$(echo "scale=3; $START1 + ($i-1)*$STEP1" | bc)
    for j in $(seq 1 $NSTEPS2); do
        b2=$(echo "scale=3; $START2 + ($j-1)*$STEP2" | bc)
        awk -v c1=$COL1 -v c2=$COL2 '{print $1,$c1,$c2}' ${INPUT}_${i}_${j}_rst_1.dump | tail -${LAST} > w1_${i}_${j}.out
        echo w1_${i}_${j}.out ${b1} ${b2} ${TWO_RK1} ${TWO_RK2} >> meta.dat
    done
done

# hist1_min hist1_max nbins1 hist2_min hist2_max nbins2 tolerance temperature periodic metafile outfile
/home/jorge/bin/wham/wham-2d/wham-2d Px=0 ${HIST_MIN1} ${HIST_MAX1} 50 Py=0 ${HIST_MIN2} ${HIST_MAX2} 75 0.0001 300 0 meta.dat wham2d.out 0
