import geopandas as gpd
from rasterstats import zonal_stats
import matplotlib.pyplot as plt
from matplotlib.colors import BoundaryNorm, ListedColormap
import os
from matplotlib.offsetbox import OffsetImage, AnnotationBbox
from PIL import Image

def calcular_estatistica_por_municipio(raster_path, municipios_shapefile, estatistica="max"):
    # Carregar o shapefile de municípios
    municipios = gpd.read_file(municipios_shapefile).to_crs(epsg=4326)

    # Calcular a estatística de precipitação por município usando zonal_stats
    stats = zonal_stats(municipios, raster_path, stats=[estatistica], geojson_out=True)
    
    # Transformar o resultado em um GeoDataFrame
    municipios_stats = gpd.GeoDataFrame.from_features(stats)
    
    # Renomear a coluna para refletir a estatística escolhida
    municipios_stats = municipios_stats.rename(columns={estatistica: f"{estatistica}_precipitation"})
    
    return municipios_stats

def plotar_mapa_por_municipio(municipios_stats, titulo):

    sp_border = gpd.read_file('/content/drive/MyDrive/dados/mun/DIV_MUN_SP_2021a.shp').to_crs(epsg=4326)
    minx, miny, maxx, maxy = sp_border.total_bounds

    # Definir os limites e o cmap para o colorbar
    bounds = [0, 2, 3, 5, 7, 10, 15, 20, 25, 30, 40, 50, 75, 100]
    cmap = ListedColormap([
        "#ffffff00", "#0080aabf", "#0000B3", "#80FF55", "#00CC7F",
        "#558000", "#005500", "#FFFF00", "#FFCC00", "#FF9900",
        "#D55500", "#FFBBFF", "#FF2B80", "#8000AA"
    ])
    norm = BoundaryNorm(bounds, cmap.N)

    # Plotar o mapa dos municípios com a estatística de precipitação
    fig, ax = plt.subplots(figsize=(18, 12))
    ax.set_xlim(minx, maxx)
    ax.set_ylim(miny, maxy)

    # Identificar o nome da coluna da estatística
    estatistica_coluna = [col for col in municipios_stats.columns if "_precipitation" in col][0]

    municipios_stats.plot(
        column=estatistica_coluna,
        cmap=cmap,
        linewidth=0.3,
        edgecolor="black",
        legend=False,
        ax=ax, 
        norm=norm
    )

    # Adicionar o colorbar manualmente
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = fig.colorbar(sm, ax=ax, orientation="horizontal", label="Precipitação (mm)", shrink=0.75, pad=0.05, extend='max')
    cbar.set_ticks(bounds)
    cbar.set_ticklabels([str(b) for b in bounds])

    ax.set_title(titulo, fontsize=16)
    ax.grid(which='both', linestyle='-', linewidth=0.5, color='gray', alpha=0.6)
    ax.tick_params(axis='both', which='major', labelsize=8)
    logo_path = "/content/drive/MyDrive/logo/logo_spaguas.png"

    if os.path.exists(logo_path):
        logo = Image.open(logo_path)
        imagebox = OffsetImage(logo, zoom=0.2)
        ab = AnnotationBbox(
            imagebox,
            (0.91, 0.91),
            xycoords='axes fraction',
            frameon=True,
            bboxprops=dict(facecolor="white", edgecolor="none")
        )
        ax.add_artist(ab)
    else:
        print("Aviso: O logo não foi encontrado e não será exibido.")

    annotation_text = (
        "Elaborado pela equipe técnica da Sala de Situação São Paulo (SSSP).\n"
        "Interpolação dos pluviômetros a partir do método IDW."
    )

    ax.annotate(
        annotation_text, xy=(0.02, 0.02), xycoords='axes fraction',
        fontsize=8, ha='left', va='bottom',
        bbox=dict(facecolor='white', alpha=0.7, edgecolor='white')
    )

    plt.savefig(titulo, dpi=300, bbox_inches="tight")
    plt.show()

# Caminhos para o raster e shapefile dos municípios
cropped_raster = "output_idw_cropped.tif"
municipios_shapefile = '/content/drive/MyDrive/dados/mun/DIV_MUN_SP_2021a.shp'

# Solicitar a escolha da estatística ao usuário
estatistica_desejada = input("Escolha a estatística para o cálculo de precipitação (max, mean, median): ").strip().lower()
while estatistica_desejada not in ["max", "mean", "median"]:
    print("Opção inválida. Escolha entre 'max', 'mean' ou 'median'.")
    estatistica_desejada = input("Escolha a estatística para o cálculo de precipitação (max, mean, median): ").strip().lower()

# Calcular a estatística de precipitação por município
municipios_stats = calcular_estatistica_por_municipio(cropped_raster, municipios_shapefile, estatistica=estatistica_desejada)

hoje = datetime.now()
hoje_format = hoje.strftime('%Y-%m-%d')

ontem = hoje - timedelta(days=1)
ontem_format = ontem.strftime('%Y-%m-%d')



# Plotar o mapa da estatística de precipitação por município
titulo_mapa = f"Acumulado de chuvas 24H por Município\n07:00h de {ontem_format} às 07:00h de {hoje_format}"
plotar_mapa_por_municipio(municipios_stats, titulo_mapa)
