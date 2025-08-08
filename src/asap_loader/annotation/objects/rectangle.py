from dataclasses import dataclass

from asap_loader.annotation.objects.annotation_object import AnnotationObject


@dataclass
class Rectangle(AnnotationObject):
    x_min: float
    x_max: float
    y_min: float
    y_max: float
