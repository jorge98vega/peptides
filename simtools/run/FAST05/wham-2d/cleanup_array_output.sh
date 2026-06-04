#VALUES=($(seq 0 503))
VALUES=($(seq 504 1007))

for index in $(seq 0 503)
do
  val=${VALUES[$index]}
  i=$(( ( $val / 48 ) + 4 ))
  j=$(( ( $val % 48 ) + 1 ))

  mv slurm-*_${index}.out wham_${i}_${j}
  mv slurm-*_${index}.error wham_${i}_${j}
done
