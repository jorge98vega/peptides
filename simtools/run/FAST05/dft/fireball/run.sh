#!/bin/bash -l
#SBATCH -J fireball
#SBATCH --partition=CLUSTER
#SBATCH --output=slurm-%j.out
#SBATCH --error=slurm-%j.error
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --nodes=1
#SBATCH --get-user-env
#SBATCH --time=72:00:00
#SBATCH --mem=10G
. startjob
/home/jorge/Fireball/progs_updated/progs/fireball.x > out.txt
. endjob
