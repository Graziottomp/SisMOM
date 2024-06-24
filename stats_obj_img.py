#Stats_obj_img
#_________________________________________________________________________________________
# Rotina que recebe uma imagem de um objeto (mancha de óleo) e do fundo (mar) e realiza 
# as estatísticas entre os dois para melhor análise se é ou não óleo no oceano
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
import csv
import rasterio
import numpy as np
import scipy.ndimage as ndi
import skimage.filters as filters
from skimage.filters import threshold_mean, threshold_otsu

def load_class_data(class_data_csv):
    """
    Carrega dados de classe de um arquivo CSV e retorna um dicionário com ID_POLY como chave.
    """
    class_data = {}
    with open(class_data_csv, mode='r') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        for row in csv_reader:
            class_data[row['ID_POLY']] = {
                'CLASSE': row['CLASSE'],
                'SUBCLASSE': row['SUBCLASSE']
            }
    return class_data


def stats_obj_img(fname_img_pol, fname_img, img_name, class_data):
    """
    Calcula estatísticas de uma imagem de objeto e de fundo, bem como métricas relacionadas ao gradiente.

    :param fname_img_pol: caminho para o arquivo raster do objeto (polígono).
    :param fname_img: caminho para o arquivo raster da imagem de fundo.
    :param img_name: nome da imagem.
    :param class_data: dicionário com dados de classe.
    :return: Um dicionário contendo estatísticas e métricas calculadas.
    """
    # Extrair ID_POLY removendo tudo após o primeiro "_"
    id_poly = img_name.split('_background')[0]
    id_poly_base = id_poly.split('_')[0]

    # Estatísticas do Objeto
    with rasterio.open(fname_img_pol) as object_img:
        band_object = object_img.read(1)
        if band_object.size == 0 or np.all(np.isnan(band_object)):
            raise ValueError("Objeto de imagem vazio ou sem valores válidos")
        object_mean = np.nanmean(band_object)  # Média, ignorando NaNs
        object_std_dev = np.nanstd(band_object)  # Desvio padrão, ignorando NaNs
        object_max = np.nanmax(band_object)
        object_min = np.nanmin(band_object)
        object_median = np.nanmedian(band_object)
        object_coefficient_of_variation = object_std_dev / object_mean  # Coeficiente de variação

    # Estatísticas do Fundo
    with rasterio.open(fname_img) as background_img:
        band_background = background_img.read(1)
        if band_background.size == 0 or np.all(np.isnan(band_background)):
            raise ValueError("Imagem de fundo vazia ou sem valores válidos")
        
        finite_background = band_background[np.isfinite(band_background)]
        if finite_background.size == 0:
            raise ValueError("Imagem de fundo sem valores finitos")
        
        # Threshold para identificar fundo
        try:
            background_threshold = threshold_mean(finite_background)
        except ValueError as e:
            print(f"Erro ao calcular o threshold médio para {img_name}: {e}")
            print("Usando threshold Otsu como fallback.")
            try:
                background_threshold = threshold_otsu(finite_background)
            except ValueError as e:
                raise ValueError(f"Erro ao calcular threshold Otsu para {img_name}: {e}")

        background_mean = np.nanmean(band_background)  # Média, ignorando NaNs
        background_std_dev = np.nanstd(band_background)  # Desvio padrão, ignorando NaNs
        background_max = np.nanmax(band_background)
        background_min = np.nanmin(band_background)
        background_median = np.nanmedian(band_background)
        background_coefficient_of_variation = background_std_dev / background_mean

        # Gradientes e Bordas
        gradient_x = ndi.sobel(band_background, axis=1)  # Gradiente ao longo do eixo X
        gradient_y = ndi.sobel(band_background, axis=0)  # Gradiente ao longo do eixo Y
        gradient_magnitude = np.hypot(gradient_x, gradient_y)

        edges = filters.sobel(band_background)  # Detecção de bordas

        border_gradients = gradient_magnitude[edges > 0]
        if border_gradients.size == 0:
            mean_border_gradient = np.nan
            gradient_std_dev = np.nan
            max_border_gradient = np.nan
        else:
            mean_border_gradient = np.nanmean(border_gradients)
            gradient_std_dev = np.nanstd(border_gradients)
            max_border_gradient = np.nanmax(border_gradients)

        # Contraste entre objeto e fundo
        finite_object = band_object[np.isfinite(band_object)]
        if finite_object.size == 0:
            raise ValueError("Objeto sem valores finitos")

        try:
            object_threshold = threshold_mean(finite_object)  # Valor do threshold
        except ValueError as e:
            print(f"Erro ao calcular o threshold médio para objeto em {img_name}: {e}")
            print("Usando threshold Otsu como fallback.")
            try:
                object_threshold = threshold_otsu(finite_object)
            except ValueError as e:
                raise ValueError(f"Erro ao calcular threshold Otsu para objeto em {img_name}: {e}")

        lowest_backscatter_object = np.nanmin(band_object)

        max_contrast = abs(background_mean - lowest_backscatter_object)
        mean_contrast = abs(background_mean - object_mean)

        # Object Power to Mean Ratio
        object_power_to_mean_ratio = object_mean / background_mean

    # Adicionar informações de classe
    classe_info = class_data.get(id_poly_base, {'CLASSE': 'Desconhecido', 'SUBCLASSE': 'Desconhecido'})

    # Resultados como um dicionário
    results = {
        "img_name": '21 S1B_IW_GRDH_1SDV_20200802T001516_NR_Orb_Cal_TC',
        "IMG_NUMBER": '21',
        "ID_POLY": id_poly,
        "CLASSE": classe_info['CLASSE'],
        "SUBCLASSE": classe_info['SUBCLASSE'],
        "area": '',
        "perim": '',
        "complexity_measure": '',
        "spreading": '',
        "shape_factor": '',
        "hu_moment": '',
        "circularity": '',
        "FG_MEAN": object_mean,
        "FG_STD": object_std_dev,
        "FG_MIN": object_min,
        "FG_MAX": object_max,
        "FG_MEDIAN": object_median,
        "FG_VAR_COEF": object_coefficient_of_variation,
        "FG_THRES": object_threshold,
        "BG_MEAN": background_mean,
        "BG_STD": background_std_dev,
        "BG_MIN": background_min,
        "BG_MAX": background_max,
        "BG_MEDIAN": background_median,
        "BG_VAR_COEF": background_coefficient_of_variation,
        "BG_THRES": background_threshold,
        "FG_BG_MAX_CONTRAST": max_contrast,
        "FG_BG_MEAN_CONTRAST_RATIO": mean_contrast,
        "POWER_MEAN_RATIO": object_power_to_mean_ratio,
        "BORDER_GRAD_MEAN": mean_border_gradient,
        "BORDER_GRAD_STD": gradient_std_dev,
        "BORDER_GRAD_MAX": max_border_gradient,
    }

    return results


def main():
    # Diretório contendo as imagens
    img_dir = 'caminho para o arquivo'
    class_data_csv = 'caminho para o arquivo.csv'

    # Carregar dados de classe
    class_data = load_class_data(class_data_csv)

    # Nome do arquivo CSV para salvar resultados
    csv_filename = "caminho para o arquivo.csv"

    # Verifica se o arquivo CSV existe, se não, cria e escreve o cabeçalho
    if not os.path.isfile(csv_filename):
        with open(csv_filename, mode='w', newline='') as csvfile:
            fieldnames = [
                "img_name", "IMG_NUMBER", "ID_POLY", "CLASSE", "SUBCLASSE", "area",
                "perim", "complexity_measure", "spreading", "shape_factor", "hu_moment",
                "circularity", "FG_MEAN", "FG_STD", "FG_MIN", "FG_MAX", "FG_MEDIAN",
                "FG_VAR_COEF", "FG_THRES", "BG_MEAN", "BG_STD", "BG_MIN", "BG_MAX",
                "BG_MEDIAN", "BG_VAR_COEF", "BG_THRES", "FG_BG_MAX_CONTRAST",
                "FG_BG_MEAN_CONTRAST_RATIO", "POWER_MEAN_RATIO", "BORDER_GRAD_MEAN",
                "BORDER_GRAD_STD", "BORDER_GRAD_MAX",
            ]
            csv_writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            csv_writer.writeheader()

        # Processa cada imagem na pasta
    for img_name in os.listdir(img_dir):
        if img_name.endswith('_background.tif'):  # Verifica se é um arquivo TIFF de background
            try:
                # Caminhos para os arquivos do objeto e do fundo
                fname_img_pol = os.path.join(img_dir, img_name)
                fname_img = os.path.join(img_dir, img_name.split('_background')[0] + '.tif')

                # Obter estatísticas usando a função stats_obj_img
                results = stats_obj_img(fname_img_pol, fname_img, img_name, class_data)

                # Escrever resultados em arquivo CSV
                with open(csv_filename, mode='a', newline='') as csvfile:  # Modo 'a' para append
                    csv_writer = csv.DictWriter(csvfile, fieldnames=results.keys())
                    csv_writer.writerow(results)

            except Exception as e:
                print(f"Erro ao processar a imagem {img_name}: {e}")
                continue

    print(f"Resultados adicionados a {csv_filename}")

if __name__ == "__main__":
    main()
