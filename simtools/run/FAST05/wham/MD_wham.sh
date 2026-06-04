#!/bin/bash

# Definir los parámetros locales y configurar las opciones necesarias para la simulación
set -e

INPUT=$1  # Nombre del archivo de entrada (por ejemplo, archivo .top de Amber)
WINDOW=$2  # Número de la ventana actual en la simulación WHAM
ITER=$3  # Número de iteración actual
NSTEPS=$4  # Número de pasos de simulación
JOB=${INPUT}_wham${2}_${ITER}  # Nombre del trabajo basado en la entrada y la ventana/iteración
PREV=$((ITER-1))  # Iteración anterior

#######################################################################
# PREPARAR LA SIMULACIÓN AMBER (QM/MM)

# Crear el archivo de entrada de Amber con los parámetros configurados
cat << EOF > amberwham.in
QM/MM
 &cntrl
 ifqnt = 1,  ! Activar la simulación QM
 nmropt = 1,  ! (Leer fichero de restraints)
 ntx = 5, irest = 1, ntrx = 1, ! (Formato del input)
 ntxo = 2, iwrap = 0, ntpr = 100, ntwx = 100, ntwr = 100,  ! (Formato y frecuencia del output)
 ntr = 0,  ! (Restraints sobre átomos)
 ntp = 0, ntf = 2, ntc = 2, ntb = 1, cut = 10,  ! (Presión, SHAKE, PBCs)
 imin = 0,  ! (Flags de minimización)
 nstlim = $NSTEPS, dt = 0.0005,  ! (Pasos de dinámica molecular, con dt en ps -> 0.5 fs)
 temp0 = 300, tempi = 300, ntt = 3, ig=-1, gamma_ln = 5,  ! (Control de la temperatura)
 &end
 &wt type = 'DUMPFREQ', istep1 = 1, /
 &wt type = 'END' &end
 DISANG = wham${WINDOW}_rst.dat
 LISTOUT = wham${WINDOW}_rst_${ITER}.lis
 DUMPAVE = wham${WINDOW}_rst_${ITER}.dump
/
 &qmmm
 qmmask='@547,548,549,550,551,552,553,465,466,467,468,469,470,1314'
 qm_theory='extern'  ! Teoría QM externa
 qm_ewald= 0,  ! No usar Ewald para la QM
 qmshake= 0,  ! No usar SHAKE para la QM
 qmcharge= 0,  ! No realizar cargas QM
 writepdb= 1,  ! Escribir el archivo PDB de salida
/
 &fb
 basis= '/home/jorge/Fireball/Fdatas/Fdata_HCNOSCl/',  ! Basis set para cálculos QM
 idipole = 1,  ! Usar dipolo
 idftd3  = 1  ! Activar corrección de dispersión DFT-D3
/
EOF

# Ejecutar la simulación utilizando Amber y el archivo de entrada generado
$AMBERHOME/bin/sander -O -i amberwham.in \
    -o ${JOB}.out \
    -p ${INPUT}.top \
    -c ${INPUT}_wham${WINDOW}_${PREV}.rst \
    -x ${JOB}.nc \
    -r ${JOB}.rst > ${JOB}.out

# Si es la primera iteración, copiar los archivos de resultados a las siguientes ventanas
if [[ $ITER -eq 1 ]]; then
    if [[ $5 -eq 0 ]]; then
        # Si la condición es 0, se copian los archivos a la ventana anterior y siguiente
        #NEXT_WINDOW=$((WINDOW-1))
        #cp ${JOB}.rst ../wham${NEXT_WINDOW}/${INPUT}_wham${NEXT_WINDOW}_0.rst
        NEXT_WINDOW=$((WINDOW+1))
        cp ${JOB}.rst ../wham${NEXT_WINDOW}/${INPUT}_wham${NEXT_WINDOW}_0.rst
    elif [[ $5 -lt 0 ]]; then
        # Si el paso es negativo, solo copiar a la ventana anterior
        NEXT_WINDOW=$((WINDOW-1))
        cp ${JOB}.rst ../wham${NEXT_WINDOW}/${INPUT}_wham${NEXT_WINDOW}_0.rst
    elif [[ $5 -gt 0 ]]; then
        # Si el paso es positivo, solo copiar a la ventana siguiente
        NEXT_WINDOW=$((WINDOW+1))
        cp ${JOB}.rst ../wham${NEXT_WINDOW}/${INPUT}_wham${NEXT_WINDOW}_0.rst
    fi
fi
