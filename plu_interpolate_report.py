import requests
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.colors import Normalize, ListedColormap, BoundaryNorm
from datetime import datetime, timedelta
import geopandas as gpd
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

# Perguntar ao usuário uma vez se deseja excluir alguma estação por prefixo
excluir_prefixos = input(
    "Digite os prefixos das estações a serem excluídas (separados por vírgula), ou pressione Enter para continuar: "
).strip()
excluir_prefixos = [prefix.strip() for prefix in excluir_prefixos.split(",")] if excluir_prefixos else []

# Função para carregar e processar os dados de cada URL
def gerar_mapa_chuva(url, titulo, excluir_prefixos):
    # Carregando a fronteira do estado de São Paulo
    sp_border = gpd.read_file('/content/drive/MyDrive/dados/mun/DIV_MUN_SP_2021a.shp')
    sp_border = sp_border.to_crs(epsg=4326)

    # Obtendo os limites do estado de São Paulo
    minx, miny, maxx, maxy = sp_border.total_bounds

    # Obtendo os dados da API
    response = requests.get(url)
    data = response.json()

    # Extraindo as coordenadas e valores
    stations = [
        (item["prefix"], float(item["latitude"]), float(item["longitude"]), item["value"])
        for item in data["json"]
        if item["latitude"] is not None and
           item["longitude"] is not None and
           item["value"] is not None
    ]

    # Filtrando estações
    filtered_stations = [
        (lat, lon, value)
        for prefix, lat, lon, value in stations
        if prefix not in excluir_prefixos
    ]

    if not filtered_stations:
        print("Erro: Não há dados válidos para interpolação após a exclusão.")
        return

    # Separando latitudes, longitudes e valores
    lats, longs, values = zip(*filtered_stations)

    # Função para IDW
    def idw(x, y, z, xi, yi, power=2, epsilon=1e-10):
        dist = np.sqrt((x[:, None] - xi[None, :])**2 + (y[:, None] - yi[None, :])**2)
        dist[dist < epsilon] = epsilon
        weights = 1 / dist**power
        weights /= weights.sum(axis=0)
        zi = np.dot(weights.T, z)
        return zi

    # Criando a grade para interpolação
    grid_x, grid_y = np.meshgrid(
        np.linspace(minx, maxx, 500),
        np.linspace(miny, maxy, 500)
    )

    lats = np.array(lats)
    longs = np.array(longs)
    values = np.array(values)

    # Interpolação usando IDW
    grid_z = idw(longs, lats, values, grid_x.ravel(), grid_y.ravel())
    grid_z = grid_z.reshape(grid_x.shape)

    # Definindo colormap e intervalos
    cmap = ListedColormap([
        "#ffffff00",
        "#0080AA",
        "#0000B3",
        "#00CC7F",
        "#558000", 
        "#005500",
        "#FFFF00",
        "#FFCC00",
        "#FF9900",
        "#D55500",
        "#FFBBFF",
        "#FF2B80",
        "#8000AA"

    ])

    bounds = [0, 2, 3, 5, 7, 10, 15, 20, 25,  30, 40,  50, 75, 100]
    norm = BoundaryNorm(bounds, cmap.N)

    # Criando a figura
    fig, ax = plt.subplots(figsize=(15, 10))

    # Plotando a fronteira do estado de São Paulo
    sp_border.plot(ax=ax, edgecolor='black', facecolor='none', linewidth=0.3)

    # Plotando o mapa interpolado
    c = ax.imshow(
        grid_z,
        extent=(minx, maxx, miny, maxy),
        origin='lower', cmap=cmap, aspect='auto',
        norm=norm
    )

    # Barra de cores
    cbar = plt.colorbar(c, ax=ax, ticks=bounds, spacing='uniform', shrink=0.8)
    cbar.set_label('mm', fontsize=8)

    # Configurando título e limites dos eixos
    date = (datetime.now() - timedelta(hours=3)).strftime('%d/%m/%Y %H:%M')
    ax.set_title(f'{titulo}\n{date}', fontsize=14)
    ax.grid(which='both', linestyle='--', linewidth=0.5, color='gray', alpha=0.6)
    ax.tick_params(axis='both', which='major', labelsize=8)
    ax.set_xlim([minx, maxx])
    ax.set_ylim([miny, maxy])

    # Carregando o logotipo
    logo_path = "/content/drive/MyDrive/logo/logo_spaguas.png"
    logo = Image.open(logo_path)

    # Adicionando o logotipo no gráfico
    imagebox = OffsetImage(logo, zoom=0.2)
    ab = AnnotationBbox(
        imagebox, (0.91, 0.92),
        xycoords='axes fraction',
        frameon=True,
        bboxprops=dict(facecolor='white', edgecolor='none')
    )
    ax.add_artist(ab)

    # Anotação no canto inferior esquerdo
    annotation_text = (
        "Elaborado pela equipe técnica da Sala de Situação São Paulo (SSSP).\n"
        "Interpolação dos pluviômetros a partir do método IDW."
    )
    ax.annotate(
        annotation_text,
        xy=(0.01, 0.01),
        xycoords='axes fraction',
        fontsize=8, ha='left', va='bottom',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='white')
    )

    # Mostrar o gráfico
    plt.show()

# URLs e títulos para diferentes intervalos
intervalos = [
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=1&show_all=true", "ACUMULADO DE CHUVAS DA ÚLTIMA 1H"),
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=2&show_all=true", "ACUMULADO DE CHUVAS DAS ÚLTIMAS 2H"),
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=3&show_all=true", "ACUMULADO DE CHUVAS DAS ÚLTIMAS 3H"),
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=12&show_all=true", "ACUMULADO DE CHUVAS DAS ÚLTIMAS 12H"),
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=24&show_all=true", "ACUMULADO DE CHUVAS DAS ÚLTIMAS 24H"),
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=48&show_all=true", "ACUMULADO DE CHUVAS DAS ÚLTIMAS 48H"),
    ("https://cth.daee.sp.gov.br/sibh/api/v1/measurements/last_hours_events?hours=72&show_all=true", "ACUMULADO DE CHUVAS DAS ÚLTIMAS 72H")
]

# Gerando mapas para cada intervalo
for url, titulo in intervalos:
    gerar_mapa_chuva(url, titulo, excluir_prefixos)
