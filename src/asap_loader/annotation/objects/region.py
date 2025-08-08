from dataclasses import dataclass, field
from asap_loader.annotation.objects.point import Point
from asap_loader.annotation.objects.rectangle import Rectangle


@dataclass
class Region(Rectangle):
    members: list[Point] = field(default_factory=list)

    def add(self, member: Point):
        if member in self:
            self.members.append(member)

    def __contains__(self, point: Point) -> bool:
        return (
            self.x_min <= point.x <= self.x_max and self.y_min <= point.y <= self.y_max
        )
