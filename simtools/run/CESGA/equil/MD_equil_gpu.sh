#######################################################################
# DEFINE LOCALS
set -e

# EN $CESGA:
module load cesga/2020 gcc/system openmpi/4.0.5_ft3_cuda amber/20.12-AmberTools-21.12

INPUT=$1
JOB=${INPUT}_equil

#######################################################################
# RUN SIMULATION

for i in {0..99..1}
#i=0
do
j=$(( i + 1 ))

echo $j

cat << EOF > ${JOB}_${j}.in
estab_md_cuda
 &cntrl
 nmropt = 1, ! (Leer fichero de restraints)
 ntx = 5, irest = 1, ntrx = 1, ! (Formato del input)
 ntxo = 1, iwrap = 0, ntpr = 10000, ntwx = 10000, ! (comentado) ntwr = -100000, ! (Formato y frecuencia del output)
 ntr = 0, ! (comentado) restraintmask = '@339', restraint_wt = 20, ! (Restraints sobre átomos)
 ntp = 1, ntf = 2, ntc = 2, ntb = 2, cut = 10, ! (Presión, SHAKE, PBCs)
 imin = 0, ! (Flags de minimización)
 nstlim = 100000, dt = 0.002, ! (Flags de dinámica molecular)
 temp0 = 300, tempi = 300, ntt = 3, gamma_ln = 5, ! (Control de la temperatura)
 &end
 &wt type = 'DUMPFREQ', istep1 = 1000, /
 &wt type = 'END' &end
 DISANG = ${JOB}_rst.dat
 DUMPAVE = ${JOB}_${j}_rst.out
 LISTOUT = ${JOB}_${j}_rst.lis
END
EOF

pmemd.cuda_SPFP -O -i ${JOB}_${j}.in \
                   -o ${JOB}_${j}.out \
                   -p ${INPUT}.top \
                   -c ${JOB}_${i}.rst \
                   -ref ${JOB}_0.rst \
                   -x ${JOB}_${j}.coord \
                   -r ${JOB}_${j}.rst

gzip -f ${JOB}_${i}.rst ${JOB}_${j}.out ${JOB}_${j}.coord
\rm ${JOB}_${j}.in

done

