OPENSLIDE_PATH = r"C:\Users\MS\openslide-bin-4.0.0.8-windows-x64\bin"

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
from PIL.Image import Image
from PIL import ImageDraw
from IPython.display import display

import xml.etree.ElementTree as ET
from asap_loader.annotation.objects.rectangle import Rectangle
from asap_loader.annotation.objects.group import Group
from asap_loader.annotation.objects.annotation_object import AnnotationObject
from pathlib import Path
from pandas import DataFrame


def read_rectangles(xml_path):

    tree = ET.parse(xml_path)
    root = tree.getroot()

    group = None
    for child in root.find("AnnotationGroups"):

        print(xml_path)

        group_data = {}
        if "Obszary" in child.attrib["Name"]:
            group_data["name"] = child.attrib["Name"]
            group_data["color"] = child.attrib["Color"]
            group_data["group"] = (
                None
                if child.attrib["PartOfGroup"] == "None"
                else child.attrib["PartOfGroup"]
            )

            group = Group(**group_data)

    assert group is not None

    for child in root[0]:
        if "Type" in child.attrib and child.attrib["Type"] == "Rectangle":

            rectangle_data = {
                "name": child.attrib["Name"],
                "color": child.attrib["Color"],
                "group": group,
            }

            for coord in child[0]:
                # print(coord.attrib)
                if int(coord.attrib["Order"]) == 0:
                    rectangle_data["x_min"] = float(coord.attrib["X"])
                    rectangle_data["y_min"] = float(coord.attrib["Y"])

                elif int(coord.attrib["Order"]) == 2:
                    temp_x = float(coord.attrib["X"])
                    temp_y = float(coord.attrib["Y"])

            rectangle_data["x_max"] = max(temp_x, rectangle_data["x_min"])
            rectangle_data["y_max"] = max(temp_y, rectangle_data["y_min"])
            rectangle_data["x_min"] = min(temp_x, rectangle_data["x_min"])
            rectangle_data["y_min"] = min(temp_y, rectangle_data["y_min"])

            rectangle = Rectangle(**rectangle_data)

    return group


def get_images_from_group(mrxs_file, rectangle_group, wsi_level=0):

    slide = Slide(mrxs_file, "")
    downsample_ratio = (
        slide.level_dimensions()[0] / slide.level_dimensions(level=wsi_level)[0]
    )

    images = []

    for rect in rectangle_group.members:
        base_size = (rect.x_max - rect.x_min, rect.y_max - rect.y_min)
        coordinates = CoordinatePair(
            int(rect.x_min),
            int(rect.y_min),
            int(rect.x_max),
            int(rect.y_max),
        )
        # print(coordinates)
        image = slide.extract_tile(
            coordinates,
            (
                int(base_size[0] / downsample_ratio),
                int(base_size[1] / downsample_ratio),
            ),
            level=wsi_level,
        ).image

        images.append(image)

    return images


def save_images_from_slide(slide_name, images, dest_dir, group, infix="ROI", ext="png"):

    meta_data = []

    assert len(images) == len(group.members)

    for i, (image, rect) in enumerate(zip(images, group.members)):
        filename = Path(dest_dir, f"{slide_name}_{infix}_{i}.{ext}")
        # image.save(filename)

        info = {
            "slide": slide_name,
            "patch_id": i,
            "x_min": rect.x_min,
            "y_min": rect.y_min,
            "path": filename,
        }
        print(info)
        meta_data.append(info)

    return meta_data


def save_all_patches(data_dir, out_dir):

    dir = Path(data_dir)
    subdirectories = [a.name for a in dir.iterdir() if a.is_dir()]
    print(subdirectories)

    rows = []

    for slide_name in subdirectories:

        xml_file = f"{slide_name}.xml"
        mrxs_file = f"{slide_name}.mrxs"

        xml_pathname = Path(dir, xml_file)
        mrxs_pathname = Path(dir, mrxs_file)

        rect_group = read_rectangles(xml_pathname)
        images = get_images_from_group(mrxs_pathname, rect_group)
        meta_data = save_images_from_slide(slide_name, images, out_dir, rect_group)
        rows = rows + meta_data

    print(rows[0])
    columns = list(rows[0].keys())
    data = {col: [] for col in columns}
    for row in rows:
        keys = list(row.keys())
        for key in keys:
            data[key].append(row[key])

    df = DataFrame(data=data)
    print(df)

    out_datafile = Path(out_dir, "patches.csv")
    df.to_csv(out_datafile)

    return df
