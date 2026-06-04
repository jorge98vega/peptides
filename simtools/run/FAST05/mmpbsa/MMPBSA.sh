unset AMBERHOME
module load ambertools/22_mpi_intel

#INPUT=4t10s_run01
INPUT=$1
JOB=${INPUT}_prod

cat << EOF > mmpbsa.in
&general
startframe=1, endframe=100, interval=1,
verbose=2, keep_files=2, full_traj=1,
/
&gb
igb=1,
/
&decomp
idecomp=3
csv_format=0
/
EOF


MMPBSA.py -O -i mmpbsa.in -o FINAL_RESULTS_MMPBSA.dat -cp complex.top -rp receptor.top -lp ligand.top -y ${JOB}_extract.nc

rm mmpbsa.in
