#!/bin/bash

# Este script automatiza la ejecución de múltiples pasos de la simulación WHAM para cada ventana.
# Requiere la especificación de la entrada, ventana, límite, paso y el ID de trabajo anterior para encadenar los trabajos de SLURM.
# Cada paso prepara, ejecuta y organiza los trabajos de la simulación para calcular los perfiles de potencial de free-energy.

INPUT="4t8sXwL_run40w"  # Archivo de entrada (por ejemplo, archivo .top de Amber)
window=25  # Número de ventana actual
limit=50  # Límite de ventanas (última ventana a procesar)
step=0  # Paso actual
OLD_JOB_ID=""  # ID del trabajo anterior (para establecer dependencias de ejecución)
wd=$(pwd)  # Obtener el directorio de trabajo actual

# Si el paso es 0 (preparación inicial):
if [ $step -eq 0 ]; then
    # Copiar archivos de entrada a la ventana correspondiente
    cp ${wd}/${INPUT}.top ${wd}/wham${window}/
    cp ${wd}/${INPUT}_wham_0.rst ${wd}/wham${window}/${INPUT}_wham${window}_0.rst

    # Cambiar al directorio de la ventana
    cd ${wd}/wham${window}/
    echo "Window $window - Step $step"
    
    # Enviar trabajo para preparar la ventana y obtener el JOB_ID de SLURM
    JOB_ID=$(sbatch -J "prep${window}" run_wham.sh $INPUT $window 1 2000 $step | awk '{print $4}')

    # Enviar trabajo para la simulación WHAM, dependiente del trabajo anterior
    sbatch -J "wham${window}" -d afterany:$((JOB_ID)) run_wham.sh $INPUT $window 2 5000
    
    echo "Job $JOB_ID"
    cd $wd

    # Llamada recursiva para la ventana anterior (si corresponde)
    new_window=$((window-1))
    new_step=$((step-1))
    ./run_all_wham.sh $new_window $new_step $((JOB_ID))

    # Llamada recursiva para la ventana siguiente (si corresponde)
    new_window=$((window+1))
    new_step=$((step+1))
    ./run_all_wham.sh $new_window $new_step $((JOB_ID))

# Si el paso no es 0 (se están ejecutando los trabajos de simulación):
else
    # Copiar archivos de entrada a la ventana correspondiente
    cp ${wd}/${INPUT}.top ${wd}/wham${window}/
    
    # Cambiar al directorio de la ventana
    cd ${wd}/wham${window}/
    echo "Window $window - Step $step"
    
    # Enviar trabajo para preparar la ventana, dependiente del trabajo anterior
    JOB_ID=$(sbatch -J "prep${window}" -d afterok:${OLD_JOB_ID} run_wham.sh $INPUT $window 1 2000 $step | awk '{print $4}')

    # Enviar trabajo para la simulación WHAM, dependiente del trabajo anterior
    sbatch -J "wham${window}" -d afterany:$((JOB_ID)) run_wham.sh $INPUT $window 2 5000
    
    echo "Job $JOB_ID"
    cd $wd

    # Llamada recursiva para la ventana anterior si el paso es negativo y la ventana es mayor que 0
    if [[ $step -lt 0 ]] && [[ $window -gt 0 ]]; then
        new_window=$((window-1))
        new_step=$((step-1))
        ./run_all_wham.sh $new_window $limit $new_step $((JOB_ID))
    # Llamada recursiva para la ventana siguiente si el paso es positivo y la ventana es menor que el límite
    elif [[ $step -gt 0 ]] && [[ $window -lt $limit ]]; then
        new_window=$((window+1))
        new_step=$((step+1))
        ./run_all_wham.sh $new_window $limit $new_step $((JOB_ID))
    fi
fi
