#!/bin/bash

# Descripción:
# Este script configura simulaciones WHAM (Weighted Histogram Analysis Method) creando directorios,
# copiando los scripts necesarios y generando archivos de restricciones específicos para cada ventana de simulación.

# Iteración sobre las ventanas de simulación (1 a 49)
for i in {1..81} # ventana
do
    # Calcular el centro del potencial (valor b) para la ventana i.
    # El centro varía desde -2.0 hasta +2.0 en función de la ventana.
    b=$(echo "scale=3; -2.050+($i*0.050)" | bc)

    # Crear el directorio para la ventana actual (wham${i})
    mkdir -p wham${i}

    # Copiar los scripts necesarios a cada directorio de ventana
    cp run_wham.sh wham${i}
    cp MD_wham.sh wham${i}

    # Crear el archivo de restricciones para la ventana actual
    # El archivo contiene restricciones de distancias y ángulos entre átomos específicos
    cat << EOF > wham${i}/wham${i}_rst.dat
!!! RESTRAINED COORDINATES !!!
! 1 - REACTION COORDINATE - d(HZ11-NZ1) - d(HZ11-NZ2)
&rst iat = 551, 550, 551, 797,
      rstwt = 1, -1,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 400, rk3 = 400,
      &end

!!! FREE COORDINATES !!!
! 2 - DISTANCE - d(HZ11-NZ1)
&rst iat = 551, 550,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 3 - DISTANCE - d(HZ11-NZ2)
&rst iat = 551, 797,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 4 - DISTANCE - d(NZ1-NZ2)
&rst iat = 550, 797,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 5 - ANGLE - a(NZ1-HZ11-NZ2)
&rst iat = 550, 551, 797,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 6 - DISTANCE - d(NZ1-Cl1)
&rst iat = 550, 1314,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 7 - DISTANCE - d(NZ2-Cl1)
&rst iat = 797, 1314,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 8 - DISTANCE - d(HZ11-Cl1)
&rst iat = 551, 1314,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

EOF

    # Fin de la creación de restricciones para la ventana actual.
done

# Fin del script.
