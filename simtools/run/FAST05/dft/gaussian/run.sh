#!/bin/bash -l
#SBATCH --partition=CLUSTER
#SBATCH --nodelist=compute-0-1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=4
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=500:00:00
#SBATCH --mem=40G
. startjob
module purge
export GAUSS_SCRDIR="/home/jorge/SCRATCH_GAUSSIAN"
export g09root="/export/apps/installed"
EXE="/export/apps/installed/g09/g09"
. $g09root/g09/bsd/g09.profile
source /opt/intel/oneapi/setvars.sh intel64
export OMP_STACKSIZE=2G
$EXE < gaussian_input.gjf > output.log
/export/apps/installed/g09/formchk system.chk system.fchk
. endjob
