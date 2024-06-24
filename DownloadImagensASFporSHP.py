#DownloadImagensASFporSHP
#_________________________________________________________________________________________
# Rotina para buscar imagens de setélite na plataforma ASF ao longo do tempo em um local 
# determinado por um shapefile 
#Abre e lê arquivo shp> Transforma as coords em WKT> Faz a busca no ASF com os parametros 
#determinados> Salva a busca em um arquivo .csv> Autentica as credenciais do ASF para o 
#download dos arquivos> Realiza o download da pesquisa.
#_________________________________________________________________________________________
# MIT License
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#__________________________________________________________________________________________
# Author: Maria Paula Graziotto
# Github: Graziottomp
# Email: graziotto.mp@outlook.com
# Created: 2024-06-20
#__________________________________________________________________________________________


#Bibliotecas
import os
from pathlib import Path    #Acessa os diretórios do computador
import asf_search as asf    #Acessa a plataforma ASF
import getpass              #Recebe e verifica as credeenciais para acesso aos dados
import glob                 #Percorre a lista de arquivos no diretório
import geopandas as gpd     #Para ler e processar o arquivo .shp
import shapely.geometry     #Manipulação dos polígonos
import csv                  #Cria, abre e manipula arquivos .csv

#Cria ou confere se existe o diretório que será salvo as imagens
def create_directories(dirs):
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

#Abre os arquivos .shp e extrai as coordenadas do polígonos
def read_shapefiles(shapefile_directory):
    shapefiles = glob.glob(os.path.join(shapefile_directory, '*.shp'))
    polygons = []
    for shp_file in shapefiles:
        gdf = gpd.read_file(shp_file)
        for _, row in gdf.iterrows():
            polygons.append(row.geometry)
    return polygons

#Transforma as coordenadas dos polígonos em WTK para criar a Area Of Interest
def get_wkt_from_polygons(polygons):
    wkt_list = [polygon.wkt for polygon in polygons]
    return wkt_list

#Armazena o resultado da busca feita no ASF em um .csv para ter o catálogo de imagens 

def save_results_to_csv(results, filename):
    with open(filename, "w") as f:
        f.writelines(results.csv())
    print(*results.csv(), sep='')


#Função que define aonde e o que será feito
def main():
    # Definição dos diretórios
    dirs = "caminho para o arquivo"
    shp_dir = "caminho para o arquivo"

    # Leitura dos arquivos shapefile e criação da Área de Interesse (AOI)
    polygons = read_shapefiles(shp_dir)
    if not polygons:
        print("Nenhum shapefile encontrado.")
        return

    wkt_list = get_wkt_from_polygons(polygons)
    if not wkt_list:
        print("Nenhum polígono válido encontrado.")
        return

    aoi = wkt_list[0]  # Exemplo: usa o primeiro polígono da lista

    # Parâmetros da pesquisa, trocar conforme a necessidade
    search_opts = {
        'platform': asf.PLATFORM.SENTINEL1,  
        'beamMode': asf.BEAMMODE.IW,
        'polarization': asf.POLARIZATION.VV, 
        'start': '2024-01-01T00:00:00Z',
        'end': '2024-06-20T23:59:59Z'
    }

    # Executa a pesquisa e obtém os resultados
    results = asf.geo_search(intersectsWith=aoi, **search_opts)
    print(f'{len(results)} resultados encontrados')
    print(results)

    # Salva os resultados em um arquivo CSV, pode trocar o nome "search_results.csv"
    save_results_to_csv(results, "search_results.csv")

    # Pergunta ao usuário se deseja continuar com o download das imagens
    proceed = input("Deseja continuar com o download das imagens? (s/n): ")
    if proceed.lower() != 's':
        print("Download cancelado pelo usuário.")
        return
    
    # Autenticação - digite sua autenticação 
    username = input('Username:')
    password = getpass.getpass('Password:')

    try:
        session = asf.ASFSession().auth_with_creds(username, password)
    except asf.ASFAuthenticationError as e:
        print(f'Falha na autenticação: {e}')
        return
    else:
        print('Autenticação bem-sucedida!')

    # Realiza o download das imagens
    results.download(path=dirs[0], session=session, processes=50)


if __name__ == "__main__":
    main()
