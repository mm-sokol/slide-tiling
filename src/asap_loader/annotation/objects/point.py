from dataclasses import dataclass
from asap_loader.annotation.objects.annotation_object import AnnotationObject


@dataclass
class Point(AnnotationObject):
    x: float
    y: float

    @property
    def label(self) -> str | None:
        return getattr(self.group, "name", None)



