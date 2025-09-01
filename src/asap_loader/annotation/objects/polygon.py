from dataclasses import dataclass
from asap_loader.annotation.objects.annotation_object import AnnotationObject
from asap_loader.annotation.objects.point import Point
from shapely import geometry, centroid


@dataclass
class Polygon(AnnotationObject):
    vertices: set[tuple[float]]

    # def __post_init__(self):
    #     super().__po
    #     print("Created polygon: ", len(self.vertices), " vertices")

    @property
    def label(self) -> str | None:
        return getattr(self.group, "name", None)

    def __contains__(self, point: Point) -> bool:
        geo_point = geometry.Point(point.x, point.y)
        geo_polygon = geometry.Polygon(self.vertices)
        return geo_point.within(geo_polygon)

    def centeroid(self):
        geo_polygon = geometry.Polygon(self.vertices)
        center = centroid(geo_polygon)
        return center.x, center.y

    def bbox_dims(self):

        x_min = min([point[0] for point in self.vertices])
        x_max = max([point[0] for point in self.vertices])

        y_min = min([point[1] for point in self.vertices])
        y_max = max([point[1] for point in self.vertices])

        return (x_max - x_min, y_max - y_min)
