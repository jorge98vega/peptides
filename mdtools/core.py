### IMPORTS ###


import os
import re
import glob
import math
import time
import json
import pickle
import numpy as np
import pandas as pd
import seaborn as sns
import networkx as nx
import ruptures as rpt
from scipy.spatial import distance_matrix
from scipy.spatial.distance import pdist
from scipy.signal import argrelmax
import matplotlib as mpl
import matplotlib.pyplot as plt
import matplotlib.colors as clr
import matplotlib.path as mpath
import matplotlib.collections as mcoll
from matplotlib.gridspec import GridSpec
from mpl_toolkits.mplot3d import axes3d
import mdtraj as md


### CORE ###


def orient(p, p0, pA, pB, axes_order="ZX"):
    '''
    Cambia las coordenadas de "p" a un nuevo sistema de referencia donde:
    - "p0" es el origen.
    - "pA" define el primer eje de la base.
    - "pB" define el segundo eje de la base, proyectado ortogonalmente.
    - "axes_order" especifica los ejes elegidos (por ejemplo, "ZX", "XY", etc.).
    '''
    
    # Diccionario para mapear ejes a índices
    axes = {'X': 0, 'Y': 1, 'Z': 2}

    # Primer eje: normalización de pA - p0
    vA = pA - p0
    uA = vA / np.linalg.norm(vA)

    # Segundo eje: proyección ortogonal de pB - p0 sobre el plano perpendicular a uA
    wB = pB - p0
    vB = wB - np.dot(wB, uA) * uA  # Proyección
    uB = vB / np.linalg.norm(vB)   # Normalización

    # Determinar si el producto cruzado es A × B o B × A
    cross_sign = 1 if axes_order in ["ZX", "XY", "YZ"] else -1
    uC = np.cross(uA, uB) * cross_sign  # Corrige la orientación si es necesario

    # Vector donde guardamos los nuevos ejes
    us = [None, None, None]
    us[axes[axes_order[0]]] = uA
    us[axes[axes_order[1]]] = uB

    # Encontrar el índice que falta
    remaining_index = 3 - (axes[axes_order[0]] + axes[axes_order[1]])
    us[remaining_index] = uC  # Asignar el tercer eje

    # Extraer los vectores en orden
    uX, uY, uZ = us

    # Transformar el punto a las nuevas coordenadas
    vp = p - p0
    orientado = np.array([np.dot(vp, uX), np.dot(vp, uY), np.dot(vp, uZ)])

    return orientado


def recenter_traj_RMSD(run_name, N_tubes, N_res):
    '''
    Reorienta la trayectoria de una simulación MD (Molecular Dynamics) 
    para que las coordenadas se centren en un nuevo sistema de referencia basado 
    en los centros de masa de diferentes partes de los nanotubos.

    Parámetros:
    - run_name: Nombre de los archivos de entrada y salida (sin extensión).
    - N_tubes: Número de nanotubos.
    - N_res: Número de residuos que componen los anillos de los nanotubos.
    '''
    
    # Carga la trayectoria MD y la topología
    traj = md.load(run_name+"_MD.nc", top=run_name+".parm7")
    
    # Selección de los átomos de carbono alfa (CA) de todos los nanotubos
    CAs = traj.top.select("name==CA")
    # Dividimos los átomos de carbono alfa en los diferentes nanotubos
    CAs_tube1 = CAs[0:int(CAs.size/N_tubes)]
    CAs_tube2 = CAs[int(CAs.size/N_tubes):int(2*CAs.size/N_tubes)]
    CAs_tube3 = CAs[int(2*CAs.size/N_tubes):int(3*CAs.size/N_tubes)]
    CAs_tube4 = CAs[int(3*CAs.size/N_tubes):int(4*CAs.size/N_tubes)]
    # Seleccionamos los carbonos alfa de la parte superior e inferior de los tubos
    CAs_top = np.concatenate((CAs_tube1[0:N_res], CAs_tube2[0:N_res], CAs_tube3[0:N_res], CAs_tube4[0:N_res]))
    CAs_bot = np.concatenate((CAs_tube1[-N_res:], CAs_tube2[-N_res:], CAs_tube3[-N_res:], CAs_tube4[-N_res:]))
    
    step = len(traj)-1  # (último frame)
    # Calculamos los centros de masa para los puntos p0, pZ y pX
    p0 = np.sum(traj.xyz[step][CAs], axis=0)/CAs.size  # centro de masa de todos los átomos de CA en la simulación
    pZ = np.sum(traj.xyz[step][CAs_top], axis=0)/CAs_top.size  # centro de masa de los átomos de CA en los primeros anillos de los nanotubos
    pX = np.sum(traj.xyz[step][CAs_tube1], axis=0)/CAs_tube1.size  # centro de masa del tubo 1 (solo átomos de CA)
    
    # Creamos una lista para almacenar las coordenadas de los átomos orientados
    selection = CAs
    xyz = []
    # Reorientamos las coordenadas de cada átomo en la selección
    for atom in selection:
        xyz.append(orient(traj.xyz[step][atom], p0, pZ, pX))

    # Creamos una nueva trayectoria con las coordenadas orientadas
    oriented = md.Trajectory(xyz, traj.top.subset(selection))
    # Realizamos la superposición RMSD con el primer frame (0)
    traj.superpose(oriented, 0, atom_indices=selection, ref_atom_indices=range(oriented.n_atoms))
    # Guardamos la nueva trayectoria alineada
    traj.save(run_name+"_RMSD.nc")


class MyAtom():
    '''
    Representa un átomo con información adicional sobre su índice, nombre, residuos
    y su ubicación en nanotubos (si aplica).
    '''
    
    def __new__(cls, *args, **kwargs):
        return super().__new__(cls)

    def __init__(self, top, N_rings, N_res, index):
        '''
        Inicializa MyAtom con datos de un átomo en una simulación.
        top: Topología, N_rings: número de anillos, N_res: número de residuos, index: índice del átomo.
        '''
        atom = top.atom(index)
        self.index = index
        self.name = atom.name
        self.resid = atom.residue.index
        self.resname = atom.residue.name
        
        if atom.residue.is_protein:
            self.tube = atom.residue.index // (N_rings * N_res)
            self.layer = (atom.residue.index // N_res) % N_rings
        else:
            self.tube = None
            self.layer = None

    @classmethod
    def from_string(cls, string):
        '''
        Crea MyAtom a partir de su representación en string.
        '''
        regex = r"MyAtom\(index=(\d+), name=(\w+[\+\-]?), resid=(\d+), resname=(\w+[\+\-]?), tube=(\w+), layer=(\w+)\)"
        result = re.search(regex, string)
        
        myatom = cls.__new__(cls)
        myatom.index = int(result.groups()[0])
        myatom.name = result.groups()[1]
        myatom.resid = int(result.groups()[2])
        myatom.resname = result.groups()[3]
        
        # Maneja el caso de None para tube y layer
        if result.groups()[4] == "None":
            myatom.tube = None
            myatom.layer = None
        else:
            myatom.tube = int(result.groups()[4])
            myatom.layer = int(result.groups()[5])
        
        return myatom

    def __str__(self):
        ''' Devuelve una representación en string de MyAtom. '''
        return f"MyAtom(index={self.index}, name={self.name}, resid={self.resid}, resname={self.resname}, tube={self.tube}, layer={self.layer})"
    
    def __repr__(self):
        ''' Devuelve una representación oficial de MyAtom. '''
        return f"MyAtom(index={self.index}, name={self.name}, resid={self.resid}, resname={self.resname}, tube={self.tube}, layer={self.layer})"


def select_atoms(top, N_rings, N_res, selection):
    '''
    Selecciona los átomos de la topología según un criterio y devuelve una lista de objetos MyAtom.
    
    top: Topología de la simulación.
    N_rings: Número de anillos en cada nanotubo.
    N_res: Número de residuos en cada nanotubo.
    selection: Criterio de selección (expresión de MDTraj).
    '''
    return np.array([
        MyAtom(top, N_rings, N_res, index)
        for index in top.select(selection)
    ])


class MyParams:
    def __init__(self, traj, N_tubes, N_rings, N_res, selections):
        '''
        Inicializa parámetros de un sistema basado en nanotubos.
        
        traj: Objeto de trayectoria de MDTraj.
        N_tubes: Número de tubos en el sistema.
        N_rings: Número de anillos en cada tubo.
        N_res: Número de residuos en cada anillo.
        selections: Selecciones adicionales de átomos para "bondable".
        '''
        
        # Definición de parámetros básicos
        self.N_tubes = N_tubes  # Número de tubos
        self.N_rings = N_rings  # Número de anillos por tubo
        self.N_res = N_res  # Número de residuos por anillo
        N_allres = N_tubes * N_rings * N_res  # Total de residuos
        self.N_allres = N_allres
        
        top = traj.top  # Obtenemos la topología de la trayectoria
        self.CAs = select_atoms(top, N_rings, N_res, "name CA")  # Selección de átomos CA
        self.bbNs = select_atoms(top, N_rings, N_res, "name N and resid 0 to " + str(N_allres-1))  # N de backbone
        self.bbOs = select_atoms(top, N_rings, N_res, "name O and resid 0 to " + str(N_allres-1))  # O de backbone
        
        # Selección de átomos que pueden formar enlaces
        bondable = np.array([], dtype=int)
        for selection in selections:
            bondable = np.concatenate((bondable, select_atoms(top, N_rings, N_res, selection)))
        self.bondable = bondable
        
        # Selección de agua e iones
        self.WATs = traj.top.select("water and name O")  # Átomos de oxígeno en agua
        self.IONs = traj.top.select("element Cl")  # Átomos de Cl (iones)


def get_reslist(N_rings, N_res, tube, residues):
    '''
    Genera una lista de residuos en función del número de tubos, anillos y residuos.

    N_rings: Número de anillos en el tubo.
    N_res: Número de residuos por anillo.
    tube: Índice del tubo.
    residues: Lista de residuos a seleccionar de cada anillo.

    Ejemplo:
    get_reslist(6, 8, 0, [1, 3]) devuelve: [1, 11, 17, 27, 33, 43]
    Cada ring tiene 8 residuos, que numeramos del 0 al 7.
    Para el primer ring del tubo 0 devuelve el resid del residuo 1 del ring,
    para el segundo ring del tubo 0 devuelve el resid del residuo 3 del ring.
    Para el tercer ring de nuevo el residuo 1, para el cuarto ring el residuo 3 y así...
    '''
    reslist = []
    for layer in range(N_rings):  # Itera sobre los anillos (layers)
        # Calcula el residuo para cada capa en función de la selección de 'residues'
        reslist.append(tube * N_rings * N_res + layer * N_res + residues[layer % len(residues)])
    
    return reslist


def get_channel_reslist(N_rings, N_res, tubes, tuberesidues):
    '''
    Devuelve una lista de residuos para varios tubos concatenados.
    
    N_rings: Número de anillos por tubo.
    N_res: Número de residuos por anillo.
    tubes: Lista de índices de los tubos.
    tuberesidues: Lista de listas de residuos para cada tubo.

    Ejemplo:
    get_channel_reslist(6, 8, [0, 1], [[1, 3], [5, 5]]) devuelve la concatenación de las listas de residuos de ambos tubos.
    '''
    reslist = []
    for i, tube in enumerate(tubes):
        # Concatena los resultados de get_reslist para cada tubo
        reslist += get_reslist(N_rings, N_res, tube, tuberesidues[i])
    
    return reslist


def get_atoms_in_reslist(myatoms, reslist):
    '''
    Devuelve una lista de átomos cuyos residuos están en reslist.
    
    myatoms: Lista de objetos MyAtom.
    reslist: Lista de índices de residuos a seleccionar.
    '''
    return np.array([atom for atom in myatoms if atom.resid in reslist])


def get_indices(myatoms):
    '''
    Devuelve los índices de los átomos en myatoms.
    
    myatoms: Lista de objetos MyAtom.
    '''
    return np.array([atom.index for atom in myatoms])


def get_indices_in_layer(myatoms, layer):
    '''
    Devuelve los índices de los átomos en un determinado layer.
    
    myatoms: Lista de objetos MyAtom.
    layer: Capa de la que se desea obtener los átomos.
    '''
    return np.array([atom.index for atom in myatoms if atom.layer == layer])


def get_indices_between_layers(myatoms, firstlayer, lastlayer):
    '''
    Devuelve los índices de los átomos entre dos capas (inclusive).
    
    myatoms: Lista de objetos MyAtom.
    firstlayer: Capa inicial.
    lastlayer: Capa final.
    '''
    indices = np.array([], dtype=int)
    for layer in range(firstlayer, lastlayer+1):
        indices = np.concatenate((indices, get_indices_in_layer(myatoms, layer)))
    return indices


def wrap_coordinates(point, box):
    '''
    Coordenadas de un punto dentro de los límites de la caja (sólo para celdas ortoédricas).
    
    point: Coordenada del punto (array de 3 elementos).
    box: Dimensiones de la caja de simulación (array de 3 elementos).
    
    Devuelve el punto dentro de la caja.
    '''
    # Copia el punto para no modificar el original
    wrapped_point = np.copy(point)
    
    # Coordenadas de cada dimensión
    for dim in range(3):
        wrapped_point[dim] = ((point[dim] + box[dim]/2) % box[dim]) - box[dim]/2
    
    return wrapped_point


def periodic_pdist(positions, box):
    '''
    Calcula la distancia periódica entre todas las posiciones de átomos considerando las condiciones periódicas de la caja.
    
    positions: Matriz de posiciones de los átomos (número de átomos x 3).
    box: Dimensiones de la caja de simulación (array de 3 elementos).
    
    Devuelve la distancia periódica entre todas las posiciones.
    '''
    dist = 0
    
    for dim in range(3):  # Itera sobre cada dimensión (x, y, z)
        pddim = pdist(positions[:, dim].reshape(positions.shape[0], 1))  # Calcula la distancia entre átomos en la dimensión actual
        pddim[pddim > 0.5 * box[dim]] -= box[dim]  # Aplica las condiciones periódicas: ajusta las distancias mayores que la mitad de la caja
        dist += pddim ** 2  # Acumula la distancia total
        
    return np.sqrt(dist)  # Devuelve la distancia total como la raíz cuadrada de la suma de distancias al cuadrado


def decorate_ax(ax, title, titlesize, xlabel, ylabel, labelsize, ticksize, linewidth, length, legend):
    '''
    Configura la apariencia de un gráfico (títulos, etiquetas, ticks, etc.).
    
    ax: El objeto de ejes del gráfico.
    title: Título del gráfico.
    titlesize: Tamaño de la fuente del título.
    xlabel: Etiqueta del eje X.
    ylabel: Etiqueta del eje Y.
    labelsize: Tamaño de la fuente de las etiquetas.
    ticksize: Tamaño de las etiquetas de los ticks.
    linewidth: Grosor de las líneas (ejes y ticks).
    length: Longitud de los ticks.
    legend: Booleano para mostrar la leyenda.
    '''
    # Configura el título y etiquetas con los tamaños especificados
    ax.set_title(title, fontsize=titlesize, pad=titlesize)
    ax.set_xlabel(xlabel, fontsize=labelsize)
    ax.set_ylabel(ylabel, fontsize=labelsize)
    
    # Configura los parámetros de los ticks (ubicación, tamaño y grosor)
    ax.tick_params(top=True, right=True, labelsize=ticksize, width=linewidth, length=length)
    
    # Establece el grosor de las líneas del gráfico
    for axis in ['top', 'bottom', 'left', 'right']:
        ax.spines[axis].set_linewidth(linewidth)
    
    # Si se pide una leyenda, la agrega
    if legend:
        ax.legend(fontsize=ticksize, edgecolor='0.75')
