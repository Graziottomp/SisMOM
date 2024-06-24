#crop_slicks_outOf_image
# _______________________________________________________________________________________
#Substitui o valor dos pixels dentro de todos os poligonos(não separando eles) referente 
# à imagem por NaN e deixa o valor dos pixels ao redor deles intacto 
# _______________________________________________________________________________________
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
from rasterio.features import geometry_mask
import numpy as np

def mask_polygons_in_image(image_file, polygons):
    """
    Mascara a área de todos os polígonos em uma imagem.
    
    Parâmetros:
    image_file (str): Caminho do arquivo da imagem.
    polygons (GeoDataFrame): Geodataframe com os polígonos.
    
    Retorna:
    tuple: Imagem mascarada e metadados atualizados.
    """
    with rasterio.open(image_file) as src:
        image = src.read()
        out_meta = src.meta

        total_mask = np.zeros((src.height, src.width), dtype=bool)
        
        for polygon in polygons.geometry:
            mask_data = geometry_mask([polygon], transform=src.transform, invert=True, out_shape=(src.height, src.width))
            total_mask |= mask_data

        expanded_mask = np.broadcast_to(total_mask, image.shape)
        masked_image = np.where(expanded_mask, np.nan, image)

        return masked_image, out_meta

# Uso do exemplo:
dir_img = 'caminho para o arquivo'
image_file = glob.glob(f"{dir_img}*.tif")[0]
shp_file = 'caminho para o arquivo.shp'
output_file = os.path.join(dir_img, '_output.tif')

polygons = gpd.read_file(shp_file)
masked_image, out_meta = mask_polygons_in_image(image_file, polygons)

out_meta.update({
    "driver": "GTiff",
    "height": masked_image.shape[1],
    "width": masked_image.shape[2],
    "count": masked_image.shape[0],
    "dtype": "float32"
})

with rasterio.open(output_file, 'w', **out_meta) as dst:
    for i in range(masked_image.shape[0]):
        dst.write(masked_image[i], i + 1)

print(f"Imagem final salva com sucesso em {output_file}.")

