#!/bin/bash

# Descripción:
# Este script configura simulaciones WHAM (Weighted Histogram Analysis Method) creando directorios,
# copiando los scripts necesarios y generando archivos de restricciones específicos para cada ventana de simulación.

# Iteración sobre las ventanas de simulación (1 a 49)
for i in {1..49} # ventana
do
    # Calcular el centro del potencial (valor b) para la ventana i.
    # El centro varía desde -1.550 hasta 2.450 en función de la ventana.
    b=$(echo "scale=3; -1.550+($i*0.050)" | bc)

    # Crear el directorio para la ventana actual (wham${i})
    mkdir -p wham${i}

    # Copiar los scripts necesarios a cada directorio de ventana
    cp run_wham.sh wham${i}
    cp MD_wham.sh wham${i}

    # Crear el archivo de restricciones para la ventana actual
    # El archivo contiene restricciones de distancias y ángulos entre átomos específicos
    cat << EOF > wham${i}/wham${i}_rst.dat
!!! RESTRAINED COORDINATES !!!
! 1 - REACTION COORDINATE - d(NZ1-HZ) - d(HZ-O)
&rst iat = 3503, 3506, 3506, 5944,
      rstwt = 1, -1,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 400, rk3 = 400,
      &end

!!! FREE COORDINATES !!!
! 2 - DISTANCE - d(NZ1-HZ)
&rst iat = 3503, 3506,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 3 - DISTANCE - d(HZ-O)
&rst iat = 3506, 5944,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 4 - DISTANCE - d(NZ1-O)
&rst iat = 3503, 5944,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 5 - ANGLE - a(NZ1-HZ-O)
&rst iat = 3503, 3506, 5944,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 6 - REACTION COORDINATE - d(O-H) - d(H-NZ2)
&rst iat = 5944, 5945, 5945, 2300
      rstwt = 1, -1,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 7 - DISTANCE - d(O-H)
&rst iat = 5944, 5945,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 8 - DISTANCE - d(H-NZ2)
&rst iat = 5945, 2300,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 9 - DISTANCE - d(O-NZ2)
&rst iat = 5944, 2300,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end

! 10 - ANGLE - a(O-H-NZ2)
&rst iat = 5944, 5945, 2300,
      r1 = -500, r2 = ${b}, r3 = ${b}, r4 = 500,
      rk2 = 0, rk3 = 0,
      &end
EOF

    # Fin de la creación de restricciones para la ventana actual.
done

# Fin del script.
