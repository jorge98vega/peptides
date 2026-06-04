#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
#SBATCH -J check_GPUs
#SBATCH --partition=GPUNODE
#SBATCH --output=_check_GPUs.out
#SBATCH --error=_check_GPUs.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=00:01:00
#SBATCH --nodelist=compute-0-11
# SBATCH --mem-per-cpu=150
#SBATCH --mem=1G
# ===========================================
# . startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm


nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv > GPUs.csv


# ===========================================
# End Commands
# ===========================================
# . endjob        # Do not remove this line!
#--------------------------------------------

