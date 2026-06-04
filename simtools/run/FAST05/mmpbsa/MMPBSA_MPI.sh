unset AMBERHOME
module load ambertools/22_mpi_intel

#INPUT=4t10s_run01
INPUT=$1
JOB=${INPUT}_mdestab

cat << EOF > mmpbsa.in
&general
receptor_mask=':1-80'
ligand_mask=':81-160'
startframe=1, endframe=1000, interval=1,
verbose=2, keep_files=1, full_traj=1,
/
&gb
igb=2, saltcon=0.10,
/
&decomp
idecomp=3
csv_format=0
/
EOF
# &pb
# istrng=0.10,
# /
# EOF


mpirun -np 4 MMPBSA.py.MPI -O -i mmpbsa.in -o FINAL_RESULTS_MMPBSA.dat -cp complex.top -rp receptor.top -lp ligand.top -y ${JOB}_extract.nc

rm mmpbsa.in
