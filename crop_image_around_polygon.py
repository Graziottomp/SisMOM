#Substitui o valor dos pixels dentro de cada poligonos por NaN e deixa o valor dos pixels
#ao redor deles intacto 
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


import os
import glob
import geopandas as gpd
import rasterio
from rasterio import mask
from rasterio.features import geometry_mask
from shapely.geometry import box
import numpy as np

def crop_image_around_polygon(image_file, polygon, buffer_percent):
    """
    Recorta a imagem ao redor de um polígono com um buffer adicional.
    
    Parâmetros:
    image_file (str): Caminho do arquivo da imagem.
    polygon (Polygon): Polígono do shapefile.
    buffer_percent (float): Percentual de buffer ao redor do polígono.
    
    Retorna:
    tuple: Imagem recortada, transformação e metadados atualizados.
    """
    with rasterio.open(image_file) as src:
        bbox = polygon.bounds
        minx, miny, maxx, maxy = bbox

        x_buffer = (maxx - minx) * buffer_percent
        y_buffer = (maxy - miny) * buffer_percent

        bbox_expanded = box(minx - x_buffer, miny - y_buffer, maxx + x_buffer, maxy + y_buffer)

        out_image, out_transform = mask.mask(src, [bbox_expanded], crop=True)
        out_meta = src.meta
        out_meta.update({
            "driver": "GTiff",
            "height": out_image.shape[1],
            "width": out_image.shape[2],
            "transform": out_transform
        })

        return out_image, out_transform, out_meta

def create_masked_image(image, polygon, transform):
    """
    Cria uma imagem mascarada onde a área dentro do polígono é definida como NaN.
    
    Parâmetros:
    image (numpy.ndarray): Imagem de entrada.
    polygon (Polygon): Polígono do shapefile.
    transform (Affine): Transformação da imagem.
    
    Retorna:
    numpy.ndarray: Imagem com a área do polígono mascarada.
    """
    transformed_polygon = [polygon]
    mask_data = geometry_mask(transformed_polygon, transform=transform, invert=True, out_shape=image.shape[1:])
    inverse_mask_data = ~mask_data
    masked_image = np.where(inverse_mask_data, image, np.nan)

    return masked_image

# Uso do exemplo:
dir_img = 'caminho para o arquivo'
image_file = f'{dir_img}caminho para o arquivo.tif'
shp_dir = f'{dir_img}'
buffer_percent = 0.05  # 5% de buffer ao redor do polígono

# Garantir que o diretório de saída exista
os.makedirs(shp_dir, exist_ok=True)

# Iterar sobre cada shapefile no diretório
for shp_f in glob.glob(os.path.join(shp_dir, '*.shp')):
    polygons = gpd.read_file(shp_f)
    
    for idx, polygon in polygons.iterrows():
        out_image, out_transform, out_meta = crop_image_around_polygon(image_file, polygon.geometry, buffer_percent)
        masked_image = create_masked_image(out_image, polygon.geometry, out_transform)
        
        output_image_file = os.path.join(shp_dir, f'{os.path.splitext(os.path.basename(shp_f))[0]}_background.tif')
        with rasterio.open(output_image_file, 'w', **out_meta) as dst:
            dst.write(masked_image)
        
        print(f"Imagem recortada para {os.path.basename(shp_f)} salva com sucesso em {output_image_file}.")






