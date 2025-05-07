#!/bin/bash

# Nombre del archivo de entrada y salida
INFILE=9tubes_10stack_oriented
OUTFILE=9t10s_run01

# Número de "tubos" y péptidos por tubo
TUBES=9
PEPTIDES=10

# Secuencia de residuos
SEQ="LYS PHD LYN PHD LYS PHD LYN PHD
LYN PHD LYS PHD LYN PHD LYS PHD"
# Cada cuantos péptidos se repite la secuencia
REP=2
# ¿Son péptidos cíclicos?
CYCLIC=true

# Iones por cada REP péptidos (puede estar vacío)
IONS="TFA TFA TFA TFA"

# Creación del archivo de entrada para tleap
cat << EOF > leap.in
source leaprc.protein.ff19SB
source leaprc.water.tip3p
verbosity 2
loadamberparams frcmod.ionsff99_tip3p
loadamberparams frcmod.tip3p
loadamberprep PHD.prep
loadamberprep TYD.prep
loadamberprep TFA.prepc
loadamberparams TFA.frcmod
x = loadpdbusingseq ${INFILE}.pdb {
EOF

# Generación de la secuencia de residuos para cada tubo
for (( i=1; i<=TUBES; i++ )); do
    for (( j=1; j<=$(( PEPTIDES / REP )); j++ )); do
        echo "$SEQ" >> leap.in
    done
done

# Adición de iones a cada tubo
for (( i=0; i<TUBES; i++ )); do
    for (( j=1; j<=$(( PEPTIDES / REP )); j++ )); do 
        echo "$IONS" >> leap.in
    done
done

# Cierre de la estructura de la molécula en tleap
echo "}" >> leap.in

# Creación de enlaces covalentes entre los anillos
if $CYCLIC; then
    for (( i=0; i<TUBES; i++ )); do
        for (( j=0; j<PEPTIDES; j++ )); do
            echo "bond x.$(( 1 + 8 * j + 8 * PEPTIDES * i )).N x.$(( 8 + 8 * j + 8 * PEPTIDES * i )).C" >> leap.in
        done
    done
fi

# Solvatación y adición de iones
cat << EOF >> leap.in
solvatebox x TIP3PBOX 15.0 2.0
addions x Cl- 180
addions x Na+ 0
charge x
savepdb x ${OUTFILE}.pdb
saveamberparm x ${OUTFILE}.top ${OUTFILE}.rst
EOF

# Código comentado opcional para definir la caja y no centrar la molécula
# cat << EOF >> leap.in
# set x box { 40.0  40.0  40.0 }
# set default nocenter on
# charge x
# savepdb x ${OUTFILE}.pdb
# saveamberparm x ${OUTFILE}.top ${OUTFILE}.rst
# EOF

echo "Archivo leap.in generado correctamente."
