OPENSLIDE_PATH = "C:\\Users\\MS\\openslide-bin-4.0.0.8-windows-x64\\bin"
import os
from pathlib import Path

if hasattr(os, "add_dll_directory"):
    # Windows
    with os.add_dll_directory(OPENSLIDE_PATH):
        import openslide
    print(openslide.__version__)
else:
    print("nope")
    import openslide

from histolab.slide import Slide, CoordinatePair
import cv2
import numpy as np


def get_tile_coordinates(tile_filename, slide_filename, roi_x_min, roi_y_min, roi_w, roi_h):

    slide = Slide(slide_filename, "")

    downsample_ratio = (
        slide.level_dimensions()[0] / slide.level_dimensions(level=0)[0]
    )
    
    # print("Slide level dim: ", slide.level_dimensions())
    # print("Slide level dim (level 0): ", slide.level_dimensions(level=0))

    coordinates = CoordinatePair(
        int(roi_x_min),
        int(roi_y_min),
        int(roi_x_min + roi_w),
        int(roi_y_min + roi_h),
    )
    image = slide.extract_tile(
        coordinates,
        (
            int(roi_w / downsample_ratio),
            int(roi_h / downsample_ratio),
        ),
        level=0,
    ).image


    region_np = np.array(image)
    region_cv = cv2.cvtColor(region_np, cv2.COLOR_RGB2GRAY)

    
    tile = cv2.imread(tile_filename, cv2.IMREAD_GRAYSCALE)
    
    # print("Tile shape:", tile.shape)       
    # print("Region shape:", region_cv.shape)


    result = cv2.matchTemplate(region_cv, tile, cv2.TM_CCOEFF_NORMED)
    _, _, _, max_loc = cv2.minMaxLoc(result)
    x0, y0 = max_loc  
    h, w = tile.shape[:2]
    x_center = x0 + w / 2
    y_center = y0 + h / 2

    coords = (x_center + roi_x_min, y_center + roi_y_min)
    # print("Center:", (x_center, y_center), " -> ", coords)
    
    return coords
