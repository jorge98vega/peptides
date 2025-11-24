#!/bin/bash

# Este script automatiza la ejecución de múltiples pasos de la simulación WHAM para cada ventana.
# Requiere la especificación de la entrada, ventana, límite, paso y el ID de trabajo anterior para encadenar los trabajos de SLURM.
# Cada paso prepara, ejecuta y organiza los trabajos de la simulación para calcular los perfiles de potencial de free-energy.
# Ejemplo de cómo usar el script - windows de 10_1 a 10_49, empezando por la 10_25:
# ./run_all_wham2d.sh 4t8sXwL_run40w 10 25 49 0

INPUT=$1  # Archivo de entrada (por ejemplo, archivo .top de Amber)
fixedwindow=$2  # Ventana de la coordenada fija
window=$3  # Número de ventana actual
limit=$4  # Límite de ventanas (última ventana a procesar)
step=$5  # Paso actual
OLD_JOB_ID=$6  # ID del trabajo anterior (para establecer dependencias de ejecución)
wd=$(pwd)  # Obtener el directorio de trabajo actual

# Si el paso es 0 (preparación inicial):
if [ $step -eq 0 ]; then
    # Copiar archivos de entrada a la ventana correspondiente
    cp ${wd}/${INPUT}.top ${wd}/MD_wham2d.sh ${wd}/run_wham2d.sh ${wd}/wham_${fixedwindow}_${window}/
    #cp ${wd}/${INPUT}_wham_0.rst ${wd}/wham_${fixedwindowd}_${window}/${INPUT}_wham_${fixedwindow}_${window}_0.rst

    # Cambiar al directorio de la ventana
    cd ${wd}/wham_${fixedwindow}_${window}/
    echo "Window ${fixedwindow}_${window} - Step $step"
    
    # Enviar trabajo para preparar la ventana y obtener el JOB_ID de SLURM
    JOB_ID=$(sbatch -J "wham_${fixedwindow}_${window}" run_wham2d.sh $INPUT $fixedwindow $window 1 8000 $step | awk '{print $4}')
    echo "Job $JOB_ID"

    # Enviar trabajo para la simulación WHAM, dependiente del trabajo anterior
    #sbatch -J "wham${window}" -d afterany:$((JOB_ID)) run_wham.sh $INPUT $window 2 5000
    
    cd $wd
    # Llamada recursiva para la ventana anterior
    if [[ $window -gt 1 ]]; then
        new_window=$((window-1))
        new_step=$((step-1))
        ./run_all_wham2d.sh $INPUT $fixedwindow $new_window $limit $new_step $((JOB_ID))
    fi
    # Llamada recursiva para la ventana siguiente
    if [[ $window -lt $limit ]]; then
        new_window=$((window+1))
        new_step=$((step+1))
        ./run_all_wham2d.sh $INPUT $fixedwindow $new_window $limit $new_step $((JOB_ID))
    fi

# Si el paso no es 0:
else
    # Copiar archivos de entrada a la ventana correspondiente
    cp ${wd}/${INPUT}.top ${wd}/MD_wham2d.sh ${wd}/run_wham2d.sh ${wd}/wham_${fixedwindow}_${window}/
    
    # Cambiar al directorio de la ventana
    cd ${wd}/wham_${fixedwindow}_${window}/
    echo "Window ${fixedwindow}_${window} - Step $step"
    
    # Enviar trabajo para preparar la ventana, dependiente del trabajo anterior
    JOB_ID=$(sbatch -J "wham_${fixedwindow}_${window}" -d afterok:${OLD_JOB_ID} run_wham2d.sh $INPUT $fixedwindow $window 1 8000 $step | awk '{print $4}')
    echo "Job $JOB_ID"

    # Enviar trabajo para la simulación WHAM, dependiente del trabajo anterior
    #sbatch -J "wham${window}" -d afterany:$((JOB_ID)) run_wham.sh $INPUT $window 2 5000
    
    cd $wd
    # Llamada recursiva para la ventana anterior si el paso es negativo y la ventana es mayor que 0
    if [[ $step -lt 0 ]] && [[ $window -gt 1 ]]; then
        new_window=$((window-1))
        new_step=$((step-1))
        ./run_all_wham2d.sh $INPUT $fixedwindow $new_window $limit $new_step $((JOB_ID))
    # Llamada recursiva para la ventana siguiente si el paso es positivo y la ventana es menor que el límite
    elif [[ $step -gt 0 ]] && [[ $window -lt $limit ]]; then
        new_window=$((window+1))
        new_step=$((step+1))
        ./run_all_wham2d.sh $INPUT $fixedwindow $new_window $limit $new_step $((JOB_ID))
    fi
fi
