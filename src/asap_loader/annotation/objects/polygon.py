from dataclasses import dataclass
from asap_loader.annotation.objects.annotation_object import AnnotationObject
from asap_loader.annotation.objects.point import Point
from shapely import geometry


@dataclass
class Polygon(AnnotationObject):
    verticies: set[tuple[float]]

    @property
    def label(self) -> str | None:
        return getattr(self.group, "name", None)

    def __contains__(self, point: Point) -> bool:
        geo_point = geometry.Point(point.x, point.y)
        geo_polygon = geometry.Polygon(self.verticies)
        return geo_point.within(geo_polygon)
