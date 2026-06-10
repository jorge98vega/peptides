#!/bin/bash
set -e

usage() {
    echo "Usage: $(basename $0) -m MOL [-w WINDOW] [-i ITER] [-o OUTPUT]"
    echo ""
    echo "  -m MOL      System name (.top base, e.g. 1t8s_1Cl_WAT)"
    echo "  -w WINDOW   Fixed axis-1 window index for 2D mode (omit for 1D)"
    echo "  -i ITER     Iteration of .nc files to use (default: 1)"
    echo "  -o OUTPUT   Output NetCDF filename"
    echo "              (default: MOL_allwindows.nc  or  MOL_wWINDOW_allwindows.nc)"
    echo ""
    echo "Run from the directory containing MOL.top and windows/."
    exit 1
}

ITER=1
WINDOW=""
OUTPUT=""

while getopts "m:w:i:o:" opt; do
    case $opt in
        m) MOL=$OPTARG ;;
        w) WINDOW=$OPTARG ;;
        i) ITER=$OPTARG ;;
        o) OUTPUT=$OPTARG ;;
        *) usage ;;
    esac
done

[[ -z "$MOL" ]] && { echo "Error: -m MOL is required."; usage; }

if [[ -n "$WINDOW" ]]; then
    PATTERN="windows/wham_${WINDOW}_*/"
    [[ -z "$OUTPUT" ]] && OUTPUT="${MOL}_w${WINDOW}_allwindows.nc"
else
    PATTERN="windows/wham_*/"
    [[ -z "$OUTPUT" ]] && OUTPUT="${MOL}_allwindows.nc"
fi

INPUT=$(mktemp)
count=0

for whamdir in $(ls -d ${PATTERN} 2>/dev/null | sort -V); do
    NC=$(ls "${whamdir}"/*_${ITER}.nc 2>/dev/null | head -n 1)
    if [[ -n "$NC" ]]; then
        echo "trajin $NC" >> "$INPUT"
        (( count++ )) || true
    else
        echo "Warning: no *_${ITER}.nc in $whamdir" >&2
    fi
done

if [[ $count -eq 0 ]]; then
    echo "Error: no trajectories found matching '${PATTERN}'." >&2
    rm "$INPUT"
    exit 1
fi

echo "trajout ${OUTPUT} netcdf" >> "$INPUT"
cpptraj ${MOL}.top "$INPUT"
rm "$INPUT"

echo "Concatenated $count windows -> $OUTPUT"
