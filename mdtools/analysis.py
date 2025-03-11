### IMPORTS ###


from mdtools.core import *


### ANALYSIS ###


def get_indices(traj, WATs, IONs, CAs, N_rings, layer=0, boundary=None,
                delta=0.1, delta_r=None, delta_z=None, offset=None,
                preselected=False, save=True, savefileWATs="iterWATs", savefileIONs="iterIONs", first=None, last=None):
    """
    Guarda los índices de moléculas de agua (WATs) e iones (IONs) que están entre dos capas en un sistema
    a lo largo de una trayectoria.

    Parámetros:
    - traj: Trayectoria de MDTraj.
    - WATs: Lista de índices de átomos de oxígeno de moléculas de agua.
    - IONs: Lista de índices de iones.
    - CAs: Lista de átomos de carbono alfa (CAs) que definen la estructura de referencia.
    - N_rings: Número total de anillos en la estructura.
    - layer: Número de anillos a excluir desde los extremos.
    - boundary: Límite de exclusión (por defecto, igual a `layer`).
    - delta: Ajuste general para dimensiones espaciales.
    - delta_r: Ajuste del radio de selección.
    - delta_z: Ajuste de la altura de selección.
    - offset: Vector de desplazamiento de la región de selección.
    - preselected: Indica si WATs e IONs ya están preseleccionados por frame.
    - save: Guarda los resultados en archivos.
    - savefileWATs: Nombre base del archivo para guardar índices de agua.
    - savefileIONs: Nombre base del archivo para guardar índices de iones.
    - first: Primer frame a analizar.
    - last: Último frame a analizar.
    """
    # Inicializar parámetros opcionales
    if boundary is None: boundary = layer
    if delta_r is None: delta_r = delta
    if delta_z is None: delta_z = delta
    if offset is None: offset = np.array([0.0, 0.0, 0.0])
    if first is None: first = 0
    if last is None: last = len(traj)
    
    # Inicializar listas para almacenar los índices de WATs e IONs
    iterWATs, iterIONs = [], []
    if layer != boundary:
        iterWATs_b, iterIONs_b = [], []
    
    # Obtener los átomos que delimitan la capa seleccionada
    atoms_top = get_indices_in_layer(CAs, layer)
    atoms_bot = get_indices_in_layer(CAs, N_rings-layer-1)
    if layer != boundary:
        atoms_top_b = get_indices_in_layer(CAs, boundary)
        atoms_bot_b = get_indices_in_layer(CAs, N_rings-boundary-1)
    
    # Si los WATs e IONs ya están preseleccionados, usar sus listas
    if preselected:
        auxWATs, auxIONs = WATs, IONs
    
    # Iterar sobre los frames de la trayectoria
    for step in range(first, last):
        frame = traj.slice(step, copy=False).xyz[0]  # Obtener la posición de los átomos en el frame actual
        
        if preselected:
            WATs, IONs = auxWATs[step], auxIONs[step]
        
        # Calcular el centro y el radio de la región de selección
        centertop = np.mean(frame[atoms_top], axis=0)
        centerbot = np.mean(frame[atoms_bot], axis=0)
        center = (centertop + centerbot) / 2
        
        rtop = np.max(distance_matrix(frame[atoms_top], frame[atoms_top]))
        rbot = np.max(distance_matrix(frame[atoms_bot], frame[atoms_bot]))
        r = max(rtop, rbot) / 2 + delta_r  # Radio ajustado
        
        # Calcular las alturas de la región de selección
        zmax = np.mean(frame[atoms_top][:, 2]) - center[2] + delta_z
        zmin = np.mean(frame[atoms_bot][:, 2]) - center[2] - delta_z
        if layer != boundary:
            zmax_b = np.mean(frame[atoms_top_b][:, 2]) - center[2] + delta_z
            zmin_b = np.mean(frame[atoms_bot_b][:, 2]) - center[2] - delta_z
        
        # Seleccionar aguas en la región
        aux, aux_b = [], []
        for atom in WATs:
            xyz = frame[atom] - (center + offset)
            if zmin < xyz[2] < zmax and (xyz[0]**2 + xyz[1]**2 < r**2):
                aux.append(atom)
            elif layer != boundary and zmin_b < xyz[2] < zmax_b and (xyz[0]**2 + xyz[1]**2 < r**2):
                aux_b.append(atom)
        
        iterWATs.append(np.array(aux))
        if layer != boundary:
            iterWATs_b.append(np.array(aux_b))
        
        # Seleccionar iones en la región
        aux, aux_b = [], []
        for atom in IONs:
            xyz = frame[atom] - (center + offset)
            if zmin < xyz[2] < zmax and (xyz[0]**2 + xyz[1]**2 < r**2):
                aux.append(atom)
            elif layer != boundary and zmin_b < xyz[2] < zmax_b and (xyz[0]**2 + xyz[1]**2 < r**2):
                aux_b.append(atom)
        
        iterIONs.append(np.array(aux))
        if layer != boundary:
            iterIONs_b.append(np.array(aux_b))
    
    # Convertir listas a arrays de objetos
    iterWATs = np.array(iterWATs, dtype=object)
    iterIONs = np.array(iterIONs, dtype=object)
    if layer != boundary:
        iterWATs_b = np.array(iterWATs_b, dtype=object)
        iterIONs_b = np.array(iterIONs_b, dtype=object)
    
    # Guardar los resultados si es necesario
    if save:
        np.save(f"{savefileWATs}.npy", iterWATs)
        np.save(f"{savefileIONs}.npy", iterIONs)
        if layer != boundary:
            np.save(f"{savefileWATs}_b.npy", iterWATs_b)
            np.save(f"{savefileIONs}_b.npy", iterIONs_b)


def get_indices_xtal(traj, WATs, IONs, CAs, N_rings, delta_r=0.0, offsets=None, # En unidades de los lattice vectors
                     save=True, savefileWATs="iterWATs", savefileIONs="iterIONs", first=None, last=None):
    """
    Guarda los índices de moléculas de agua (WATs) e iones (IONs) en una región específica de un sistema periódico
    a lo largo de una trayectoria.

    Parámetros:
    - traj: Trayectoria de MDTraj.
    - WATs: Lista de índices de átomos de oxígeno de moléculas de agua.
    - IONs: Lista de índices de iones.
    - CAs: Lista de átomos de carbono alfa (CAs) que definen la estructura de referencia.
    - N_rings: Número total de anillos en la estructura.
    - delta_r: Ajuste del radio de selección.
    - offsets: Lista de vectores de desplazamiento en unidades de los vectores de celda.
    - save: Guarda los resultados en archivos.
    - savefileWATs: Nombre base del archivo para guardar índices de agua.
    - savefileIONs: Nombre base del archivo para guardar índices de iones.
    - first: Primer frame a analizar.
    - last: Último frame a analizar.
    """
    # Inicializar parámetros opcionales
    if offsets is None: offsets = [np.array([0.0, 0.0, 0.0])]
    if first is None: first = 0
    if last is None: last = len(traj)
    
    # Inicializar listas para almacenar los índices de WATs e IONs
    iterWATs, iterIONs = [], []
    
    # Definir los átomos que delimitan la capa seleccionada
    layer = 0
    atoms_top = get_indices_in_layer(CAs, layer)
    atoms_bot = get_indices_in_layer(CAs, N_rings-layer-1)
    
    # Iterar sobre los frames de la trayectoria
    for step in range(first, last):
        frame = traj.slice(step, copy=False).xyz[0]  # Obtener posiciones de los átomos en el frame actual
        lvs = traj.slice(0, copy=False).unitcell_lengths[0]  # Vectores de celda de la simulación periódica
        
        # Calcular el centro y el radio de la región de selección
        centertop = np.mean(frame[atoms_top], axis=0)
        centerbot = np.mean(frame[atoms_bot], axis=0)
        center = (centertop + centerbot) / 2
        
        rtop = np.max(distance_matrix(frame[atoms_top], frame[atoms_top]))
        rbot = np.max(distance_matrix(frame[atoms_bot], frame[atoms_bot]))
        r = max(rtop, rbot) / 2 + delta_r  # Radio ajustado
        
        # Seleccionar aguas en la región
        aux = []
        for atom in WATs:
            for offset in offsets:
                xyz = wrap_coordinates(frame[atom], lvs) - (center + offset * lvs)
                if xyz[0]**2 + xyz[1]**2 < r**2:
                    aux.append(atom)
                    break  # Si el átomo ya está en la región, no es necesario seguir iterando
        iterWATs.append(np.array(aux))
        
        # Seleccionar iones en la región
        aux = []
        for atom in IONs:
            for offset in offsets:
                xyz = wrap_coordinates(frame[atom], lvs) - (center + offset * lvs)
                if xyz[0]**2 + xyz[1]**2 < r**2:
                    aux.append(atom)
                    break
        iterIONs.append(np.array(aux))
    
    # Convertir listas a arrays de objetos
    iterWATs = np.array(iterWATs, dtype=object)
    iterIONs = np.array(iterIONs, dtype=object)
    
    # Guardar los resultados si es necesario
    if save:
        np.save(f"{savefileWATs}.npy", iterWATs)
        np.save(f"{savefileIONs}.npy", iterIONs)


def analyse(p, traj, prelabelWATs="iterWATs", prelabelIONs="iterIONs", label=None, reslist=[], layer=0, boundary=None,
            distance_cutoff=2.5, angle_cutoff=120, first=None, last=None, xtal=False):
    """
    Analiza la trayectoria de un sistema periódico para identificar puentes de hidrógeno y puentes salinos.

    Parámetros:
    - p: Parámetro personalizado con información relevante del sistema.
    - traj: Trayectoria de MDTraj.
    - prelabelWATs: Prefijo de archivo para cargar los índices de moléculas de agua.
    - prelabelIONs: Prefijo de archivo para cargar los índices de iones.
    - label: Etiqueta específica de los archivos de entrada/salida.
    - reslist: Lista de residuos a analizar.
    - layer: Capa actual de análisis.
    - boundary: Límite superior de la capa de análisis.
    - distance_cutoff: Umbral de distancia para detección de puentes de hidrógeno (en Ångstroms).
    - angle_cutoff: Umbral de ángulo para detección de puentes de hidrógeno (en grados).
    - first: Primer frame a analizar.
    - last: Último frame a analizar.
    - xtal: Indica si el sistema es periódico.
    """
    # Inicialización de parámetros opcionales
    boundary = layer if boundary is None else boundary
    first = 0 if first is None else first
    last = len(traj) if last is None else last
    
    # Cargar los índices de agua e iones
    iterWATs = np.load(f"{prelabelWATs}_{label}.npy", allow_pickle=True)
    iterIONs = np.load(f"{prelabelIONs}_{label}.npy", allow_pickle=True)
    
    # Obtener los átomos con capacidad de formar enlaces de hidrógeno
    bondable_atoms = get_atoms_in_reslist(p.bondable, reslist)
    bondable = get_indices_between_layers(bondable_atoms, layer, p.N_rings-layer-1)
    backbone = get_indices_between_layers(np.concatenate((p.bbNs, p.bbOs)), layer, p.N_rings-layer-1)
    
    if layer != boundary:
        # Cargar índices de la capa complementaria (boundary)
        iterWATs_b = np.load(f"{prelabelWATs}_{label}_b.npy", allow_pickle=True)
        iterIONs_b = np.load(f"{prelabelIONs}_{label}_b.npy", allow_pickle=True)
        bondable_b = np.concatenate((
            get_indices_between_layers(bondable_atoms, boundary, layer-1),
            get_indices_between_layers(bondable_atoms, p.N_rings-layer, p.N_rings-boundary-1)
        ))
        backbone_b = np.concatenate((
            get_indices_between_layers(np.concatenate((p.bbNs, p.bbOs)), boundary, layer-1),
            get_indices_between_layers(np.concatenate((p.bbNs, p.bbOs)), p.N_rings-layer, p.N_rings-boundary-1)
        ))
    else:
        bondable_b = np.array([], dtype=int)
        backbone_b = np.array([], dtype=int)
    
    # Inicialización de estructuras de datos para almacenar resultados
    stats_dicts = []  # Estadísticas generales
    hbonds_dicts = []  # Lista de puentes de hidrógeno
    hbonds_G = nx.MultiDiGraph()  # Grafo de puentes de hidrógeno
    
    # Iterar sobre los frames de la trayectoria
    for step in range(first, last):
        frame = traj.slice(step, copy=False)
        
        # Obtener listas de átomos en la región de análisis
        WATs = iterWATs[step]
        IONs = iterIONs[step]
        if layer != boundary:
            WATs_b = iterWATs_b[step]
            IONs_b = iterIONs_b[step]
        else:
            WATs_b = np.array([], dtype=int)
            IONs_b = np.array([], dtype=int)
        b = np.concatenate((WATs_b, IONs_b, bondable_b, backbone_b))
        
        N_hbonds = 0
        d_ave = 0.0
        
        # Buscar puentes de hidrógeno
        interesting_atoms = np.concatenate((WATs, IONs, bondable, backbone, b))
        triplets, distances, angles, presence = md.baker_hubbard(
            frame, periodic=xtal, interesting_atoms=interesting_atoms, return_geometry=True,
            distance_cutoff=0.1 * distance_cutoff, angle_cutoff=angle_cutoff
        )
        
        # Evitar conteo doble
        ignore_indices = []
        u, c = np.unique(triplets[presence[0]][:, 1], return_counts=True)
        for duplicate in u[c > 1]:
            indices, = np.where(triplets[presence[0]][:, 1] == duplicate)
            dmin_index = np.argmin(distances[0][presence[0]][indices])
            ignore_indices += [index for index in np.delete(indices, dmin_index)]
        
        # Guardar información de los puentes de hidrógeno
        for index, ((donor, h, acceptor), d, theta) in enumerate(zip(triplets[presence[0]], distances[0][presence[0]], angles[0][presence[0]])):
            if index in ignore_indices or (donor in b and acceptor in b) or (donor in backbone and acceptor in backbone):
                continue
            
            mydonor = MyAtom(traj.top, p.N_rings, p.N_res, donor)
            myacceptor = MyAtom(traj.top, p.N_rings, p.N_res, acceptor)
            hbonds_G.add_edge(donor, acceptor, step=step, h=h, d=10.0*d)
            hbonds_dicts.append({
                'step': step, 'donor': mydonor, 'h': h, 'acceptor': myacceptor,
                'd': 10.0 * d, 'theta': theta * 180.0 / np.pi
            })
            N_hbonds += 1
            d_ave += d
        
        # Guardar estadísticas del frame actual
        d_ave = d_ave / N_hbonds if N_hbonds != 0 else 0.0
        stats_dicts.append({'step': step, 'N_WATs': len(WATs), 'N_IONs': len(IONs), 'N_HBonds': N_hbonds, 'ave_dist': 10.0 * d_ave})
    
    # Guardar los resultados en archivos
    pickle.dump(hbonds_G, open(f"{label}_hbondsG.dat", 'wb'))
    pd.DataFrame(hbonds_dicts).to_csv(f"{label}_hbonds.csv")
    pd.DataFrame(stats_dicts).to_csv(f"{label}_stats.csv")


def detail_hbonds(label):
    '''
    Procesa un archivo CSV con información sobre puentes de hidrógeno (H-bonds)
    y genera un nuevo archivo con detalles agregados por tipo de interacción.

    label: Prefijo del archivo CSV de entrada y salida.
    '''
    hbonds_df = pd.read_csv(label + "_hbonds.csv")
    Nsteps = hbonds_df['step'].max() + 1

    # Lista para almacenar los detalles de los puentes de hidrógeno
    detail_dicts = []

    for step in range(Nsteps):
        aux_df = hbonds_df[hbonds_df["step"] == step]
        atoms = []
        nhbonds = []
        dists = []

        for _, hbond in aux_df.iterrows():
            donor = MyAtom.from_string(hbond['donor'])
            acceptor = MyAtom.from_string(hbond['acceptor'])
            
            # Identificación del par donador-aceptor sin números en los nombres
            atoms_dict = {
                'donor': donor.resname + "-" + re.sub(r'\d+', '', donor.name),
                'acceptor': acceptor.resname + "-" + re.sub(r'\d+', '', acceptor.name)
            }

            # Si es un nuevo par, lo añadimos
            if atoms_dict not in atoms:
                atoms.append(atoms_dict)
                nhbonds.append(1)
                dists.append(hbond['d'])
            else:
                index = atoms.index(atoms_dict)
                nhbonds[index] += 1
                dists[index] += hbond['d']

        # Agregar los datos agregados al diccionario de detalles
        for pair, nhb, d in zip(atoms, nhbonds, dists):
            detail_dicts.append({
                'step': step, 'donor': pair['donor'], 'acceptor': pair['acceptor'],
                'N_HBonds': nhb, 'd': d / nhb  # Distancia media
            })

    # Guardar los detalles en un nuevo CSV
    detail_df = pd.DataFrame(detail_dicts)
    detail_df.to_csv(label + "_detail.csv", index=False)


def search_longestpaths(traj, label, xtal=False, first=None, last=None, update=1000):
    '''
    Busca y almacena las rutas más largas y los clusters más grandes de H-bonds en la trayectoria.

    traj: Trayectoria de simulación.
    label: Prefijo de los archivos de salida.
    xtal: Si es True, aplica corrección periódica en z.
    first, last: Rango de pasos de la trayectoria a analizar.
    update: Frecuencia de impresión del progreso.
    '''

    def wrap(dz, lvsz):
        return ((dz + lvsz / 2) % lvsz) - lvsz / 2

    hbondsG = pickle.load(open(label + '_hbondsG.dat', 'rb'))
    if first is None: first = 0
    if last is None: last = len(traj)
    start = time.time()

    cluster_dicts, path_dicts = [], []

    for step in range(first, last):
        if step % update == 0:
            print(step, time.time() - start, "s")
            start = time.time()

        frame = traj.slice(step, copy=False).xyz[0]
        if xtal:
            lvs = traj.slice(0, copy=False).unitcell_lengths[0]  # nm

        auxG = nx.MultiDiGraph(
            (u, v, d) for u, v, d in hbondsG.edges(data=True) if d['step'] == step
        )

        largest_cluster = {'step': step, 'nodes': [], 'residues': [], 'size': 0.0, 'ratio': 0.0, 'nratio': 0.0, 'percolating': 0}
        longest_path = {'step': step, 'path': [], 'residues': [], 'dz': 0.0, 'ratio': 0.0}

        # Cálculo de caminos más largos y clusters
        paths = dict(nx.all_pairs_shortest_path(auxG))
        for node1, subpaths in paths.items():
            # Clusters
            cluster_size = len(subpaths)
            if cluster_size > largest_cluster['size']:
                largest_cluster.update({'nodes': list(subpaths.keys()), 'size': cluster_size})

            # Caminos más largos
            for node2, path in subpaths.items():
                dz = 10.0 * (frame[node2][2] - frame[node1][2])
                if xtal:
                    dz = sum(
                        wrap(10.0 * (frame[path[i + 1]][2] - frame[path[i]][2]), 10 * lvs[2])
                        if abs(10.0 * (frame[path[i + 1]][2] - frame[path[i]][2])) > 10.0 * lvs[2] / 2
                        else 10.0 * (frame[path[i + 1]][2] - frame[path[i]][2])
                        for i in range(len(path) - 1)
                    )

                if abs(dz) > abs(longest_path['dz']):
                    longest_path.update({'path': path, 'dz': dz})

        # Búsqueda de ciclos en sistemas periódicos
        if xtal:
            for cycle in sorted(nx.simple_cycles(auxG)):
                cycle.append(cycle[0])
                dz = sum(
                    wrap(10.0 * (frame[cycle[i + 1]][2] - frame[cycle[i]][2]), 10 * lvs[2])
                    if abs(10.0 * (frame[cycle[i + 1]][2] - frame[cycle[i]][2])) > 10.0 * lvs[2] / 2
                    else 10.0 * (frame[cycle[i + 1]][2] - frame[cycle[i]][2])
                    for i in range(len(cycle) - 1)
                )

                if abs(dz) > abs(longest_path['dz']):
                    longest_path.update({'path': cycle, 'dz': dz})
                    if abs(dz) >= 10 * lvs[2]:
                        largest_cluster['percolating'] = 1
                        break  # Terminar búsqueda en cuanto se detecta un ciclo percolante

        # Cálculo de métricas del cluster más grande
        largest_cluster['ratio'] = largest_cluster['size'] / auxG.number_of_nodes()
        source = largest_cluster['nodes'][0]
        reachable_nodes = sum(
            1 for n in auxG.nodes if traj.top.atom(n).residue.name != 'LYS'
        ) + int(traj.top.atom(source).residue.name == 'LYS')
        largest_cluster['nratio'] = largest_cluster['size'] / reachable_nodes
        largest_cluster['residues'] = [traj.top.atom(node).residue.name for node in largest_cluster['nodes']]
        cluster_dicts.append(largest_cluster)

        # Normalización de desplazamiento en sistemas periódicos
        if xtal:
            longest_path['ratio'] = abs(longest_path['dz'] / (10.0 * lvs[2]))
        longest_path['residues'] = [traj.top.atom(node).residue.name for node in longest_path['path']]
        path_dicts.append(longest_path)

    # Guardar resultados
    pd.DataFrame(cluster_dicts).to_csv(label + "_largestclusters.csv", index=False)
    pd.DataFrame(path_dicts).to_csv(label + "_longestpaths.csv", index=False)


def search_paths_res(traj, label, resnamelist, first=None, last=None):
    """
    Busca caminos en la red de puentes de hidrógeno que sigan un orden específico de residuos.

    Parámetros:
    - traj: trayectoria de la simulación.
    - label: prefijo para cargar y guardar archivos de datos.
    - resnamelist: lista de nombres de residuos en el orden a buscar en los caminos.
    - first: primer frame a analizar (opcional, por defecto 0).
    - last: último frame a analizar (opcional, por defecto longitud de la trayectoria).

    Salida:
    - CSV con los caminos encontrados que siguen la secuencia de residuos especificada.
    """

    def search_neighbors_res(G, nodes, resnamelist, path, path_dicts):
        """
        Busca caminos en el grafo G siguiendo la secuencia de residuos dada.

        Parámetros:
        - G: grafo dirigido con los enlaces de puentes de hidrógeno.
        - nodes: lista de nodos actuales en el grafo.
        - resnamelist: secuencia de residuos que deben aparecer en el camino.
        - path: camino actual en construcción.
        - path_dicts: lista de diccionarios donde se guardarán los caminos encontrados.
        """
        if not resnamelist:  # Si ya se ha recorrido toda la secuencia, guardamos el camino
            path_dicts.append({'step': step, 'path': path})
            return
        
        for node in nodes:
            if traj.top.atom(node).residue.name != resnamelist[0]:
                continue  # Solo seguimos caminos que coincidan con el siguiente residuo de la secuencia
            
            aux_path = path.copy()
            aux_path.append(node)  # Agregamos el nodo al camino actual
            
            # Exploramos vecinos en busca del siguiente residuo en la secuencia
            search_neighbors_res(G, G.neighbors(node), resnamelist[1:], aux_path, path_dicts)

    # Cargamos el grafo con la información de los puentes de hidrógeno
    hbondsG = pickle.load(open(label + '_hbondsG.dat', 'rb'))
    
    if first is None: first = 0
    if last is None: last = len(traj)

    # Creamos un identificador de la secuencia de residuos para el archivo de salida
    reslabel = "-".join(resnamelist)

    path_dicts = []
    for step in range(first, last):
        frame = traj.slice(step, copy=False).xyz[0]  # Extraemos la posición de los átomos en este frame
        
        # Filtramos el grafo para obtener solo los enlaces del frame actual
        auxG = nx.MultiDiGraph((u, v, d) for u, v, d in hbondsG.edges(data=True) if d['step'] == step)
        
        nodes = list(auxG.nodes)  # Lista de nodos en el frame actual
        search_neighbors_res(auxG, nodes, resnamelist, [], path_dicts)  # Buscamos caminos

    # Guardamos los caminos encontrados en un archivo CSV
    path_df = pd.DataFrame(path_dicts)
    path_df.to_csv(label + "_paths_" + reslabel + ".csv")


def water_channel_stability(traj, regex="iterWATs_channel*.npy", width=100, model="l2", dz=2.5, method="onebyone", 
                            first=None, last=None, savefile="water_stability.csv"):
    """
    Analiza la estabilidad de las moléculas de agua dentro de un canal en la trayectoria de simulación.

    Parámetros:
    - traj: trayectoria de la simulación.
    - regex: patrón para encontrar archivos de datos de agua.
    - width: tamaño de ventana para la detección de cambios en la posición del agua.
    - model: modelo de segmentación usado por ruptures (por defecto "l2").
    - dz: umbral en Ångstroms para considerar un cambio significativo en la posición del agua.
    - method: método de búsqueda de cambios ("onebyone" o "direct").
    - first: primer frame a analizar (opcional, por defecto 0).
    - last: último frame a analizar (opcional, por defecto longitud de la trayectoria).
    - savefile: nombre del archivo CSV donde se guardarán los resultados.

    Salida:
    - Archivo CSV con los intervalos de estabilidad de cada molécula de agua en el canal.
    """

    def get_filepaths_with_glob(root_path: str, file_regex: str):
        """Devuelve una lista de archivos en el directorio que coincidan con el patrón especificado."""
        return glob.glob(os.path.join(root_path, file_regex))

    def custom_search(algo, zs, dz, method):
        """
        Encuentra los puntos de cambio en la posición del agua a lo largo de la trayectoria.

        Parámetros:
        - algo: objeto de segmentación de ruptures.
        - zs: posiciones en z de la molécula de agua en la trayectoria.
        - dz: umbral de distancia para considerar un cambio en la posición.
        - method: método de búsqueda ("onebyone" o "direct").

        Salida:
        - Lista de puntos de cambio donde la posición del agua se considera estable.
        """
        order = max(max(algo.width, 2 * algo.min_size) // (2 * algo.jump), 1)
        peak_inds_shifted = argrelmax(algo.score, order=order, mode="wrap")[0]
        peak_inds_arr = np.take(algo.inds, peak_inds_shifted)
        peak_inds = [0] + list(peak_inds_arr) + [algo.n_samples]

        while True:
            avs = [zs[i:j].mean() for i, j in zip(peak_inds[:-1], peak_inds[1:])]
            davs = np.abs(np.array(avs[:-1]) - np.array(avs[1:]))

            if method == "onebyone":
                conditions = np.ones(len(peak_inds), dtype=bool)
                if len(davs) > 0 and np.min(davs) < dz:
                    conditions[np.argmin(davs) + 1] = False
            elif method == "direct":
                conditions = np.array([True] + list(davs > dz) + [True])
            else:
                print("Error: method must be 'onebyone' or 'direct'")
                return

            if all(conditions):
                break
            peak_inds = [peak for (peak, cond) in zip(peak_inds, conditions) if cond]

        return peak_inds[1:]

    # Definir los frames a analizar
    if first is None:
        first = 0
    if last is None:
        last = len(traj)
    
    dz *= 0.1  # Convertir de Ångstroms a nm

    # Obtener archivos de datos de agua en el canal
    files = get_filepaths_with_glob(".", regex)
    WATs_channels = []

    for fileWATs in files:
        iterWATs = np.load(fileWATs, allow_pickle=True)
        WATs_channels += list(iterWATs[first])  # Solo tomamos las aguas del primer frame

    WATs_channels = np.unique(np.array(WATs_channels))  # Eliminar duplicados

    stab_dicts = []
    for atom in WATs_channels:
        # Extraer posiciones en z de la molécula de agua en todos los frames analizados
        zs = np.array([traj.slice(step, copy=False).xyz[0][atom][2] for step in range(first, last)])

        # Aplicar segmentación para detectar cambios en la estabilidad de la posición
        algo = rpt.Window(width=width, model=model).fit(zs)
        bkps = custom_search(algo, zs, dz, method)  # Puntos de cambio en la estabilidad

        # Calcular la duración de los periodos estables
        intervals = [bkps[0]] + [bkps[i+1] - bkps[i] for i in range(len(bkps) - 1)]

        # Guardar la información en el diccionario
        stab_dicts.append({'index': atom, 'bkps': bkps, 'intervals': intervals})

    # Guardar los resultados en un archivo CSV
    stab_df = pd.DataFrame(stab_dicts)
    stab_df.to_csv(savefile)
