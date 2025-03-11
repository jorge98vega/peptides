# Script para fusionar múltiples archivos de trayectoria en un único archivo NetCDF usando cpptraj.

MOL=4t10s_run01

# Añade las trayectorias de los archivos de producción a la entrada de cpptraj
echo "trajin prod_0/${MOL}_MD.nc" >> input   # Trayectoria del primer archivo
echo "trajin prod_1/${MOL}_MD.nc" >> input   # Trayectoria del segundo archivo

# Centra la molécula y ajusta la imagen
echo "center :1-320" >> input   # Centra los átomos de la proteína (residuo 1 a 320)
echo "image" >> input           # Realiza la imagen de las moléculas

# Define el archivo de salida como formato netcdf
echo "trajout ${MOL}_MD_merged.nc netcdf" >> input   # Salida en formato netcdf

# Ejecuta cpptraj con el archivo de entrada
cpptraj ${MOL}.top input 

# Elimina el archivo de entrada temporal
rm input
