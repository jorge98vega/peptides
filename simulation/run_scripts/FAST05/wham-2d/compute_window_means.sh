#!/bin/bash
#
# Uso: ./compute_all_window_means.sh
# Calcula medias y desviaciones de columnas 2 y 7 de todos los .dump del directorio

if [ $# -lt 1 ]; then
    echo "Uso: $0 N"
    echo "Ejemplo: $0 5000   # usa las últimas 5000 líneas de cada .dump"
    exit 1
fi

N=$1
outfile="window_means_${N}.dat"
echo "#window mean_c1 std_c1 mean_c2 std_c2" > "$outfile"

for window in {1..25}; do
    file="wham_${window}_0/wham_${window}_0_rst_1.dump"
    [ -f "$file" ] || continue

    # Extraer número de ventana (primera coincidencia numérica en el nombre)
    #window=$(echo "$file" | grep -oE '[0-9]+' | head -1)

    tail -n "$N" "$file" | awk -v w="$window" '
    BEGIN {sum1=0; sum2=0; sumsq1=0; sumsq2=0; n=0}
    !/^#/ {
        x=$2; y=$7
        sum1+=x; sum2+=y
        sumsq1+=x*x; sumsq2+=y*y
        n++
    }
    END {
        if (n>0) {
            mean1=sum1/n
            mean2=sum2/n
            std1=sqrt(sumsq1/n - mean1*mean1)
            std2=sqrt(sumsq2/n - mean2*mean2)
            printf "%d %.6f %.6f %.6f %.6f\n", w, mean1, std1, mean2, std2
        }
    }' >> "$outfile"

    echo "✅ Procesado $file → ventana $window"
done

echo "📄 Archivo final generado: $outfile"

