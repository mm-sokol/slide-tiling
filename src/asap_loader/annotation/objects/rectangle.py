from dataclasses import dataclass

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
