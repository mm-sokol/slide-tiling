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
from PIL import Image
from IPython.display import display
from enum import Enum
import numpy as np


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

    for annotation in xml_root.findall(f"./Annotations/Annotation"):

        class_name = annotation.attrib.get("PartOfGroup")

        if class_name not in group_dict:
            # print(f"{class_name} not in group dict {group_dict}")
            # print(".")
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


def get_images_for_group(slide, group, group_bbox_size, wsi_level, target_size=None):

    images = []
    centers = []
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

        base_size = group_bbox_size

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

        if target_size is not None:
            tile = Image.new("RGB", target_size, (0, 0, 0))

            left, top = (
                (tgt_px - img_px) // 2 for tgt_px, img_px in zip(target_size, base_size)
            )

            # print("target=", target_size, " bbox=", bbox.size, " left=", left, " top=", top)
            tile.paste(image, (left, top))

            images.append(tile)
        else:
            images.append(image)
        centers.append(center)

    print(f"[get_images_for_group] {group.name}: ", len(images))

    return images, centers


def get_regions(xml_root):

    roi = []

    for region in xml_root[0]:
        #     if "Type" in child.attrib and child.attrib["Type"] == "Rectangle":
        # for region in xml_root.findall(f"./Annotations/Annotation"):
        if region.attrib.get("PartOfGroup") not in ("Obszary", "Obszary "):
            continue
        coords = region.findall("./Coordinates/Coordinate")
        vertices = [
            (float(coord.attrib["X"]), float(coord.attrib["Y"])) for coord in coords
        ]
        xs, ys = zip(*vertices)

        rect = Rectangle(
            group=None,
            name=region.attrib["Name"],
            color=region.attrib["Color"],
            x_max=max(xs),
            x_min=min(xs),
            y_max=max(ys),
            y_min=min(ys),
        )
        roi.append(rect)

    return roi


def get_tile_images_from_wsi(
    xml_path: Path,
    mrxs_path: Path,
    selected_classes: set,
    bbox_sizes: dict,
    tile_size=None,
    wsi_level=0,
    show_n=0,
):

    tree = ET.parse(xml_path)
    root = tree.getroot()

    annotation_groups = get_annotation_groups(root, selected_classes)
    annotation_groups = get_group_members(root, annotation_groups)

    slide = Slide(mrxs_path, "")

    all_images = []
    all_centers = []
    all_classes = []

    print(xml_path)
    for groupname, group in annotation_groups.items():

        print(len(group.members))

        images, centers = get_images_for_group(
            slide,
            group,
            group_bbox_size=bbox_sizes[groupname],
            wsi_level=wsi_level,
            target_size=tile_size,
        )

        if isinstance(show_n, int) and show_n > 0:
            display(images[0])
            show_n = show_n - 1

        all_images += images
        all_centers += centers
        all_classes += [groupname for _ in images]

    print("[get_tile_images_from_wsi] WSI images: ", len(all_images))
    return all_images, all_centers, all_classes


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
    verbose=True,
):

    xml_path = src_path / Path(f"{wsi_name}.xml")
    mrxs_path = src_path / Path(f"{wsi_name}.mrxs")

    images = get_tile_images_from_wsi(
        xml_path, mrxs_path, selected_classes, bbox_size, wsi_level
    )

    n_images = 0
    for i, image in enumerate(images):
        filename = dest_path / Path(f"{wsi_name}_{infix}_{i}.{ext}")
        image.save(filename)

        if verbose:
            n_images = n_images + 1
        if isinstance(show_n, int) and show_n > 0:
            display(image)
            show_n = show_n - 1

    if verbose:
        print(wsi_name, ": ", n_images, " saved")


class ROIAssignmentOption(Enum):
    MIN_CENTER_DIST = 0
    CENTER_WITHIN_ROI = 1


def euc_dist_2d(a, b, dtype=float):
    a, b = np.array(a, dtype=dtype), np.array(b, dtype=dtype)
    return np.sqrt(np.sum((a - b) ** 2, axis=0))


def assign_tiles_to_rois(rois, centers, option=ROIAssignmentOption.CENTER_WITHIN_ROI):

    roi_ids = []
    if option == ROIAssignmentOption.CENTER_WITHIN_ROI:
        for center in centers:
            center_assigned = False
            for i, roi in enumerate(rois):
                if center in roi:
                    roi_ids.append(i)
                    center_assigned = True
                    break
            if not center_assigned:

                roi_ids.append(None)

    elif option == ROIAssignmentOption.MIN_CENTER_DIST:
        for center in centers:
            min_dist = 1000000
            roi_assigned = None
            for i, roi in enumerate(rois):
                roi_center = ((roi.x_max + roi.x_min) / 2, (roi.y_min + roi.y_max) / 2)
                dist = euc_dist_2d(roi_center, center)
                if dist < min_dist:
                    min_dist = dist
                    roi_assigned = i
            roi_ids.append(roi_assigned)
            print("Assigned roi: ", roi_assigned, center)

            if roi_assigned is None:
                print(rois)
                print(center)
                print(min_dist)
                raise IndexError("No ROI assigned.")
    return roi_ids


def save_image_batch(
    out_dir,
    section,
    wsi_name,
    images,
    roiid_assignment,
    classes,
    infix="tile",
    ext="png",
    all_classnames=None,
    class_shortcodes=None,
):

    if all_classnames is not None and len(all_classnames) > 0:
        for classname in all_classnames:
            out_path = Path(out_dir, section, classname)
            out_path.mkdir(parents=True, exist_ok=True)

    print(f"ROIs: {len(roiid_assignment)}")
    print(f"IMGs: {len(images)}")
    print(f"CLASSes: {len(classes)}")

    placeholder = "x"
    for i, (img, roiid, classname) in enumerate(zip(images, roiid_assignment, classes)):
        class_code = class_shortcodes[classname]
        filename = f"{wsi_name}_ROI_{roiid if roiid is not None else placeholder}_{infix}_{i}_{class_code}.{ext}"

        file_path = Path(out_dir, section, classname, filename)
        img.save(file_path)


def save_yolo_dataset_desc(
    out_dir,
    section,
    images,
    centers,
    classes,
    rois,
    roiid_assignment,
    class_map,
    ext="txt",
    prefix="cd34",
    wsi=None,
):

    for img, center, classname, roiid in zip(
        images, centers, classes, roiid_assignment
    ):
        class_num = class_map[classname]
        roi = rois[roiid]
        roi_w = abs(roi.x_max - roi.x_min)
        roi_h = abs(roi.y_max - roi.y_min)
        img_w_norm, img_h_norm = img.size[0] / roi_w, img.size[0] / roi_h
        center_x_norm = (center[0] - roi.x_min) / roi_w
        center_y_norm = (center[1] - roi.y_min) / roi_h
        if center_x_norm > 1 or center_y_norm > 1:
            print(
                f"[WSI {wsi}] Center: {center} -> ({center[0] - roi.x_min}, {center[1] - roi.y_min}), Roi {roiid}: ({roi_w}, {roi_h}) normalized to: ({center_x_norm}, {center_y_norm})"
            )
            continue
        # line_seq = [class_num, center_x_norm, center_y_norm, img_w_norm, img_h_norm]
        # line = " ".join([str(elem) for elem in line_seq])
        line_seq = (
            f"{class_num} {center_x_norm} {center_y_norm} {img_w_norm} {img_h_norm}\n"
        )
        Path(out_dir, section).mkdir(exist_ok=True, parents=True)
        out_path = Path(out_dir, section, f"{wsi}_ROI_{roiid}.{ext}")
        with open(out_path, "a") as yolo_txt:
            yolo_txt.write(line_seq)


def save_tile_images(
    train_wsi_names: list[str],
    test_wsi_names: list[str],
    data_dir,
    out_dir,
    selected_classes,
    class_shortcodes,
    bbox_sizes,
    tile_size=None,
    show_n=None,
):
    # src_path = Path(data_dir)
    sections = ["test", "train"]
    wsi_names = {"train": train_wsi_names, "test": test_wsi_names}

    for section in sections:  # train, test

        for wsi in wsi_names[section]:

            xml_pathname = Path(data_dir, f"{wsi}.xml")
            mrxs_pathname = Path(data_dir, f"{wsi}.mrxs")

            tree = ET.parse(xml_pathname)
            root = tree.getroot()

            rois = sorted(
                get_regions(root), key=lambda r: (r.x_min, r.x_max, r.y_min, r.y_max)
            )

            images, centers, classes = get_tile_images_from_wsi(
                xml_pathname,
                mrxs_pathname,
                selected_classes,
                bbox_sizes,
                tile_size,
                wsi_level=0,
                show_n=show_n,
            )

            roiid_assignment = assign_tiles_to_rois(rois, centers)

            save_image_batch(
                out_dir,
                section,
                wsi,
                images,
                roiid_assignment,
                classes,
                all_classnames=selected_classes,
                class_shortcodes=class_shortcodes,
            )

            print(
                f"{wsi} ({section}): {len(roiid_assignment)} roi_id, {len(images)} images"
            )


def save_yolo_dataset(
    train_wsi_names: list[str],
    test_wsi_names: list[str],
    data_dir,
    out_dir,
    selected_classes,
    class_map,
    bbox_sizes,
    tile_size=None,
    show_n=None,
):
    # src_path = Path(data_dir)
    sections = ["test", "train"]
    wsi_names = {"train": train_wsi_names, "test": test_wsi_names}

    for section in sections:  # train, test

        for wsi in wsi_names[section]:

            xml_pathname = Path(data_dir, f"{wsi}.xml")
            mrxs_pathname = Path(data_dir, f"{wsi}.mrxs")

            tree = ET.parse(xml_pathname)
            root = tree.getroot()

            # rois = sorted(
            #     get_regions(root), key=lambda r: (r.x_min, r.x_max, r.y_min, r.y_max)
            # )
            rois = get_regions(root)

            print("WSI: ", wsi)
            images, centers, classes = get_tile_images_from_wsi(
                xml_pathname,
                mrxs_pathname,
                selected_classes,
                bbox_sizes,
                tile_size,
                wsi_level=0,
                show_n=show_n,
            )

            roiid_assignment = assign_tiles_to_rois(
                rois, centers, ROIAssignmentOption.MIN_CENTER_DIST
            )

            save_yolo_dataset_desc(
                out_dir,
                section,
                images,
                centers,
                classes,
                rois,
                roiid_assignment,
                class_map=class_map,
                wsi=wsi,
            )

            print(
                f"{wsi} ({section}): {len(roiid_assignment)} roi_id, {len(images)} images"
            )
