#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_mmpbsa
#SBATCH --partition=CLUSTER
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=999:00:00
#SBATCH --nodelist=compute-0-4
# SBATCH --mem-per-cpu=150
#SBATCH --mem=5G
# ===========================================
. startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm


./MMPBSA.sh $1


# ===========================================
# End Commands
# ===========================================
. endjob        # Do not remove this line!
#--------------------------------------------
