#Substitui o valor dos pixels dentro de cada poligonos por NaN e deixa o valor dos pixels ao redor deles intacto 
import os
import glob
import geopandas as gpd
import rasterio
from rasterio import mask
from rasterio.features import geometry_mask
from shapely.geometry import box
import numpy as np

def crop_image_around_polygon(image_file, polygon, buffer_percent):
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
    # Transform polygon to image coordinates
    transformed_polygon = [polygon]

    # Create a mask with the polygon area set to 0
    mask_data = geometry_mask(transformed_polygon, transform=transform, invert=True, out_shape=image.shape[1:])

    # Create an inverse mask where the polygon is 1 and outside is 0
    inverse_mask_data = ~mask_data

    # Apply the inverse mask to the image
    masked_image = np.where(inverse_mask_data, image, np.nan)

    return masked_image

# Example usage:
dir_img = 'C:\\Users\\grazi\\Cantarell\\21'
image_file = f'{dir_img}\\imagem_21_poligonos_NaN.tif'
shp_dir = f'{dir_img}'
buffer_percent = 0.05  # 5% buffer around the polygon

# Ensure output directory exists
os.makedirs(shp_dir, exist_ok=True)

# Iterate over each shapefile in the directory
for shp_f in glob.glob(os.path.join(shp_dir, '*.shp')):
    # Read the shapefile containing the polygons
    polygons = gpd.read_file(shp_f)

    # Iterate over each polygon in the shapefile
    for idx, polygon in polygons.iterrows():
        # Crop the image around the current polygon
        out_image, out_transform, out_meta = crop_image_around_polygon(image_file, polygon.geometry, buffer_percent)

        # Create the masked image
        masked_image = create_masked_image(out_image, polygon.geometry, out_transform)

        # Save the masked image
        output_image_file = os.path.join(shp_dir, f'{os.path.splitext(os.path.basename(shp_f))[0]}_background.tif')
        with rasterio.open(output_image_file, 'w', **out_meta) as dst:
            dst.write(masked_image)

        print(f"Cropped image for {os.path.basename(shp_f)} saved successfully at {output_image_file}.")








#_________________________________________________________________________________________________________________________________________________
#Substitui o valor dos pixels dentro de todos os poligonos(não separando eles) referente à imagem por NaN e deixa o valor dos pixels ao redor deles intacto 
import os
import glob
import geopandas as gpd
import rasterio
from rasterio.features import geometry_mask
from shapely.geometry import box
import numpy as np

def mask_polygons_in_image(image_file, polygons):
    with rasterio.open(image_file) as src:
        # Read the image data
        image = src.read()
        out_meta = src.meta

        # Create an empty mask
        total_mask = np.zeros((src.height, src.width), dtype=bool)

        # Iterate over each polygon to create the mask
        for polygon in polygons.geometry:
            # Create the mask for this polygon
            mask_data = geometry_mask([polygon], transform=src.transform, invert=True, out_shape=(src.height, src.width))

            # Combine this mask with the total mask
            total_mask |= mask_data

        # Apply the total mask to set the polygon areas to NaN
        expanded_mask = np.broadcast_to(total_mask, image.shape)
        masked_image = np.where(expanded_mask, np.nan, image)

        return masked_image, out_meta

# Example usage:
dir_img = 'C:\\Users\\grazi\\Cantarell\\'
image_file = glob.glob(f"{dir_img}*.tif")[0]
shp_file = 'C:\\Users\\grazi\\Cantarell\\21\\OilSlicks_Cantarell_GEOG_18052022_01_21.shp'
output_file = os.path.join(dir_img, '_output.tif')  # Final output image file

# Read the shapefile containing the polygons
polygons = gpd.read_file(shp_file)

# Mask the polygons in the image
masked_image, out_meta = mask_polygons_in_image(image_file, polygons)

# Update metadata for saving the masked image
out_meta.update({
    "driver": "GTiff",
    "height": masked_image.shape[1],
    "width": masked_image.shape[2],
    "count": masked_image.shape[0],
    "dtype": "float32"  # Ensure correct data type for NaN values
})

# Save the masked image
with rasterio.open(output_file, 'w', **out_meta) as dst:
    for i in range(masked_image.shape[0]):
        dst.write(masked_image[i], i+1)

print(f"Final output image saved successfully at {output_file}.")
