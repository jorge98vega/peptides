#!/bin/bash

# Uso: ./concat_trajectories.sh /ruta/al/directorio

if [ $# -ne 2 ]; then
  echo "Uso: $0 <directorio> <ventana c1>"
  exit 1
fi

DIR="$1"
WINDOW="$2"

# Ir al directorio
cd "$DIR" || { echo "❌ No se pudo entrar en $DIR"; exit 1; }

# Buscar el archivo .top (topología)
TOP_FILE=$(ls *.top 2>/dev/null | head -n 1)

if [ -z "$TOP_FILE" ]; then
  echo "❌ No se encontró ningún archivo .top en $DIR"
  exit 1
fi

# Nombre base (sin extensión)
BASE_NAME="${TOP_FILE%.top}"

# Archivo de salida
OUT_FILE="${BASE_NAME}_${WINDOW}_allwindows.nc"

# Crear input para cpptraj
CPPTRAJ_IN="concat.in"

echo "parm $TOP_FILE" > "$CPPTRAJ_IN"

# Añadir todas las trayectorias en orden wham1, wham2...
for whamdir in $(ls -d wham_${WINDOW}_*/ 2>/dev/null | sort -V); do
  TRAJ=$(ls "$whamdir"/*.nc 2>/dev/null | head -n 1)
  if [ -n "$TRAJ" ]; then
    echo "trajin $TRAJ" >> "$CPPTRAJ_IN"
  else
    echo "⚠️ No se encontró .nc en $whamdir"
  fi
done

echo "trajout $OUT_FILE netcdf" >> "$CPPTRAJ_IN"

# Ejecutar cpptraj
echo "🚀 Ejecutando cpptraj..."
cpptraj -i "$CPPTRAJ_IN"

# Borrar input temporal
rm -f "$CPPTRAJ_IN"

echo "✅ Trayectorias concatenadas en $OUT_FILE"

