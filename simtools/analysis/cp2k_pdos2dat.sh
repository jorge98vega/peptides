#!/bin/bash
# cp2k_pdos2dat.sh — Convert CP2K .pdos files to smoothed dos_listN.dat files.
#
# Usage: cp2k_pdos2dat.sh <prefix> [--sigma 0.0015] [--iter 1]
#   prefix  : base name of the pdos files (e.g. water_bundle_channel)
#             expects <prefix>-listN-<iter>.pdos for N = 1, 2, ...
#   --sigma : gaussian broadening sigma in Hartree (default: 0.0015)
#   --iter  : iteration index in filename (default: 1)
#
# Output: dos_list1.dat, dos_list2.dat, ...
#         dos_all.dat is a copy of dos_list1.dat (always the total/all-atoms list)

if [ $# -lt 1 ]; then
    echo "Usage: $0 <prefix> [--sigma 0.0015] [--iter 1]"
    exit 1
fi

PREFIX=$1
SIGMA=0.0015
ITER=1
shift

while [[ $# -gt 0 ]]; do
    case $1 in
        --sigma) SIGMA=$2; shift 2 ;;
        --iter)  ITER=$2;  shift 2 ;;
        *) echo "Unknown argument: $1" >&2; exit 1 ;;
    esac
done

SCRIPT_DIR=$(dirname "$(realpath "$0")")

n=1
while true; do
    pdos="${PREFIX}-list${n}-${ITER}.pdos"
    [ -f "$pdos" ] || break
    out="dos_list${n}.dat"
    python3 "${SCRIPT_DIR}/cp2k_pdos.py" "$pdos" --sigma "$SIGMA" --output "$out"
    echo "$pdos → $out"
    n=$((n + 1))
done

if [ -f "dos_list1.dat" ]; then
    cp dos_list1.dat dos_all.dat
    echo "dos_list1.dat → dos_all.dat"
fi
