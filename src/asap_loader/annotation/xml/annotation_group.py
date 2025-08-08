from dataclasses import dataclass


@dataclass
class AnnotationGroup:
    name: str
    color: str
    group: str | None
