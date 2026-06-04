#!/bin/bash
set -e

usage() {
    echo "Usage: $(basename $0) -m MOL -n NRUNS [-p PREFIX] [-c CENTER_SEL] [-o OUTPUT]"
    echo ""
    echo "  -m MOL         System name              (e.g. 4t10s_run01)"
    echo "  -n NRUNS       Number of runs to merge  (merges PREFIX_0 … PREFIX_{N-1})"
    echo "  -p PREFIX      Run directory prefix     (default: prod)"
    echo "  -c CENTER_SEL  cpptraj center selection (default: :1-320)"
    echo "  -o OUTPUT      Output NetCDF filename   (default: MOL_MD_merged.nc)"
    echo ""
    echo "Run from the directory containing PREFIX_0/, PREFIX_1/, etc."
    exit 1
}

PREFIX=prod
CENTER_SEL=":1-320"
OUTPUT=""

while getopts "m:n:p:c:o:" opt; do
    case $opt in
        m) MOL=$OPTARG ;;
        n) NRUNS=$OPTARG ;;
        p) PREFIX=$OPTARG ;;
        c) CENTER_SEL=$OPTARG ;;
        o) OUTPUT=$OPTARG ;;
        *) usage ;;
    esac
done

if [[ -z "$MOL" || -z "$NRUNS" ]]; then
    echo "Error: -m MOL and -n NRUNS are required."
    usage
fi

[[ -z "$OUTPUT" ]] && OUTPUT="${MOL}_MD_merged.nc"

INPUT=$(mktemp)
for (( i=0; i<NRUNS; i++ )); do
    echo "trajin ${PREFIX}_${i}/${MOL}_MD.nc"
done >> "$INPUT"
echo "center ${CENTER_SEL}" >> "$INPUT"
echo "image"                >> "$INPUT"
echo "trajout ${OUTPUT} netcdf" >> "$INPUT"

cpptraj ${MOL}.top "$INPUT"

rm "$INPUT"
