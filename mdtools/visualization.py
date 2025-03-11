### IMPORTS ###


from mdtools.core import *


### VISUALIZATION ###


def plot_CAs(p, traj, step):
    """
    Genera una visualización 3D de los átomos Cα en un frame específico de la trayectoria.

    Parámetros:
    - p: Objeto que contiene información sobre los Cα y su organización en tubos y capas.
    - traj: Trayectoria de la simulación.
    - step: Número de frame a visualizar.

    Salida:
    - Gráfica 3D con los Cα representados como puntos y líneas conectando los átomos en cada tubo.
    """
    
    # Extraer la posición de los átomos en el frame seleccionado
    frame = traj.slice(step, copy=False).xyz[0]

    # Crear la figura y el eje 3D
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')

    # Establecer las proporciones del gráfico para que la vista sea clara
    ax.set_box_aspect((15, 15, 30))  # Relación de aspecto personalizada

    # Dibujar los Cα como puntos grises
    for atom in p.CAs:
        xyz = frame[atom.index]
        ax.scatter(xyz[0], xyz[1], xyz[2], c='grey')

    # Dibujar las conexiones entre los átomos Cα en cada tubo y capa
    for tube in range(p.N_tubes):
        for ring in range(p.N_rings):
            # Obtener los índices de los átomos en el tubo y capa específicos
            atoms = [atom.index for atom in p.CAs if atom.tube == tube and atom.layer == ring]

            # Cerrar el anillo conectando el último átomo con el primero
            if atoms:
                atoms.append(atoms[0])

            # Dibujar las líneas de conexión entre los átomos
            for atom1, atom2 in zip(atoms[:-1], atoms[1:]):
                xyz1 = frame[atom1]
                xyz2 = frame[atom2]
                ax.plot3D([xyz1[0], xyz2[0]], [xyz1[1], xyz2[1]], [xyz1[2], xyz2[2]], 
                          color='grey', linewidth=1)

    # Mostrar el gráfico
    plt.show()


def plot_region(p, traj, step, CAs, WATfile=None, layer=0, delta_r=0.0, delta_z=0.0, offsets=None, lvsunits=False, wrap=False):
    """
    Genera una visualización 3D de una región específica de la trayectoria con los Cα y moléculas de agua.

    Parámetros:
    - p: Objeto que contiene información sobre los Cα y moléculas de agua.
    - traj: Trayectoria de la simulación.
    - step: Número de frame a visualizar.
    - CAs: Lista de átomos Cα a considerar.
    - WATfile: Archivo con las posiciones de las moléculas de agua (opcional).
    - layer: Capa central de la región a visualizar.
    - delta_r: Margen adicional en el radio de la región.
    - delta_z: Margen adicional en la altura de la región.
    - offsets: Lista de desplazamientos para representar la celda periódica.
    - lvsunits: Si es `True`, los desplazamientos se escalan con los vectores de la celda unitaria.
    - wrap: Si es `True`, aplica envoltura periódica a las posiciones de las moléculas de agua.
    
    Salida:
    - Gráfica 3D con la región destacada, los Cα y las moléculas de agua en rojo.
    """

    # Obtener las posiciones de los átomos en el frame seleccionado
    frame = traj.slice(step, copy=False).xyz[0]
    lvs = traj.slice(0, copy=False).unitcell_lengths[0]

    # Crear la figura y el eje 3D
    fig = plt.figure()
    ax = fig.add_subplot(projection='3d')
    ax.set_box_aspect((15, 15, 30))  # Proporciones del gráfico

    # Dibujar los Cα como puntos grises
    for atom in p.CAs:
        xyz = frame[atom.index]
        ax.scatter(xyz[0], xyz[1], xyz[2], c='grey')

    # Dibujar las conexiones entre los Cα en cada tubo y capa
    for tube in range(p.N_tubes):
        for ring in range(p.N_rings):
            atoms = [atom.index for atom in p.CAs if atom.tube == tube and atom.layer == ring]
            if atoms:
                atoms.append(atoms[0])  # Cerrar el anillo
                for atom1, atom2 in zip(atoms[:-1], atoms[1:]):
                    xyz1 = frame[atom1]
                    xyz2 = frame[atom2]
                    ax.plot3D([xyz1[0], xyz2[0]], [xyz1[1], xyz2[1]], [xyz1[2], xyz2[2]], 
                              color='grey', linewidth=1)

    # Obtener las posiciones de las moléculas de agua
    if WATfile is None:
        WATs = p.WATs  # Si no se proporciona un archivo, usar las moléculas de agua de p
    else:
        iterWATs = np.load(WATfile + ".npy", allow_pickle=True)
        WATs = iterWATs[step]

    # Dibujar las moléculas de agua en rojo
    for atom in WATs:
        xyz = wrap_coordinates(frame[atom], lvs) if wrap else frame[atom]
        ax.scatter(xyz[0], xyz[1], xyz[2], c='r')

    # Identificar los átomos en la capa superior e inferior
    atoms_top = get_indices_in_layer(CAs, layer)
    atoms_bot = get_indices_in_layer(CAs, p.N_rings - layer - 1)

    # Calcular el centro de la región
    centertop = np.mean(frame[atoms_top], axis=0)
    centerbot = np.mean(frame[atoms_bot], axis=0)
    center = (centertop + centerbot) / 2

    # Calcular el radio de la región
    rtop = np.max(distance_matrix(frame[atoms_top], frame[atoms_top])) / 2
    rbot = np.max(distance_matrix(frame[atoms_bot], frame[atoms_bot])) / 2
    r = max(rtop, rbot) + delta_r  # Ajustar con delta_r

    # Calcular las alturas máxima y mínima de la región
    zmax = np.mean(frame[atoms_top][:, 2]) - center[2] + delta_z
    zmin = np.mean(frame[atoms_bot][:, 2]) - center[2] - delta_z

    # Dibujar los cilindros que representan la región de interés
    if offsets is None:
        offsets = [np.array([0.0, 0.0, 0.0])]
    if not lvsunits:
        lvs = np.array([1.0, 1.0, 1.0])  # Si no se usan unidades de celda, se establece como 1

    for offset in offsets:
        z = np.linspace(zmin + center[2] + offset[2] * lvs[2], zmax + center[2] + offset[2] * lvs[2], 50)
        phi = np.linspace(0, 2 * np.pi, 50)
        phi_grid, z_grid = np.meshgrid(phi, z)
        x_grid = r * np.cos(phi_grid) + center[0] + offset[0] * lvs[0]
        y_grid = r * np.sin(phi_grid) + center[1] + offset[1] * lvs[1]
        ax.plot_surface(x_grid, y_grid, z_grid, color='g', alpha=0.5)  # Dibujar el cilindro semitransparente

    # Mostrar la gráfica
    plt.show()


def plot_network_3D(p, traj, step, label, reslist=[], ifpath=True, layer=0, xtalcenter=None, colordict=None):
    """
    This function plots a 3D network including water molecules, ions, hydrogen bonds, and paths at a specific time step.

    Parameters:
    - p: Simulation parameters.
    - traj: Trajectory object.
    - step: The specific step (time) for plotting.
    - label: The label for the data files (e.g., 'system_name').
    - reslist: List of residue names to highlight.
    - ifpath: If True, plot the longest paths.
    - layer: The layer for bondable atoms.
    - xtalcenter: The center of the crystal for wrapping coordinates.
    - colordict: A dictionary to map atom types to colors.
    
    Returns:
    - None: Displays a 3D plot.
    """
    
    # Load water and ion data
    iterWATs = np.load(f"iterWATs_{label}.npy", allow_pickle=True)
    iterIONs = np.load(f"iterIONs_{label}.npy", allow_pickle=True)

    # Load hydrogen bonds data
    hbonds = pd.read_csv(f"{label}_hbonds.csv")

    # Load path data if available
    if ifpath and os.path.isfile(f"{label}_longestpaths.csv"):
        paths = pd.read_csv(f"{label}_longestpaths.csv")
        paths['path'] = paths['path'].apply(lambda x: np.array([int(i) for i in x[1:-1].split(",")]))
    else:
        ifpath = False

    # Default color map if none is provided
    if colordict is None:
        colordict = {'HOH-O': "r", 'LYS-N': "b", 'LYN-N': "y", 'TFA-O': "m", 'TFA-F': "k"}

    # Extract the frame and unit cell dimensions for the current time step
    frame = traj.slice(step, copy=False).xyz[0]
    lvs = traj.slice(0, copy=False).unitcell_lengths[0]

    # Determine if wrapping should be applied
    xtal = xtalcenter is not None

    # Get water and ion atoms for the current step
    WATs = iterWATs[step]
    IONs = iterIONs[step]
    if ifpath:
        path = paths['path'].iloc[step]

    # Create the 3D plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    ax.set_box_aspect((15, 15, 30))  # Set aspect ratio for clarity

    # Plot water molecules
    for index in WATs:
        atom = traj.top.atom(index)
        key = f"{atom.residue.name}-{atom.element.symbol}"
        xyz = frame[index]
        if xtal:
            xyz = wrap_coordinates(xyz - xtalcenter * lvs, lvs)
        ax.scatter(xyz[0], xyz[1], xyz[2], c=colordict.get(key, 'r'), label=key)

    # Calculate and plot ions' centers of mass
    resids = [traj.top.atom(index).residue.index for index in IONs]
    coms = []
    for resid in set(resids):
        indices = [index for index, element in enumerate(resids) if element == resid]
        com = np.mean([frame[IONs[index]] for index in indices], axis=0)
        coms.append(com)
    for index in IONs:
        atom = traj.top.atom(index)
        key = f"{atom.residue.name}-{atom.element.symbol}"
        xyz = frame[index]
        if xtal:
            xyz = wrap_coordinates(xyz - xtalcenter * lvs, lvs)
        ax.scatter(xyz[0], xyz[1], xyz[2], c=colordict.get(key, 'k'))
        
        # Plot center of mass
        com = coms[list(set(resids)).index(traj.top.atom(index).residue.index)]
        if xtal:
            com = wrap_coordinates(com - xtalcenter * lvs, lvs)
        ax.plot3D([xyz[0], com[0]], [xyz[1], com[1]], [xyz[2], com[2]], color="grey", linestyle=":", linewidth=1)

    # Plot bondable atoms
    bondable_atoms = get_atoms_in_reslist(p.bondable, reslist)
    bondable = get_indices_between_layers(bondable_atoms, layer, p.N_rings - layer - 1)
    for index in bondable:
        atom = traj.top.atom(index)
        key = f"{atom.residue.name}-{atom.element.symbol}"
        xyz = frame[index]
        if xtal:
            xyz = wrap_coordinates(xyz - xtalcenter * lvs, lvs)
        ax.scatter(xyz[0], xyz[1], xyz[2], c=colordict.get(key, 'g'))

    # Plot hydrogen bonds
    for _, bond in hbonds[hbonds["step"] == step].iterrows():
        xyz1 = frame[MyAtom.from_string(bond["donor"]).index]
        if xtal:
            xyz1 = wrap_coordinates(xyz1 - xtalcenter * lvs, lvs)
        xyz2 = frame[MyAtom.from_string(bond["acceptor"]).index]
        if xtal:
            xyz2 = wrap_coordinates(xyz2 - xtalcenter * lvs, lvs)
        
        # Plot bond lines
        ax.plot3D([xyz1[0], xyz2[0]], [xyz1[1], xyz2[1]], [xyz1[2], xyz2[2]], color='k', linewidth=1)

    # Plot paths if available
    if ifpath:
        for i in range(len(path) - 1):
            xyz1 = frame[abs(path[i])]
            if xtal:
                xyz1 = wrap_coordinates(xyz1 - xtalcenter * lvs, lvs)
            xyz2 = frame[abs(path[i+1])]
            if xtal:
                xyz2 = wrap_coordinates(xyz2 - xtalcenter * lvs, lvs)
            ax.plot3D([xyz1[0], xyz2[0]], [xyz1[1], xyz2[1]], [xyz1[2], xyz2[2]], 'k--', linewidth=2.5)

    plt.show()


def plot_network_2D(p, traj, step, label, reslist=[], phimin=-4, ifpath=True, tube=0, layer=0, colordict=None):
    """
    Función para visualizar las interacciones de agua, iones y puentes de hidrógeno en un sistema de moléculas,
    representado en un gráfico polar en 2D.

    Parámetros:
    p (objeto): Objeto que contiene información de la simulación y los átomos de interés.
    traj (objeto): Trajectory object de MDTraj o similar.
    step (int): El paso de la simulación que se quiere visualizar.
    label (str): Etiqueta para leer los archivos correspondientes.
    reslist (list): Lista de residuos que se quieren visualizar.
    phimin (float): El valor mínimo del ángulo polar (en radianes).
    ifpath (bool): Si True, se dibujan las trayectorias entre átomos.
    tube (int): Si mayor que 0, se centra la visualización alrededor de un tubo.
    layer (int): Selección de capa de átomos a visualizar.
    colordict (dict): Diccionario para definir los colores de los átomos.

    Retorna:
    fig, ax: El objeto de la figura y el eje para personalizar el gráfico si es necesario.
    """
    
    # Cargar las moléculas de agua y iones para el paso actual
    iterWATs = np.load(f"iterWATs_{label}.npy", allow_pickle=True)
    iterIONs = np.load(f"iterIONs_{label}.npy", allow_pickle=True)

    # Cargar los puentes de hidrógeno
    hbonds = pd.read_csv(f"{label}_hbonds.csv")
    
    # Cargar las trayectorias si es necesario
    if ifpath and os.path.isfile(f"{label}_paths.csv"):
        paths = pd.read_csv(f"{label}_paths.csv")
        paths['path'] = paths['path'].apply(lambda x: np.array([int(i) for i in x[1:-1].split(",")]))
    else:
        ifpath = False  # Si no existe el archivo, no se dibujan las trayectorias

    # Obtener el marco del paso actual de la simulación
    frame = traj[step]

    # Moléculas de agua y iones en el paso actual
    WATs = iterWATs[step]
    IONs = iterIONs[step]

    # Cargar el camino si es necesario
    if ifpath:
        path = paths['path'].iloc[step]

    # Crear la figura y el eje de la visualización
    fig = plt.figure()
    ax = fig.add_subplot()

    # Obtener los átomos 'bondable' según la capa especificada
    bondable_atoms = get_atoms_in_reslist(p.bondable, reslist)
    bondable = get_indices_between_layers(bondable_atoms, layer, p.N_rings-layer-1)
        
    # Graficar los átomos 'bondable' en la visualización
    for index in bondable:
        atom = traj.top.atom(index)
        key = f"{atom.residue.name}-{atom.element}"
        xyz = frame[atom]
        phi = np.arctan2(xyz[1], xyz[0])  # Calcular el ángulo polar
        if phi < phimin:
            phi += 2 * np.pi  # Ajustar el ángulo a [0, 2π]
        ax.scatter(phi, xyz[2], c=colordict.get(key, 'gray'))  # Asignar color según el tipo de átomo
    
    # Centro de la visualización si se está utilizando un tubo
    center = np.array([0.0, 0.0, 0.0])
    if tube > 0:
        # Calcular el centro de la visualización en función de los átomos en el tubo
        atoms_center = p.CAs[int((tube-1)*p.CAs.size/p.N_tubes):int(tube*p.CAs.size/p.N_tubes)]
        center = np.sum(frame[atoms_center], axis=0) / len(atoms_center)
    
    # Graficar las moléculas de agua (en rojo) en la visualización
    for atom in WATs:
        xyz = frame[atom]
        if tube > 0:
            xyz -= center  # Centrar la visualización si es un tubo
        phi = np.arctan2(xyz[1], xyz[0])
        if phi < phimin:
            phi += 2 * np.pi
        ax.scatter(phi, xyz[2], c='r')

    # Graficar los iones (en negro) en la visualización
    for atom in IONs:
        xyz = frame[atom]
        phi = np.arctan2(xyz[1], xyz[0])
        if phi < phimin:
            phi += 2 * np.pi
        ax.scatter(phi, xyz[2], c='k')

    # Graficar los puentes de hidrógeno
    xmin, xmax, ymin, ymax = 999, -999, 999, -999
    for index, bond in hbonds[hbonds["istep"] == step].iterrows():
        # Coordenadas de los átomos donadores y aceptores
        xyzd = frame[bond["donor"]]
        if tube > 0:
            xyzd -= center
        phid = np.arctan2(xyzd[1], xyzd[0])
        if phid < phimin:
            phid += 2 * np.pi
        
        xyza = frame[bond["acceptor"]]
        if tube > 0:
            xyza -= center
        phia = np.arctan2(xyza[1], xyza[0])
        if phia < phimin:
            phia += 2 * np.pi
        
        # Dibujar flechas para los puentes de hidrógeno, considerando el caso de ángulos mayores a pi
        if np.abs(phia - phid) > np.pi:
            ax.annotate("", xy=(phid, xyzd[2]), xytext=(phia-2*np.pi, xyza[2]), arrowprops=dict(arrowstyle="<|-", lw=1.2, fc='y'))
            ax.annotate("", xy=(phid+2*np.pi, xyzd[2]), xytext=(phia, xyza[2]), arrowprops=dict(arrowstyle="<|-", lw=1.2, fc='y'))
            xmin, xmax = min(xmin, phia-2*np.pi), max(xmax, phid+2*np.pi)
        elif np.abs(phid - phia) > np.pi:
            ax.annotate("", xy=(phid, xyzd[2]), xytext=(phia+2*np.pi, xyza[2]), arrowprops=dict(arrowstyle="<|-", lw=1.2, fc='y'))
            ax.annotate("", xy=(phid-2*np.pi, xyzd[2]), xytext=(phia, xyza[2]), arrowprops=dict(arrowstyle="<|-", lw=1.2, fc='y'))
            xmin, xmax = min(xmin, phid-2*np.pi), max(xmax, phia+2*np.pi)
        else:
            ax.annotate("", xy=(phid, xyzd[2]), xytext=(phia, xyza[2]), arrowprops=dict(arrowstyle="<|-", lw=1.2, fc='y'))
            xmin, xmax = min(xmin, phid, phia), max(xmax, phid, phia)
            ymin, ymax = min(ymin, xyzd[2], xyza[2]), max(ymax, xyzd[2], xyza[2])

    # Graficar las trayectorias si es necesario
    if ifpath:
        for i in range(len(path)-1):
            # Graficar trayectorias entre átomos
            xyz1 = frame[path[i]]
            if tube > 0:
                xyz1 -= center
            phi1 = np.arctan2(xyz1[1], xyz1[0])
            if phi1 < phimin:
                phi1 += 2 * np.pi
            xyz2 = frame[path[i+1]]
            if tube > 0:
                xyz2 -= center
            phi2 = np.arctan2(xyz2[1], xyz2[0])
            if phi2 < phimin:
                phi2 += 2 * np.pi
            
            # Dibujar líneas entre los átomos
            if np.abs(phi1 - phi2) > np.pi:
                ax.plot([phi1, phi2+2*np.pi], [xyz1[2], xyz2[2]], 'k--', linewidth=2.5)
                ax.plot([phi1-2*np.pi, phi2], [xyz1[2], xyz2[2]], 'k--', linewidth=2.5)
            elif np.abs(phi2 - phi1) > np.pi:
                ax.plot([phi1, phi2-2*np.pi], [xyz1[2], xyz2[2]], 'k--', linewidth=2.5)
                ax.plot([phi1+2*np.pi, phi2], [xyz1[2], xyz2[2]], 'k--', linewidth=2.5)
            else:
                ax.plot([phi1, phi2], [xyz1[2], xyz2[2]], 'k--', linewidth=2.5)

    # Configuración de los ejes y etiquetas
    xticks = np.arange(-2 * np.pi, 2.1 * np.pi, 0.5 * np.pi)
    xlabels = ["-2$\pi$", "-1.5$\pi$", "-$\pi$", "-0.5$\pi$", "0", "$0.5\pi$", "$\pi$", "$1.5\pi$", "2$\pi$"]
    plt.xticks(xticks, xlabels)
    plt.xlim(xmin-0.01, xmax+0.01)
    plt.ylim(ymin-0.01, ymax+0.01)
    ax.set_xlabel("Ángulo polar $\Phi$ (rad)")
    ax.set_ylabel("z ($\AA$)")
    
    return fig, ax  # Retornar la figura y los ejes para personalización si es necesario


def compute_xyz(p, traj, atoms, iterate, first, last, tube=0):
    """
    Calcula las coordenadas (xyz) de los átomos en una región de la trayectoria.

    Parámetros:
    - p: Objeto que contiene información sobre los Cα y otros atributos.
    - traj: Trayectoria de la simulación.
    - atoms: Lista de átomos cuyos valores de coordenadas se desean calcular.
    - iterate: Si es `True`, los átomos a considerar varían en cada paso de la simulación.
    - first: Paso inicial de la simulación para el cálculo.
    - last: Paso final de la simulación para el cálculo.
    - tube: Si es mayor que 0, realiza una corrección de las coordenadas con respecto al centro de un tubo específico.
    
    Retorna:
    - `xyz`: Un array con las coordenadas de los átomos a lo largo de la simulación.
    """

    # Inicializar el array para almacenar las coordenadas
    xyz = np.array([]).reshape(0, 3)

    # Si 'iterate' es True, los átomos cambian en cada paso de la simulación
    if iterate:
        aux = atoms  # Se guarda la lista de átomos, ya que cambiará a lo largo de la simulación

    # Iterar sobre cada paso de la simulación (desde 'first' hasta 'last')
    for step in range(first, last):
        # Obtener las coordenadas del frame actual en la trayectoria
        frame = traj[step]
        
        # Si 'iterate' es True, cambiar la lista de átomos en función del paso actual
        if iterate:
            atoms = aux[step]
        
        # Iterar sobre los átomos seleccionados en el paso actual
        for atom in atoms:
            # Obtener las coordenadas del átomo en el frame actual
            coords = frame[atom]
            
            # Si tube > 0, aplicar una corrección de las coordenadas con respecto al centro del tubo
            if tube > 0:
                # Obtener los átomos de la capa correspondiente al tubo
                atoms_center = p.CAs[int((tube - 1) * p.CAs.size / p.N_tubes):int(tube * p.CAs.size / p.N_tubes)]
                # Calcular el centro de los átomos del tubo
                center = np.sum(frame[atoms_center], axis=0) / atoms_center.size
                # Corregir las coordenadas del átomo restando el centro del tubo
                coords = coords - center
            
            # Apilar las coordenadas del átomo en el array 'xyz'
            xyz = np.vstack((xyz, coords))
    
    return xyz


def compute_density_profile(xyz, Nbins, axs, color, name):
    """
    Calcula y visualiza el perfil de densidad de las coordenadas en función de las coordenadas
    polares (r, phi) y la componente z para un conjunto de átomos.

    Parámetros:
    - xyz: Array de coordenadas de los átomos en 3D, donde cada fila es [x, y, z].
    - Nbins: Número de bins para los histogramas.
    - axs: Una lista de tres ejes (ax1, ax2, ax3) donde se trazan los histogramas.
    - color: El color que se utilizará para los histogramas.
    - name: El nombre o etiqueta que se usará para la leyenda.
    
    El método crea tres histogramas:
    1. Densidad en función del ángulo azimutal (phi) en el plano XY.
    2. Densidad en función de la distancia radial (r) desde el origen en el plano XY.
    3. Densidad en función de la altura (z) a lo largo del eje Z.
    """
    
    # Extraer las coordenadas X, Y, Z
    xs = xyz[:, 0]
    ys = xyz[:, 1]
    zs = xyz[:, 2]

    # Calcular el ángulo azimutal (phi) y la distancia radial (r)
    phis = np.arctan2(ys, xs)  # Ángulo azimutal en el plano XY
    rs = np.sqrt(xs**2 + ys**2)  # Distancia radial desde el origen en el plano XY
    
    # Calcular los histogramas
    # Histograma de phi (ángulo azimutal)
    hist, bin_edges = np.histogram(phis, bins=Nbins)
    axs[0].plot((bin_edges[1:] + bin_edges[:-1]) / 2, hist, color=color, label=name)

    # Histograma de r (distancia radial)
    hist, bin_edges = np.histogram(rs, bins=Nbins)
    axs[1].plot((bin_edges[1:] + bin_edges[:-1]) / 2, hist, color=color, label=name)

    # Histograma de z (componente Z)
    hist, bin_edges = np.histogram(zs, bins=Nbins)
    axs[2].plot((bin_edges[1:] + bin_edges[:-1]) / 2, hist, color=color, label=name)


def plot_density_profiles(p, traj, label, first, last, canal=True, tube=0, Nbins=100, layer=0, KY=False):
    """
    Calcula y visualiza los perfiles de densidad de diferentes tipos de átomos (agua, cloro, residuos de proteínas)
    en función de sus coordenadas en el espacio en tres dimensiones (azimutal, radial y a lo largo del eje z).
    
    Parámetros:
    - p: Objeto que contiene la información de los átomos, como las posiciones de los átomos de agua y proteínas.
    - traj: Trajectory de simulación con las coordenadas atómicas a través de los pasos de tiempo.
    - label: Etiqueta para el archivo de entrada (utilizado para cargar los datos de átomos específicos).
    - first: Primer paso de tiempo a considerar.
    - last: Último paso de tiempo a considerar.
    - canal: Booleano que indica si se deben incluir los canales de cloro.
    - tube: Índice del tubo (si se utiliza una estructura de tubos).
    - Nbins: Número de bins para los histogramas.
    - layer: Capa de la proteína a considerar.
    - KY: Booleano que indica si se deben incluir los átomos de un tipo específico de residuos (por ejemplo, tirosina).

    Devuelve:
    - fig: Figura generada con los perfiles de densidad.
    - axs: Ejes donde se trazaron los histogramas de densidad.
    """
    
    # Cargar los átomos de agua del canal de la simulación
    iWATs_canal = np.load("iWATs_" + label + ".npy", allow_pickle=True)
    WATs_xyz = compute_xyz(p, traj, iWATs_canal, True, first, last, tube)  # Coordenadas de las moléculas de agua

    # Si canal es True, cargar los átomos de cloro y otras moléculas relacionadas
    if canal:
        iCLs_canal = np.load("iCLs_" + label + ".npy", allow_pickle=True)
        CLs_xyz = compute_xyz(p, traj, iCLs_canal, True, first, last, tube)  # Coordenadas de los átomos de cloro
        NZs_LYS, NZs_LYN = select_atoms(p, layer)  # Átomos de residuos en la capa especificada
        NZs_LYN_xyz = compute_xyz(p, traj, NZs_LYN, False, first, last, tube)  # Coordenadas de residuos LYN
        NZs_LYS_xyz = compute_xyz(p, traj, NZs_LYS, False, first, last, tube)  # Coordenadas de residuos LYS
        
        # Si KY es True, incluir átomos de TYD
        if KY:
            TYDs = select_atoms(p, layer, KY)  # Selección de átomos TYD
            TYDs_xyz = compute_xyz(p, traj, TYDs, False, first, last, tube)  # Coordenadas de los átomos TYD

    # Crear una figura con tres subgráficos (uno para cada dimensión: phi, r y z)
    fig, axs = plt.subplots(3, 1, figsize=(8, 12))

    # Calcular y trazar el perfil de densidad de las moléculas de agua
    compute_density_profile(WATs_xyz, Nbins, axs, 'r', "WAT(O)")
    
    # Si canal es True, trazar los perfiles de densidad de los átomos de cloro y residuos
    if canal:
        compute_density_profile(CLs_xyz, Nbins, axs, 'k', "Cl")  # Cloro
        compute_density_profile(NZs_LYN_xyz, Nbins, axs, 'y', "LYN(NZ)")  # Residuos LYN
        compute_density_profile(NZs_LYS_xyz, Nbins, axs, 'b', "LYS(NZ)")  # Residuos LYS
        if KY:
            compute_density_profile(TYDs_xyz, Nbins, axs, 'm', "TYD(O)")  # Residuos TYD

    # Etiquetas y leyendas
    axs[0].set_xlabel("$\phi (rad)$")  # Ángulo azimutal
    axs[1].set_xlabel("$r (\AA)$")    # Distancia radial
    axs[2].set_xlabel("$z (\AA)$")    # Altura en el eje z
    axs[0].legend(edgecolor='0.75')  # Leyenda para el gráfico de phi
    axs[1].legend(edgecolor='0.75')  # Leyenda para el gráfico de r
    axs[2].legend(edgecolor='0.75')  # Leyenda para el gráfico de z

    # Devolver la figura y los ejes
    return fig, axs


def plot_water_stability(traj, file="water_stability.csv", index=None, figsize=(12, 6)):
    """
    Visualiza la estabilidad del agua en un canal a lo largo de los pasos de simulación, 
    mostrando su posición en el eje z y los puntos de cambio detectados.

    Parámetros:
    - traj: Objeto de simulación (con información de los pasos de tiempo y las coordenadas).
    - file: Archivo CSV con información de estabilidad de agua.
    - index: Índice del átomo de agua para analizar. Si es None, se selecciona aleatoriamente uno del archivo.
    - figsize: Tamaño de la figura (ancho, alto).

    Devuelve:
    - fig: Figura generada.
    - axs: Ejes del gráfico.
    - index: Índice seleccionado.
    """
    
    # Leer el archivo CSV con las posiciones y puntos de cambio
    stab_df = pd.read_csv(file)

    # Obtener todos los índices de agua en el archivo
    indices = stab_df['index'].tolist()
    
    # Seleccionar un índice aleatorio si no se proporciona uno específico
    if index is None:
        index = indices[np.random.randint(len(indices))]
    else:
        if index not in indices:
            print("Error: index not present in file")
            return

    # Extraer los puntos de cambio de la fila correspondiente al índice
    row = stab_df[stab_df['index'] == index]
    field = row['bkps']
    data = field.iloc[0]  # Asegurarse de obtener el primer valor de la serie
    bkps = [0] + json.loads(data)  # Los puntos de cambio (breakpoints)

    # Extraer la serie de posiciones z del átomo de agua a través de todos los pasos
    zs = np.array([traj.slice(step, copy=False).xyz[0][index][2] for step in range(len(traj))])

    # Calcular el promedio móvil (rolling average) para suavizar los datos
    window_size = 100  # Tamaño de la ventana para el promedio móvil
    zseries = pd.Series(zs)
    rolling_averages = zseries.rolling(window_size, center=True).mean()
    zra = np.array(rolling_averages.tolist())

    # Crear la figura y los ejes para graficar
    fig, axs = plt.subplots(figsize=figsize)

    # Graficar la serie original de posiciones z
    axs.plot(zs, label="Posición z (sin suavizar)", color='b', alpha=0.6)

    # Graficar las medias móviles
    axs.plot(zra, 'r', lw=3, label="Promedio móvil (rolling average)")

    # Graficar los puntos de cambio (breakpoints)
    for ibkp in range(len(bkps)-1):
        i = bkps[ibkp]
        j = bkps[ibkp+1]
        axs.plot([i, j], [zs[i:j].mean(), zs[i:j].mean()], 'k--', lw=3)

    # Ajustes finales del gráfico
    axs.set_xlim([bkps[0], bkps[-1]])
    axs.set_title(f"Estabilidad del agua en canal - Índice = {index}")
    axs.set_xlabel("Paso de tiempo")
    axs.set_ylabel("Posición z (nm)")
    axs.legend()

    # Devolver la figura, los ejes y el índice seleccionado
    return fig, axs, index
