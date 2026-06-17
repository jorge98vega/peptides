#!/bin/bash -l
#SBATCH --partition=CLUSTER
#SBATCH --ntasks=8
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
#SBATCH --time=200:00:00
#SBATCH --nodelist=compute-0-1
#SBATCH --mem-per-cpu=10G
. startjob
source /opt/intel/oneapi/setvars.sh
source /opt/cp2k/cp2k-2023.1/tools/toolchain/install/setup
export FI_PROVIDER=tcp
srun --mpi=pmi2 /opt/cp2k/cp2k-2023.1/exe/Linux-intel-x86_64/cp2k.popt -i $1 -o cp2k.out
. endjob
