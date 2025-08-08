from pathlib import Path
from xml.etree.ElementTree import XMLParser

from histolab.slide import Slide
from histolab.slide import CoordinatePair

from asap_loader.annotation.objects.group import Group
from asap_loader.annotation.objects.point import Point
from asap_loader.annotation.objects.region import Region
from asap_loader.annotation.xml.annotation import Annotation
from asap_loader.annotation.xml.annotation_group import AnnotationGroup
from asap_loader.annotation.xml.annotation_container import AnnotationContainer

from PIL import ImageDraw
from PIL.Image import Image


class GroupContainer:
    def __init__(self, groups: list[AnnotationGroup]) -> None:
        self.__container: dict[str, Group] = {}

        for group in groups:
            self.add(
                Group(
                    group.name,
                    group.color,
                    None,
                )
            )

    def add(self, group: Group):
        self.__container[group.name] = group

    def get(self, group_name: str | None) -> Group | None:
        return self.__container[group_name] if group_name else None


class AnnotatedWSI:
    groups: GroupContainer
    points: list[Point]
    regions: list[Region]

    def __init__(self, slide_path: Path | str):
        self.slide_path = (
            slide_path if isinstance(slide_path, Path) else Path(slide_path)
        )

        self.wsi = Slide(self.slide_path, "")
        self.annotation_path = self.slide_path.with_suffix(".xml")

        annotation_container = AnnotationContainer()
        with self.annotation_path.open() as f:
            parser = XMLParser(target=annotation_container)
            parser.feed(f.read())
            parser.close()

        self.groups = GroupContainer(annotation_container.annotation_groups)
        self.regions = [
            self._parse_region(region)
            for region in filter(
                lambda x: x.type == "Rectangle", annotation_container.annotations
            )
        ]
        self.points = [
            self._parse_point(point)
            for point in filter(
                lambda x: x.type == "Dot", annotation_container.annotations
            )
        ]

    def _parse_region(self, annotation: Annotation) -> Region:
        assert (
            len(annotation.coordinates) == 4
        ), "Number of cordinates is not equal to 4"

        xs = list(map(lambda coord: coord.x, annotation.coordinates))
        ys = list(map(lambda coord: coord.y, annotation.coordinates))

        return Region(
            annotation.name,
            annotation.color,
            self.groups.get(annotation.group),
            min(xs),
            max(xs),
            min(ys),
            max(ys),
        )

    def _parse_point(self, annotation: Annotation) -> Point:
        assert len(annotation.coordinates) == 1, "Multiple coordinates for single point"

        point = Point(
            annotation.name,
            annotation.color,
            self.groups.get(annotation.group),
            annotation.coordinates[0].x,
            annotation.coordinates[0].y,
        )

        for region in self.regions:
            region.add(point)

        return point

    def get_region(
        self, index: int, level: int | None = 0, draw_annotations: bool = False
    ) -> Image:
        assert index >= 0 and index < len(self.regions)

        region = self.regions[index]
        coordinates = CoordinatePair(
            int(region.x_min),
            int(region.y_min),
            int(region.x_max),
            int(region.y_max),
        )

        downsample_ratio = (
            self.wsi.level_dimensions()[0] / self.wsi.level_dimensions(level=level)[0]
        )
        base_size = (region.x_max - region.x_min, region.y_max - region.y_min)

        image = self.wsi.extract_tile(
            coordinates,
            (
                int(base_size[0] / downsample_ratio),
                int(base_size[1] / downsample_ratio),
            ),
            level=level,
        ).image

        draw = ImageDraw.Draw(image)

        if draw_annotations:
            for point in region.members:
                color = point.group.color if point.group else point.color

                draw.circle(
                    (
                        (point.x - region.x_min) / downsample_ratio,
                        (point.y - region.y_min) / downsample_ratio,
                    ),
                    fill=color,
                    radius=3,
                )

        return image
