import abc
from typing import Optional, TYPE_CHECKING
from dataclasses import dataclass

if TYPE_CHECKING:
    from asap_loader.annotation.objects.group import Group


@dataclass
class AnnotationObject(abc.ABC):
    name: str
    color: str
    group: Optional["Group"]

    def __post_init__(self) -> None:
        if self.group:
            self.group.add(self)

    # def __str__(self):
    #     return f"name={self.name}, color={self.color}, group={self.group}"
