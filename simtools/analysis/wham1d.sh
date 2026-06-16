#!/bin/bash
# Usage: wham1d.sh <input> <Nsteps> <start> <step> <last> <2rk> <col>
#   input  : dump file base name (files expected as <input>_<i>_rst_1.dump)
#   Nsteps : number of windows (loop runs 1..Nsteps)
#   start  : center of the first window
#   step   : decrement per window (use negative value for increasing centers)
#   last   : number of trailing rows to keep from each dump
#   2rk    : force constant x2 written to meta.dat (= 2 * rk from rst.dat)
#   col    : column index of the rst coordinate in the dump file (= 2 is the 1st coordinate)

if [ "$#" -ne 7 ]; then
    echo "Usage: $0 <input> <Nsteps> <start> <step> <last> <2rk> <col>"
    exit 1
fi

INPUT=$1
NSTEPS=$2
START=$3
STEP=$4
LAST=$5
TWO_RK=$6
COL=$7

LAST_CENTER=$(echo "scale=3; $START + ($NSTEPS-1)*$STEP" | bc)

if (( $(echo "$START < $LAST_CENTER" | bc -l) )); then
    HIST_MIN=$START
    HIST_MAX=$LAST_CENTER
else
    HIST_MIN=$LAST_CENTER
    HIST_MAX=$START
fi

rm -rf meta.dat
touch meta.dat

for i in $(seq 1 $NSTEPS); do
    b=$(echo "scale=3; $START + ($i-1)*$STEP" | bc)
    awk -v col=$COL '{print $1,$col}' ${INPUT}_${i}_rst_1.dump | tail -${LAST} > mc_${i}.out
    echo mc_${i}.out ${b} ${TWO_RK} >> meta.dat
done

# hist_min hist_max num_bins tolerance temperature periodic metafile outfile
/home/jorge/bin/wham/wham/wham ${HIST_MIN} ${HIST_MAX} 50 0.0001 300 0 meta.dat wham.out

cd ..
