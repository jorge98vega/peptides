#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_min
# SBATCH --partition=CLUSTER
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
# SBATCH --get-user-env
#SBATCH --time=1:00:00
# SBATCH --nodelist=compute-0-2
# SBATCH --mem-per-cpu=150
#SBATCH --mem=3G
# ===========================================
# . startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm


time ./MD_min.sh $1


# ===========================================
# End Commands
# ===========================================
# . endjob        # Do not remove this line!
#--------------------------------------------

