#!/bin/bash
set -e

usage() {
    echo "Usage: $(basename $0) -m MOL [-w WINDOW] [-f FILE] [-i ITER] [-o OUTPUT]"
    echo ""
    echo "  -m MOL      System name (.top base, e.g. 1t8s_1Cl_WAT)"
    echo "  -w WINDOW   Fixed axis-1 window index for 2D mode (omit for 1D)"
    echo "  -f FILE     Path file with i j columns (e.g. mfep.dat from plot_wham2d.py);"
    echo "              reads col 1 as i and col 2 as j, skips comment lines"
    echo "  -i ITER     Iteration of .nc files to use (default: 1)"
    echo "  -o OUTPUT   Output NetCDF filename"
    echo "              (default: MOL_allwindows.nc  or  MOL_wWINDOW_allwindows.nc)"
    echo ""
    echo "Run from the directory containing MOL.top and windows/."
    exit 1
}

ITER=1
WINDOW=""
FILE=""
OUTPUT=""

while getopts "m:w:f:i:o:" opt; do
    case $opt in
        m) MOL=$OPTARG ;;
        w) WINDOW=$OPTARG ;;
        f) FILE=$OPTARG ;;
        i) ITER=$OPTARG ;;
        o) OUTPUT=$OPTARG ;;
        *) usage ;;
    esac
done

[[ -z "$MOL" ]] && { echo "Error: -m MOL is required."; usage; }

INPUT=$(mktemp)
count=0

if [[ -n "$FILE" ]]; then
    # Path-file mode: read (i, j) from columns 1 and 2, skip comment/blank lines
    [[ -z "$OUTPUT" ]] && OUTPUT="${MOL}_mfep.nc"
    while read -r line; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue
        i=$(echo "$line" | awk '{print $1}')
        j=$(echo "$line" | awk '{print $2}')
        whamdir="windows/wham_${i}_${j}/"
        NC=$(ls "${whamdir}"/*_${ITER}.nc 2>/dev/null | head -n 1)
        if [[ -n "$NC" ]]; then
            echo "trajin $NC" >> "$INPUT"
            (( count++ )) || true
        else
            echo "Warning: no *_${ITER}.nc in $whamdir (i=$i j=$j)" >&2
        fi
    done < "$FILE"
elif [[ -n "$WINDOW" ]]; then
    [[ -z "$OUTPUT" ]] && OUTPUT="${MOL}_w${WINDOW}_allwindows.nc"
    PATTERN="windows/wham_${WINDOW}_*/"
    for whamdir in $(ls -d ${PATTERN} 2>/dev/null | sort -V); do
        NC=$(ls "${whamdir}"/*_${ITER}.nc 2>/dev/null | head -n 1)
        if [[ -n "$NC" ]]; then
            echo "trajin $NC" >> "$INPUT"
            (( count++ )) || true
        else
            echo "Warning: no *_${ITER}.nc in $whamdir" >&2
        fi
    done
else
    [[ -z "$OUTPUT" ]] && OUTPUT="${MOL}_allwindows.nc"
    PATTERN="windows/wham_*/"
    for whamdir in $(ls -d ${PATTERN} 2>/dev/null | sort -V); do
        NC=$(ls "${whamdir}"/*_${ITER}.nc 2>/dev/null | head -n 1)
        if [[ -n "$NC" ]]; then
            echo "trajin $NC" >> "$INPUT"
            (( count++ )) || true
        else
            echo "Warning: no *_${ITER}.nc in $whamdir" >&2
        fi
    done
fi

if [[ $count -eq 0 ]]; then
    echo "Error: no trajectories found matching '${PATTERN}'." >&2
    rm "$INPUT"
    exit 1
fi

echo "trajout ${OUTPUT} netcdf" >> "$INPUT"
cpptraj ${MOL}.top "$INPUT"
rm "$INPUT"

echo "Concatenated $count windows -> $OUTPUT"
