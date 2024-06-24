#_________________________________________________________________________________________
#Corta cada polígono (separando os multipolígonos) e cria um arquivo .shp e um tiff contendo
#os valores dos pixels dentro de cada um deles e com valor NaN envolta deles
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
import rasterio
from rasterio import mask
import os
import geopandas as gpd
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
import pandas as pd
import glob
import numpy as np

def getSlickPolyFromMultiPolygon(dirImg, dataBase, shpFilePath, tiffFilePath):
    df = pd.read_csv(dataBase)
    vectorAll = gpd.read_file(shpFilePath)
    
    if isinstance(tiffFilePath, str):
        tiffFilePaths = [tiffFilePath]

    results = []

    for tiffFilePath in tiffFilePaths:
        tiffBasename = os.path.basename(tiffFilePath)
        idxImg = int(tiffBasename.split(' ')[0]) 
        vectorImg = vectorAll[vectorAll['IMG_NUMBER'] == idxImg]

        if not vectorImg.empty:
            df_filtered = df[df['IMG_NUMBER'] == idxImg]
            if 'ID_POLY' in df_filtered.columns and not df_filtered.empty:
                for idPoly in df_filtered['ID_POLY'].unique():
                    multipolygonRow = vectorImg[vectorImg['ID_POLY'] == idPoly]
                    if not multipolygonRow.empty:
                        geometry = multipolygonRow.geometry.values[0]
                        if isinstance(geometry, MultiPolygon):
                            multipolygon = geometry
                            
                            outputDir = os.path.join(dirImg, str(idxImg), str(idPoly))
                            os.makedirs(outputDir, exist_ok=True)

                            geometries = list(multipolygon.geoms)
                            numPolygons = len(geometries)
                            
                            data = {'ID_POLY': [f"{idPoly}_{idx}" for idx in range(1, numPolygons + 1)]}
                            newGdf = gpd.GeoDataFrame(data, geometry=geometries)
                            with rasterio.open(tiffFilePath, masked=True, chunks=True) as tiff:
                                for idx, row in newGdf.iterrows():
                                    outImage, outTransform = mask.mask(tiff, [row['geometry']], crop=True, nodata=np.nan)
                                    outMeta = tiff.meta

                                    outMeta.update({
                                        "driver": "GTiff",
                                        "height": outImage.shape[1],
                                        "width": outImage.shape[2],
                                        "transform": outTransform
                                    })

                                    outputTiff = os.path.join(outputDir, f"{row['ID_POLY']}.tif")
                                    outputShp = os.path.join(outputDir, f"{row['ID_POLY']}.shp")
                                
                                    with rasterio.open(outputTiff, "w", **outMeta) as dest:
                                            dest.write(outImage)

                                    row['geometry'] = row['geometry'].buffer(0)
                                    rowGdf = gpd.GeoDataFrame([row])
                                    rowGdf.crs = newGdf.crs
                                    rowGdf.to_file(outputShp)

                                    results.append(f"Created {outputTiff}, shape: {outImage.shape}")
                                    results.append(f"Created {outputShp}")

                            results.append(f"ID_POLY {idPoly} is a multipolygon, divided into {numPolygons} polygons.")
                        else:
                                outputDir = os.path.join(dirImg, str(idxImg), str(idPoly))
                                os.makedirs(outputDir, exist_ok=True)

                                with rasterio.open(tiffFilePath, masked=True, chunks=True) as tiff:
                                    outImage, outTransform = mask.mask(tiff, [geometry], crop=True, nodata=np.nan)
                                    outMeta = tiff.meta

                                    outMeta.update({
                                        "driver": "GTiff",
                                        "height": outImage.shape[1],
                                        "width": outImage.shape[2],
                                        "transform": outTransform
                                    })
                                    
                                    outputTiff = os.path.join(outputDir, f"{idPoly}.tif")
                                    outputShp = os.path.join(outputDir, f"{idPoly}.shp")

                                    with rasterio.open(outputTiff, "w", **outMeta) as dest:
                                        dest.write(outImage)

                                    row = multipolygonRow.iloc[0]
                                    row['geometry'] = row['geometry'].buffer(0)
                                    rowGdf = gpd.GeoDataFrame([row])
                                    rowGdf.crs = vectorImg.crs
                                    rowGdf.to_file(outputShp)

                                    results.append(f"Created {outputTiff}, shape: {outImage.shape}")
                                    results.append(f"Created {outputShp}")
                    else:
                        results.append(f"No multipolygon found for ID_POLY {idPoly} in image {idxImg}.")
            else:
                results.append(f"No ID_POLY found for image number {idxImg}.")
        else:
            results.append(f"No polygons found for image number {idxImg}.")

    return results


dirImg = 'caminho para o arquivo'
dataBase = glob.glob(f'{dirImg}\\*.csv')[0]
shpFilePath = glob.glob(f'{dirImg}\\*.shp')[0]
tiffFilePath = glob.glob(f"{dirImg}*.tif")[0]

getSlickPolyFromMultiPolygon(dirImg, dataBase, shpFilePath, tiffFilePath)
