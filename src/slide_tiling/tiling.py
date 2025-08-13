OPENSLIDE_PATH = "C:\\Users\\MS\\openslide-bin-4.0.0.8-windows-x64\\bin"

import os

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
from IPython.display import display


def get_annotation_groups(xml_root, selected_group_names=None) -> dict:
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


def get_group_members(xml_root, group_dict, verbose=False) -> dict:

    for annotation in xml_root.find("./Annotations"):
        class_name = annotation.attrib["PartOfGroup"]
        if class_name not in group_dict.keys():
            if verbose:
                print(f"Omitting {class_name}")
            continue

        if annotation.attrib["Type"] == "Dot":
            coord = annotation.find("./Coordinates/Coordinate")
            point = Point(
                group=group_dict[class_name],
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
                group=group_dict[class_name],
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
                group=group_dict[class_name],
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


def get_images_for_group(slide, group, width_px, height_px, wsi_level):

    images = []
    downsample_ratio = (
        slide.level_dimensions()[0] / slide.level_dimensions(level=wsi_level)[0]
    )

    for member in group.members:

        if isinstance(member, Polygon) or isinstance(member, Rectangle):
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


def get_tile_images_from_wsi(
    xml_path: Path,
    mrxs_path: Path,
    selected_classes: set,
    bbox_size: tuple[int],
    wsi_level=0,
):

    tree = ET.parse(xml_path)
    root = tree.getroot()

    annotation_groups = get_annotation_groups(root, selected_classes)
    # print(annotation_groups)
    annotation_groups = get_group_members(root, annotation_groups)

    slide = Slide(mrxs_path, "")

    all_images = []
    images = []
    for group in annotation_groups.values():
        images = get_images_for_group(slide, group, *bbox_size, wsi_level=wsi_level)
        all_images += images

    return images
    # return []


def save_tile_images_from_wsi(
    wsi_name: str,
    src_path: Path,
    dest_path: Path,
    selected_classes: list,
    bbox_size: tuple[int],
    wsi_level=0,
    infix="TILE",
    ext="png",
    show_n=None,
):

    xml_path = src_path / Path(f"{wsi_name}.xml")
    mrxs_path = src_path / Path(f"{wsi_name}.mrxs")

    images = get_tile_images_from_wsi(
        xml_path, mrxs_path, selected_classes, bbox_size, wsi_level
    )

    for i, image in enumerate(images):
        filename = dest_path / Path(f"{wsi_name}_{infix}_{i}.{ext}")
        image.save(filename)

        if isinstance(show_n, int) and show_n > 0:
            display(image)
            show_n = show_n - 1


def save_tile_images(
    train_wsi_names: list[str],
    test_wsi_names: list[str],
    data_dir,
    out_dir,
    selected_classes,
    bbox_size,
    show_n=None,
):
    src_path = Path(data_dir)
    sections = ["test", "train"]
    wsi_names = {"test": train_wsi_names, "train": test_wsi_names}

    for section in sections:
        for class_name in selected_classes:
            section_dest_path = Path(out_dir, section, class_name)
            section_dest_path.mkdir(exist_ok=True, parents=True)

            for wsi_name in wsi_names[section]:
                print(f"{wsi_name} {section} class: {class_name}")
                save_tile_images_from_wsi(
                    wsi_name,
                    src_path,
                    section_dest_path,
                    selected_classes=[class_name, class_name.lower()],
                    bbox_size=bbox_size,
                    show_n=show_n,
                )
