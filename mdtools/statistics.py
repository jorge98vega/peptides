### IMPORTS ###


from mdtools.core import *


### STATISTICS ###


def N_hist(data, x=None, bins='auto', hue=None, element='bars', alpha=1, title=None, xlabel=None):
    '''
    Genera un histograma con seaborn, útil para visualizar la distribución de una variable.
    
    data: DataFrame con los datos.
    x: Nombre de la columna a graficar.
    bins: Número de bins ('auto' por defecto, 'int' para valores enteros).
    hue: Agrupación de datos por colores.
    element: Tipo de representación ('bars', 'step', etc.).
    alpha: Transparencia de las barras.
    title: Título del gráfico.
    xlabel: Etiqueta del eje X.
    '''
    N_data = data[x]
    if bins == 'int':
        bins = np.arange(min(N_data) - 0.5, max(N_data) + 1, 1)

    fig, ax = plt.subplots()
    sns.histplot(data=data, x=x, hue=hue, bins=bins, lw=2, element=element, alpha=alpha)
    ylabel = 'Count (number of frames)'
    decorate_ax(ax, title, 16, xlabel, ylabel, 14, 12, 2, 4, False)


def evolution(data, x=None, y=None, hue=None, label=None, title=None, ylabel=None):
    '''
    Grafica la evolución de una variable en función del tiempo o pasos de simulación.
    
    data: DataFrame con los datos.
    x: Nombre de la columna para el eje X.
    y: Nombre de la columna para el eje Y.
    hue: Agrupación de datos por colores.
    label: Etiqueta opcional para la leyenda.
    title: Título del gráfico.
    ylabel: Etiqueta del eje Y.
    '''
    fig, ax = plt.subplots()
    sns.lineplot(data=data, x=x, y=y, hue=hue)
    xlabel = 'Step'
    decorate_ax(ax, title, 16, xlabel, ylabel, 14, 12, 2, 4, False)


def stability_hist(df, nbins=100, color='b', label=None, fig=None, ax=None):
    '''
    Genera un histograma a partir de intervalos almacenados en un DataFrame.
    
    df: DataFrame con una columna 'intervals' que contiene listas de valores en formato JSON.
    nbins: Número de bins para el histograma.
    color: Color del histograma.
    label: Etiqueta opcional para la leyenda.
    fig, ax: Opcionales, para dibujar sobre una figura existente.
    
    Devuelve:
    - fig: Figura del gráfico.
    - ax: Ejes del gráfico.
    - data: Datos extraídos de la columna 'intervals'.
    - h: Histograma generado.
    '''
    data = []
    for index, row in df.iterrows():
        data += json.loads(row['intervals'])  # Extrae los intervalos de la columna 'intervals'

    if fig is None and ax is None:
        fig, ax = plt.subplots(figsize=(12, 8))

    # Histograma con contorno
    ax.hist(data, nbins, color=color, histtype='step')
    # Histograma con relleno semitransparente
    h = ax.hist(data, nbins, color=color, alpha=0.5, label=label)
    # Línea discontinua en la media de los datos
    ax.plot([np.array(data).mean(), np.array(data).mean()], [0, np.max(h[0])], color=color, ls='--', lw=2)

    return fig, ax, data, h
