#######################################################################
# Este script realiza una simulación de calentamiento (heating) en Amber.  
# Toma un archivo de entrada proporcionado como argumento y genera una 
# serie de simulaciones para calentar el sistema desde una temperatura 
# inicial a una temperatura final en un número determinado de pasos.

set -e  # Salir si ocurre algún error

module load ips/2019

INPUT=$1   # Archivo de entrada proporcionado como argumento
JOB=${INPUT}_heat   # Nombre del trabajo basado en el archivo de entrada
TEMPI=100   # Temperatura inicial en Kelvin
TEMPF=300   # Temperatura final en Kelvin
STEPS=10    # Número de pasos para el calentamiento
TEMP0=$TEMPI   # Inicializar la temperatura final del primer paso
DT=$(( (TEMPF - TEMPI) / STEPS ))   # Incremento de temperatura por paso

#######################################################################
# RUN SIMULATION

LASTj=0   # Contador para almacenar el número del último paso
for (( j=1; j<=$STEPS; j++ ))
do
    echo $j  # Imprimir el número de paso actual

    TEMPI=$TEMP0   # Asignar la temperatura inicial al primer paso
    TEMP0=$(( TEMPI + DT ))   # Calcular la temperatura para el siguiente paso

    # Crear el archivo de entrada para la simulación de calentamiento
    cat << EOF > ${JOB}_${j}.in
equil_md
 &cntrl
 nmropt = 1, ! (Leer fichero de restraints)
 ntx = 1, irest = 0, ntrx = 1, ! (Formato del input)
 ntxo = 1, iwrap = 0, ntpr = 100, ntwx = 100, ! (Formato y frecuencia del output)
 ntr = 0, ! (Restraints sobre átomos)
 ntp = 1, ntf = 2, ntc = 2, ntb = 2, cut = 12, dielc = 1.0, nsnb = 10, ! (Presión, SHAKE, PBCs)
 imin = 0, ! (Flags de minimización)
 nstlim = 1000, dt = 0.002, ! (Flags de dinámica molecular)
 temp0 = ${TEMP0}, tempi = ${TEMPI}, ig = -1, ntt = 3, gamma_ln = 5, vlimit = 20.0, ! (Control de la temperatura)
 &end
 &wt type = 'END' &end
 DISANG = ${JOB}_rst.dat
 LISTOUT = ${JOB}_${j}_rst.lis
EOF

    # Ejecutar la simulación con el programa sander de Amber
    ${AMBERHOME}/bin/sander -O -i ${JOB}_${j}.in \
                           -o ${JOB}_${j}.out \
                           -p ${INPUT}.top \
                           -c ${JOB}_${LASTj}.rst \
                           -ref ${INPUT}.rst \
                           -x ${JOB}_${j}.coord \
                           -r ${JOB}_${j}.rst

    # Comprimir los archivos de salida
    gzip -f ${JOB}_${LASTj}.rst ${JOB}_${j}.out ${JOB}_${j}.coord

    # Eliminar el archivo de entrada temporal
    \rm ${JOB}_${j}.in

    LASTj=$j   # Actualizar el último paso para el próximo ciclo
done
