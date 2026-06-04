#!/bin/bash
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_prod
# SBATCH --partition=GPUNODE
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
#SBATCH --gres=gpu
# SBATCH --ntasks=1
# SBATCH --cpus-per-task=1
# SBATCH --nodes=1
# SBATCH --get-user-env
#SBATCH --time=24:00:00
# SBATCH --nodelist=compute-0-10
#SBATCH -c 32 --mem-per-cpu=3G
# SBATCH --mem=10G
# ===========================================
# . startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm


time ./MD_prod_gpu.sh $1 $2


# ===========================================
# End Commands
# ===========================================
# . endjob        # Do not remove this line!
#--------------------------------------------

