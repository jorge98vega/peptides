#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_prod
#SBATCH --partition=GPUNODE
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
# SBATCH --gres=gpu:1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=999:00:00
#SBATCH --nodelist=compute-0-11
# SBATCH --mem-per-cpu=150
#SBATCH --mem=5G
# ===========================================
#. startjob      # Do not remove this line!
# ===========================================
# Your Commands Go Here 
# ===========================================

# export OMP_NUM_THREADS=$NSLOTS        # SGE
# export OMP_NUM_THREADS=$SLURM_NPROCS  # Slurm


# Check for free GPUs
GPU=$(nvidia-smi --query-gpu=index,utilization.gpu,memory.used --format=csv | grep "0 %" | head -n 1 | awk -F "," '{print $1}')

if [ $GPU ]
then
  echo "GPU index = $GPU"
  time ./MD_prod_gpu.sh $1 $GPU
else
  echo "ERROR: No GPUs available"
  exit
fi


# ===========================================
# End Commands
# ===========================================
#. endjob        # Do not remove this line!
#--------------------------------------------

