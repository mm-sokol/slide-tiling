from dataclasses import dataclass, field
from asap_loader.annotation.objects.annotation_object import AnnotationObject


@dataclass
class Group(AnnotationObject):
    members: list[AnnotationObject] = field(default_factory=list)

    def add(self, member: AnnotationObject):
        self.members.append(member)
