#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_mmpbsa
#SBATCH --partition=CLUSTER
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=4
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=999:00:00
#SBATCH --nodelist=compute-0-7
# SBATCH --mem-per-cpu=150
#SBATCH --mem=5G
# ===========================================
. startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm


declare -a ENES=("VDWAALS" "EEL" "EGB" "ESURF" "DELTA G gas" "DELTA G solv" "DELTA TOTAL")
rm -f mmpbsa.out ptraj.out ante.out
touch mmpbsa.out ptraj.out ante.out
rm -f all_energies.dat
touch all_energies.dat
echo "FRAME WATER VDWAALS EEL EGB ESURF DELTA_G_gas DELTA_G_solv DELTA_TOTAL" >> all_energies.dat

# ./get_water_indices.py ${1}.top ../../estab_2/${1}_MD.nc ${1}_RMSD.nc 4990 5000
FIRST=4990 # First frame - (empezando en 0, +1 empezando en 1)
for step in {1..10}
do
FRAME=$((FIRST + step))
NSTRIPWATS=$(awk -v line=$step 'NR==line{print NF}' iWATs_res.dat)
STRIP=$(sed "${step}s@ @,@g;${step}q;d" iWATs_res.dat)
STRIP="!(:1-320,"$STRIP")" # 320 del bundle + 0 Cls
declare -a WATS=($(sed "${step}q;d" iWATs_canal_indexres.dat))
./ptraj_extract.sh $1 $FRAME $STRIP >> ptraj.out # frame empezando en 1
./ante-mmpbsa.sh $1 $NSTRIPWATS >> ante.out

i=0
for water in "${WATS[@]}"
do
i=$(( i + 1 ))
echo Frame $FRAME - water $i / "${#WATS[@]}"
echo Frame $FRAME - water $i / "${#WATS[@]}" >> mmpbsa.out
./MMPBSA_MPI_loop.sh $1 $water >> mmpbsa.out
echo $FRAME $water >> all_energies.dat

for ene in "${ENES[@]}"
do
value=$(tail -21 FINAL_RESULTS_MMPBSA.dat | sed -n 's@^'"$ene"'[ a-zA-Z]*\(\-*[0-9]\+\.[0-9]\+\).*@\1@p')
sed -i '$s/$/ '"$value"'/' all_energies.dat
done

rm _MMPBSA_* reference.frc
rm FINAL_RESULTS_MMPBSA.dat
done

done


# ===========================================
# End Commands
# ===========================================
. endjob        # Do not remove this line!
#--------------------------------------------
