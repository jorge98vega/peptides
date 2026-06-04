#!/bin/bash -l
# ===========================================
# Slurm Header
# ===========================================
# SBATCH -J job_equil
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


module load ips/2019
export MKL_HOME=$MKLROOT

time ${AMBERHOME}/bin/sander -O -i amber_qmmm.in \
    -o 4t10s_run02_qmmm_1.out \
    -p 4t10s_run02.top \
    -c 4t10s_run02_qmmm_0.rst \
    -ref 4t10s_run02.rst \
    -x 4t10s_run02_qmmm_1.nc \
    -r 4t10s_run02_qmmm_1.rst > salida.out


# ===========================================
# End Commands
# ===========================================
. endjob        # Do not remove this line!
#--------------------------------------------

