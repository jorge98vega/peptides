unset AMBERHOME
module load ambertools/22_mpi_intel

# INPUT=4t10s_run01
INPUT=$1
WATER=$2
JOB=${INPUT}_mdestab

cat << EOF > mmpbsa.in
&general
receptor_mask='!(:${WATER})'
ligand_mask=':${WATER}'
startframe=1, endframe=1, interval=1,
verbose=2, keep_files=1, full_traj=1,
netcdf=1
/
&gb
igb=1,
/
EOF


mpirun -np 4 MMPBSA.py.MPI -O -i mmpbsa.in -o FINAL_RESULTS_MMPBSA.dat -cp complex.top -rp receptor.top -lp ligand.top -y ${JOB}_extract.nc

rm mmpbsa.in
