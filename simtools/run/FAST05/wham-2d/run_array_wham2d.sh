#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_wham
#SBATCH --partition=CLUSTER
#SBATCH --output=slurm-%A_%a.out
#SBATCH --error=slurm-%A_%a.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=999:00:00
# SBATCH --exclude=compute-0-[8,9,10]
#SBATCH --nodelist=compute-0-11
# SBATCH --mem-per-cpu=150
#SBATCH --mem=5G
#SBATCH --array=0-503%48
# ===========================================
#. startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================


# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm
module load ips/2019
export MKL_HOME=$MKLROOT

#VALUES=($(seq 0 503))
VALUES=($(seq 504 1007))

index=${VALUES[$SLURM_ARRAY_TASK_ID]}
i=$(( ( $index / 48 ) + 4 ))
j=$(( ( $index % 48 ) + 1 ))

cd wham_${i}_${j}
time ./MD_wham2d.sh $1 $i $j 1 8000 0


# ===========================================
# End Commands
# ===========================================
#. endjob        # Do not remove this line!
#--------------------------------------------

