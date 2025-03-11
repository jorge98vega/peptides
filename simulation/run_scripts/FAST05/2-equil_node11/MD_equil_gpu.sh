#######################################################################
# Este script realiza una simulación de equilibrio utilizando la GPU 
# en Amber. Se ejecutan múltiples pasos de simulación, cada uno 
# utilizando el archivo de reinicio generado en el paso anterior.
# Se utiliza el módulo CUDA para acelerar la simulación.

set -e  # Salir si ocurre algún error

# En $FAST05:
export CUDA_VISIBLE_DEVICES=$2
module load compilers/cuda/12.2 compilers/gnu/12.1.1 compilers/oneapi/mpi/2021.11
#module load cuda/12.2 gnu/12.1.1 oneapi/mpi/2021.11
source /opt/installed/softwares/amber22/amber.sh
#module load amber/18_cuda_gnu

INPUT=$1   # Nombre del archivo de entrada
JOB=${INPUT}_equil   # Nombre del trabajo basado en el archivo de entrada

#######################################################################
# RUN SIMULATION

# Realiza 100 iteraciones de simulación
for i in {0..99..1}
do
    j=$(( i + 1 ))   # Incrementar el número del paso de simulación

    echo $j   # Imprimir el número de paso actual

    # Crear el archivo de entrada para cada paso de simulación
    cat << EOF > ${JOB}_${j}.in
estab_md_cuda
 &cntrl
 nmropt = 1, ! (Leer fichero de restraints)
 ntx = 5, irest = 1, ntrx = 1, ! (Formato del input)
 ntxo = 2, iwrap = 0, ntpr = 10000, ntwx = 10000, ! (comentado) ntwr = -100000, ! (Formato y frecuencia del output)
 ntr = 0, ! (comentado) restraintmask = '@339', restraint_wt = 20, ! (Restraints sobre átomos)
 ntp = 1, ntf = 2, ntc = 2, ntb = 2, cut = 10, ! (Presión, SHAKE, PBCs)
 imin = 0, ! (Flags de minimización)
 nstlim = 100000, dt = 0.002, ! (Flags de dinámica molecular)
 temp0 = 300, tempi = 300, ig = -1, ntt = 3, gamma_ln = 5, ! (Control de la temperatura)
 &end
 &wt type = 'DUMPFREQ', istep1 = 1000, /
 &wt type = 'END' &end
 DISANG = ${JOB}_rst.dat
 DUMPAVE = ${JOB}_${j}_rst.out
 LISTOUT = ${JOB}_${j}_rst.lis
END
EOF


    # Ejecutar la simulación utilizando la versión optimizada de CUDA de pmemd
    pmemd.cuda_SPFP -O -i ${JOB}_${j}.in \
                   -o ${JOB}_${j}.out \
                   -p ${INPUT}.top \
                   -c ${JOB}_${i}.rst \
                   -ref ${JOB}_0.rst \
                   -x ${JOB}_${j}.coord \
                   -r ${JOB}_${j}.rst

    # Comprimir los archivos de salida para ahorrar espacio
    gzip -f ${JOB}_${i}.rst ${JOB}_${j}.out ${JOB}_${j}.coord

    # Eliminar el archivo de entrada temporal
    \rm ${JOB}_${j}.in
done
