#######################################################################
set -e

module load cesga/2020 gcc/system openmpi/4.0.5_ft3_cuda amber/20.12-AmberTools-21.12


INPUT=$1
JOB=${INPUT}_heat
TEMPI=100
TEMPF=300
STEPS=10
TEMP0=$TEMPI
DT=$(( (TEMPF - TEMPI) / STEPS ))

#######################################################################
# RUN SIMULATION


LASTj=0
for (( j=1; j<=$STEPS; j++ ))
do

echo $j

TEMPI=$TEMP0
TEMP0=$(( TEMPI + DT))

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
 temp0 = ${TEMP0}, tempi = ${TEMPI}, ntt = 3, gamma_ln = 5, vlimit = 20.0, ! (Control de la temperatura)
 &end
 &wt type = 'END' &end
 DISANG = ${JOB}_rst.dat
 LISTOUT = ${JOB}_${j}_rst.lis
EOF

${AMBERHOME}/bin/sander -O -i ${JOB}_${j}.in \
                           -o ${JOB}_${j}.out \
                           -p ${INPUT}.top \
                           -c ${JOB}_${LASTj}.rst \
                           -ref ${INPUT}.rst \
                           -x ${JOB}_${j}.coord \
                           -r ${JOB}_${j}.rst

gzip -f ${JOB}_${LASTj}.rst ${JOB}_${j}.out ${JOB}_${j}.coord
\rm ${JOB}_${j}.in

LASTj=$j

done
