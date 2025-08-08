from asap_loader.annotation.xml.coordinate import Coordinate


class Annotation:
    def __init__(
        self,
        annotation_type: str,
        name: str,
        color: str,
        group: str | None,
    ):
        super().__init__()

        self.type = annotation_type
        self.name = name
        self.color = color
        self.group = group
        self.coordinates: list[Coordinate] = []

    def add_coordinate(self, coord: Coordinate) -> None:
        self.coordinates.append(coord)
