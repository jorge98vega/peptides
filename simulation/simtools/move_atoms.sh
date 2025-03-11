# Script para actualizar las coordenadas de átomos en un archivo .rst o .pdb
# utilizando las nuevas coordenadas de un archivo .xyz. 

INFILE="model_building/4t10s_runNoCl_prod_0_premove.rst"   # Archivo de entrada (RST o PDB)
INDICES=(6812)  # Índices de átomos a actualizar (en formato 0-indexado para RST, 1-indexado para PDB)
XYZ="newcoords.xyz"  # Archivo con las nuevas coordenadas atómicas
OUTFILE="model_building/4t10s_runNoCl_prod_0.rst"  # Archivo de salida con coordenadas actualizadas
FORMAT="rst"  # Formato de archivo de entrada ("rst" o "pdb")

# Itera sobre los índices de átomos especificados
for INDEX in ${INDICES[@]}
do
    if [ $FORMAT = "rst" ]; then
        # Para formato RST, determina la línea y columna correspondiente
        LINE=$((INDEX/2+3))           # Línea de la coordenada en el archivo RST
        COLUMN=$((INDEX%2*3+1))       # Columna X de las coordenadas (dependiendo del índice)

        # Lee las nuevas coordenadas desde el archivo XYZ
        X=$(awk '{print $1}' $XYZ)    # Coordenada X
        Y=$(awk '{print $2}' $XYZ)    # Coordenada Y
        Z=$(awk '{print $3}' $XYZ)    # Coordenada Z

        # Actualiza las coordenadas del átomo en el archivo RST
        awk -v line=$LINE -v column=$COLUMN -v x=$X -v y=$Y -v z=$Z 'BEGIN {OFS="  "} NR==line {$column=x; $(column+1)=y; $(column+2)=z; $1="  "$1} 1' $INFILE > $OUTFILE
    fi

    if [ $FORMAT = "pdb" ]; then
        # Para formato PDB, determina la línea y la columna para las coordenadas
        LINE=$((INDEX+1))    # Línea de la coordenada en el archivo PDB (1-indexado)
        COLUMN=7             # Columna de la coordenada X (especificada, verificar en cada caso)

        # Lee las nuevas coordenadas desde el archivo XYZ
        X=$(awk '{print $1}' $XYZ)    # Coordenada X
        Y=$(awk '{print $2}' $XYZ)    # Coordenada Y
        Z=$(awk '{print $3}' $XYZ)    # Coordenada Z

        # Actualiza las coordenadas del átomo en el archivo PDB
        awk -v line=$LINE -v column=$COLUMN -v x=$X -v y=$Y -v z=$Z 'NR==line {$column=x; $(column+1)=y; $(column+2)=z} 1' $INFILE > $OUTFILE
    fi
done
