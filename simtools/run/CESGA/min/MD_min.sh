#######################################################################
set -e

module load cesga/2020 gcc/system openmpi/4.0.5_ft3_cuda amber/20.12-AmberTools-21.12

INPUT=$1
JOB=${INPUT}_min

#######################################################################
# RUN SIMULATION


cat << EOF > ${JOB}.in
min_md
 &cntrl
 nmropt = 1, ! (Leer fichero de restraints)
 ntx = 1, irest = 0, ntrx = 1, ! (Formato del input)
 ntxo = 1, iwrap = 0, ntpr = 100, ntwx = 100, ! (Formato y frecuencia del output)
 ntr = 0, ! (Restraints sobre átomos)
 ntp = 1, ntf = 1, ntc = 1, ntb = 2, cut = 8, nsnb = 10, ! (Presión, SHAKE, PBCs)
 imin = 1, maxcyc = 20000, ! (Flags de minimización)
 ! (comentado) nstlim = 1000, dt = 0.001, ! (Flags de dinámica molecular)
 temp0 = 300, tempi = 300, ntt = 1, ! (Control de la temperatura)
 &end
 &wt type = 'END' &end
 DISANG = ${JOB}_rst.dat
 LISTOUT = ${JOB}_rst.lis
EOF

${AMBERHOME}/bin/sander -O -i ${JOB}.in \
                           -o ${JOB}.out \
                           -p ${INPUT}.top \
                           -c ${INPUT}.rst \
                           -ref ${INPUT}.rst \
                           -x ${JOB}.coord \
                           -r ${JOB}.rst

\rm ${JOB}.in
