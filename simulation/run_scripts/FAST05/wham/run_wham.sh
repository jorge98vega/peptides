#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_wham
#SBATCH --partition=CLUSTER
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=999:00:00
#SBATCH --exclude=compute-0-[8,9,10]
# SBATCH --nodelist=compute-0-2
# SBATCH --mem-per-cpu=150
#SBATCH --mem=5G
# ===========================================
#. startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm
module load ips/2019
export MKL_HOME=$MKLROOT


time ./MD_wham.sh $1 $2 $3 $4 $5


# ===========================================
# End Commands
# ===========================================
#. endjob        # Do not remove this line!
#--------------------------------------------

