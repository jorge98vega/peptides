DIR=.
INPUT=$1
#INPUT=4t10s_run03
#STRIP=$(cat strip.dat)
#NWATS=$2
#NRES=$((321 + NWATS))

rm ${DIR}/complex.top ${DIR}/receptor.top ${DIR}/ligand.top

ante-MMPBSA.py -p ${DIR}/${INPUT}.top -c ${DIR}/complex.top -r ${DIR}/receptor.top -l ${DIR}/ligand.top -s ':161-900000' -m ':1-80'
#ante-MMPBSA.py -p ${DIR}/${INPUT}.top -c ${DIR}/complex.top -r ${DIR}/receptor.top -l ${DIR}/ligand.top -s :${NRES}-99999 -n :321
# -m es el receptor
# -n es el ligando
