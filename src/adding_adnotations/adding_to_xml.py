import xml.etree.ElementTree as ET
from pathlib import Path


def get_info_from_filename(txt_filename):
    name = txt_filename.split(".")[0]
    elems = name.split("_")
    assert len(elems) == 9
    wsi = "_".join([elem for elem in elems[:3]])
    roi_id = elems[4]
    cls_id = elems[7].removeprefix("cls")

    info_dict = {
        "wsi": wsi,
        "roi_id": roi_id,
        "cls_id": cls_id,
        "other": [elem for i, elem in enumerate(elems) if i not in (0, 1, 2, 3, 5, 7)],
    }
    print(info_dict)
    return info_dict


def get_coord_txt_content(txt_file, column_names=None):

    txt_attributes = column_names or [
        "cls_id",
        "x_center",
        "y_center",
        "width",
        "height",
    ]
    contents = []
    with open(txt_file, "r") as file:
        lines = file.readlines()
        for line in lines:
            annotation_info = {}
            elems = line.split()
            assert len(elems) == len(txt_attributes)
            for elem, attr in zip(elems, txt_attributes):
                annotation_info[attr] = float(elem)
            contents.append(annotation_info)

    return contents


def get_next_annotation_number(xml_root):
    existing_annotations = xml_root.findall("./Annotations/Annotation")

    if existing_annotations is None:
        return None
    if len(existing_annotations) < 1:
        return 0

    last_annotation_name = existing_annotations[-1].attrib.get("Name")
    next_annotation_number = int(last_annotation_name.split()[-1]) + 1
    return next_annotation_number


def add_rectangle_annotation(
    xml_annotations_root,
    annotation_info,
    next_annotation_number,
    roi_series,
    annotation_groups,
    colour,
):
    annotation_name = f"Annotation {next_annotation_number}"
    new_annotation_attrib = {
        "Name": annotation_name,
        "Type": "Rectangle",
        "PartOfGroup": annotation_groups[annotation_info["cls_id"]],
        "Color": colour,
    }

    new_annotation = ET.Element("Annotation", attrib=new_annotation_attrib)
    new_coords = ET.Element("Coordinates")

    print(annotation_info)

    # roi_id = annotation_info["roi_id"]

    print("len: ", len(roi_series))

    x_center = annotation_info["x_center"] * roi_series.width + roi_series.x_min
    y_center = annotation_info["y_center"] * roi_series.height + roi_series.y_min
    annotation_width = annotation_info["width"] * roi_series.width
    annotation_height = annotation_info["height"] * roi_series.height

    x_min = x_center - annotation_width / 2
    x_max = x_center + annotation_width / 2

    y_min = y_center - annotation_height / 2
    y_max = y_center + annotation_height / 2

    print("ROI width: ", roi_series.width)

    # x_min = annotation_info["x_center"] - annotation_info["width"] // 2
    # x_max = annotation_info["x_center"] + annotation_info["width"] // 2
    # y_min = annotation_info["y_center"] - annotation_info["height"] // 2
    # y_max = annotation_info["y_center"] + annotation_info["height"] // 2

    coord_attribs_0 = {"Order": "0", "X": str(x_min), "Y": str(y_min)}
    coord_0 = ET.Element("Coordinate", attrib=coord_attribs_0)
    new_coords.append(coord_0)
    coord_attribs_1 = {"Order": "1", "X": str(x_max), "Y": str(y_min)}
    coord_1 = ET.Element("Coordinate", attrib=coord_attribs_1)
    new_coords.append(coord_1)
    coord_attribs_2 = {"Order": "2", "X": str(x_max), "Y": str(y_max)}
    coord_2 = ET.Element("Coordinate", attrib=coord_attribs_2)
    new_coords.append(coord_2)
    coord_attribs_3 = {"Order": "3", "X": str(x_min), "Y": str(y_max)}
    coord_3 = ET.Element("Coordinate", attrib=coord_attribs_3)
    new_coords.append(coord_3)

    new_annotation.append(new_coords)
    xml_annotations_root.append(new_annotation)

    return xml_annotations_root


def add_annotation_groups(xml_groups_root, added_groups, annotation_colours):

    existing_groups = xml_groups_root.findall("./AnnotationGroup")

    if existing_groups is not None or len(existing_groups) > 0:
        existing_group_names = set(
            [group.attrib.get("Name") for group in existing_groups]
        )
        added_groups = added_groups.difference(existing_group_names)

    for group_name in added_groups:
        new_group_attribs = {
            "Name": group_name,
            "PartOfGroup": "None",
            "Color": annotation_colours[group_name],
        }
        new_group = ET.Element("AnnotationGroup", attrib=new_group_attribs)
        xml_groups_root.append(new_group)


def update_xmls(
    xml_src_dir,
    xml_out_dir,
    txt_files,
    roi_df,
    backup_files,
    annotation_groups,
    annotation_colours,
    all_colour,
    verbose=False,
):
    for txt_file in txt_files:
        info = get_info_from_filename(txt_file.name)

        txt_contents = get_coord_txt_content(txt_file)

        xml_filename = f"{info['wsi']}.xml"
        xml_filepath = Path(xml_src_dir, xml_filename)

        tree = ET.parse(xml_filepath)
        root = tree.getroot()

        if verbose:
            print(f"WSI: {info['wsi']}:")
            print(" - Before: ", len(root.findall(".//Annotation")), "annotations")

        print(txt_contents)

        next_annotation_number = get_next_annotation_number(root)

        added_groups = set()

        for annotation_info in txt_contents:

            # print(roi_df)
            print("Info: ", info)

            roi_series = roi_df[
                (roi_df["slide"] == info["wsi"])
                & (roi_df["patch_id"] == info["roi_id"])
            ]

            print(roi_series)

            add_rectangle_annotation(
                root.find(".//Annotations"),
                annotation_info,
                next_annotation_number,
                roi_series,
                annotation_groups,
                all_colour,
            )
            added_groups.add(annotation_groups[annotation_info["cls_id"]])
            next_annotation_number += 1

        add_annotation_groups(
            root.find(".//AnnotationGroups"), added_groups, annotation_colours
        )

        if verbose:
            print(" - After: ", len(root.findall(".//Annotation")), "annotations")

        ET.indent(tree, space="  ")

        if backup_files:
            xml_bck_filename = f"{info['wsi']}_bck.xml"
            xml_bck_filepath = Path(xml_src_dir, xml_bck_filename)
            xml_filepath.rename(xml_bck_filepath)
        tree.write(
            f"{xml_out_dir}//{info['wsi']}.xml", encoding="utf-8", xml_declaration=True
        )
