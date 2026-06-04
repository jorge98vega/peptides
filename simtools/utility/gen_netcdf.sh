#!/bin/bash
set -e

usage() {
    echo "Usage: $(basename $0) -m MOL [-r RUN] [-n NFRAMES] [-c CENTER_SEL]"
    echo ""
    echo "  -m MOL         System name              (e.g. 4t10s_run01)"
    echo "  -r RUN         Run name                 (default: prod)"
    echo "  -n NFRAMES     Number of .coord files   (default: 500)"
    echo "  -c CENTER_SEL  cpptraj center selection (default: :1-320)"
    echo ""
    echo "Run from the directory containing MOL.top and the .coord files."
    exit 1
}

RUN=prod
NFRAMES=500
CENTER_SEL=":1-320"

while getopts "m:r:n:c:" opt; do
    case $opt in
        m) MOL=$OPTARG ;;
        r) RUN=$OPTARG ;;
        n) NFRAMES=$OPTARG ;;
        c) CENTER_SEL=$OPTARG ;;
        *) usage ;;
    esac
done

if [[ -z "$MOL" ]]; then
    echo "Error: -m MOL is required."
    usage
fi

# Decompress .coord.gz files if any exist
if compgen -G "${MOL}_${RUN}_*.coord.gz" > /dev/null; then
    gunzip ${MOL}_${RUN}_*.coord.gz
fi

# Build cpptraj input
INPUT=$(mktemp)
for (( j=1; j<=NFRAMES; j++ )); do
    echo "trajin ${MOL}_${RUN}_${j}.coord"
done >> "$INPUT"
echo "center ${CENTER_SEL}" >> "$INPUT"
echo "image"                >> "$INPUT"
echo "trajout ${MOL}_MD.nc netcdf" >> "$INPUT"

# Run cpptraj
cpptraj ${MOL}.top "$INPUT"

rm "$INPUT"
