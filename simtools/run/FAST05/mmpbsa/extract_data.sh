DIR=output
cd $DIR

cp FINAL_DECOMP_MMPBSA.dat inter

sed -i 1,9d inter

awk '{if (NF>0) {print $2, $5, $7, $11, $15, $19, $23, $27, $7+$11+$15}}' inter > energias_resres.dat

rm intres.dat vdwres.dat electres.dat polres.dat totres.dat resi.dat

for i in {1..80}
do
  j=$(echo "scale=3; 160*$i" | bc )
  head -${j} energias_resres.dat | tail -80 > res${i}.dat
  awk -F' ' '{ total += $4 } END {print total}' res${i}.dat >> vdwres.dat
  awk -F' ' '{ total += $5 } END {print total}' res${i}.dat >> electres.dat
  awk -F' ' '{ total += $6 } END {print total}' res${i}.dat >> polres.dat
  awk -F' ' '{ total += $8 } END {print total}' res${i}.dat >> totres.dat
  echo $i >> resi.dat
  rm res${i}.dat
done

paste resi.dat vdwres.dat electres.dat polres.dat totres.dat > intres.dat
rm resi.dat vdwres.dat electres.dat polres.dat totres.dat

