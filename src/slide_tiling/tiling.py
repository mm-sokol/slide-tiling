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

from asap_loader.annotation.objects.rectangle import Rectangle
from asap_loader.annotation.objects.polygon import Polygon
from asap_loader.annotation.objects.point import Point

import xml.etree.ElementTree as ET
from asap_loader.annotation.objects.rectangle import Rectangle
from asap_loader.annotation.objects.group import Group
from pathlib import Path
from os import listdir
from histolab.slide import Slide, CoordinatePair
from PIL.Image import Image


def get_annotation_groups(xml_root, selected_group_names=None):
    groups = []

    for child in xml_root.find("./AnnotationGroups"):
        group_data = {}
        group_data["name"] = child.attrib["Name"]
        group_data["color"] = child.attrib["Color"]
        group_data["group"] = (
            None
            if child.attrib["PartOfGroup"] == "None"
            else child.attrib["PartOfGroup"]
        )

        group = Group(**group_data)
        groups.append(group)

    if selected_group_names is not None:
        group_dict = {gr.name: gr for gr in groups if gr.name in selected_group_names}
    else:
        group_dict = {gr.name: gr for gr in groups}

    return group_dict


def get_group_members(xml_root, group_dict, verbose=False):

    for annotation in xml_root.find("./Annotations"):
        if annotation.attrib["Type"] == "Dot":
            coord = annotation.find("./Coordinates/Coordinate")
            point = Point(
                group=group_dict[annotation.attrib["PartOfGroup"]],
                name=annotation.attrib["Name"],
                color=annotation.attrib["Color"],
                x=float(coord.attrib["X"]),
                y=float(coord.attrib["Y"]),
            )
            if verbose:
                print(f"Dot: {point}")

        elif annotation.attrib["Type"] in ("Polygon", "Spline", "PointSet"):
            coords = annotation.findall("./Coordinates/Coordinate")
            vertices = [
                (float(coord.attrib["X"]), float(coord.attrib["Y"])) for coord in coords
            ]
            polygon = Polygon(
                group=group_dict[annotation.attrib["PartOfGroup"]],
                name=annotation.attrib["Name"],
                color=annotation.attrib["Color"],
                verticies=vertices,
            )
            if verbose:
                print(f"{annotation.attrib['Type']}: {polygon.centeroid()}")

        elif annotation.attrib["Type"] == "Rectangle":
            coords = annotation.findall("./Coordinates/Coordinate")

            vertices = [
                (float(coord.attrib["X"]), float(coord.attrib["Y"])) for coord in coords
            ]
            xs, ys = zip(*vertices)

            rect = Rectangle(
                group=group_dict[annotation.attrib["PartOfGroup"]],
                name=annotation.attrib["Name"],
                color=annotation.attrib["Color"],
                x_max=max(xs),
                x_min=min(xs),
                y_max=max(ys),
                y_min=min(ys),
            )
            if verbose:
                print(f"Rectangle: {rect.centeroid()}")

        else:
            assert False

    return group_dict


def get_images_for_group_members(mrxs_file, group, width_px, height_px, wsi_level=0):

    slide = Slide(mrxs_file, "")
    downsample_ratio = (
        slide.level_dimensions()[0] / slide.level_dimensions(level=wsi_level)[0]
    )

    images = []
    for member in group.members:

        if isinstance(member, Polygon):
            center = member.centeroid()
        elif isinstance(member, Point):
            center = (member.x, member.y)
        else:
            assert False

        base_size = (width_px, height_px)

        x_min, y_min = (pos - size / 2 for pos, size in zip(center, base_size))
        x_max, y_max = (pos + size / 2 for pos, size in zip(center, base_size))

        coordinates = CoordinatePair(
            int(x_min),
            int(y_min),
            int(x_max),
            int(y_max),
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
