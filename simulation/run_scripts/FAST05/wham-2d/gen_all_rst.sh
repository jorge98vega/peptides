#!/bin/bash
#
# Uso: ./gen_all_rst.sh
# Genera todos los archivos de restraints para el mapa 2D (25x25 ventanas)
# usando el script create_wham2d_rst.py

start_c1=-1.2
step_c1=0.1
nwin=25

for ((iw=1; iw<=nwin; iw++)); do
    # Calcular centro de c1
    c1=$(awk -v start="$start_c1" -v step="$step_c1" -v i="$iw" 'BEGIN {printf "%.3f", start + (i - 1) * step}')

    # Calcular rango de c2
    c2min=$(awk -v c1="$c1" 'BEGIN {printf "%.3f", -2.4}')
    c2max=$(awk -v c1="$c1" 'BEGIN {printf "%.3f", 2.4}')

    echo "➡️  Ventana $iw: c1 = $c1 | c2 ∈ [$c2min, $c2max]"
    python create_wham2d_rst.py --start "$c2min" --stop "$c2max" --step 0.1 \
                                --fixedcenter "$c1" --fixedindex i=$iw
done

