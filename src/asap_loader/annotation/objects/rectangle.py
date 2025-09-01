from dataclasses import dataclass
from asap_loader.annotation.objects.point import Point

from asap_loader.annotation.objects.annotation_object import AnnotationObject


@dataclass
class Rectangle(AnnotationObject):
    x_min: float
    x_max: float
    y_min: float
    y_max: float

    def centeroid(self):
        x_center = (self.x_max + self.x_min) / 2
        y_center = (self.y_max + self.y_min) / 2
        return x_center, y_center

    def bbox_dims(self):
        return (self.x_max - self.x_min, self.y_max - self.y_min)

    def __contains__(self, point: tuple[float]):

        if isinstance(point, tuple):
            if (
                point[0] <= self.x_max
                and point[0] >= self.x_min
                and point[1] <= self.y_max
                and point[1] >= self.y_min
            ):
                return True

        if isinstance(point, Point):
            if (
                point.x <= self.x_max
                and point.x >= self.x_min
                and point.y <= self.y_max
                and point.y >= self.y_min
            ):
                return True

        return False

    def vertices(self):

        return [
            (self.x_min, self.y_min),
            (self.x_max, self.y_min),
            (self.x_min, self.y_max),
            (self.x_max, self.y_max),
        ]
