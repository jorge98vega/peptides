DIR=.
INPUT=4t10s_run02
#INPUT=$1
JOB=${INPUT}_prod
#FRAME=$2
#STRIP=$3
#STRIP=$(cat strip.dat)

echo 'parm '${DIR}'/'${INPUT}'.top' > ptraj.in
for i in {250..500}
do
echo 'trajin '${DIR}'/'${JOB}'_'${i}'.coord' >> ptraj.in
done
#echo 'trajin '${DIR}'/'${INPUT}'_RMSD.nc '${FRAME}' '${FRAME}' 1' >> ptraj.in
echo "strip ':161-900000'" >> ptraj.in
#echo "strip "${STRIP} >> ptraj.in
echo 'center :1-320' >> ptraj.in
echo 'image' >> ptraj.in
echo 'trajout ./'${JOB}'_extract.nc netcdf' >> ptraj.in

cpptraj < ptraj.in

rm ptraj.in
