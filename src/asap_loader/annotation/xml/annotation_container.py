from asap_loader.annotation.xml.annotation import Annotation
from asap_loader.annotation.xml.annotation_group import AnnotationGroup
from asap_loader.annotation.xml.coordinate import Coordinate


class AnnotationContainer:
    def __init__(self) -> None:
        self.stack: list[str] = []
        self.annotations: list[Annotation] = []
        self.annotation_groups: list[AnnotationGroup] = []

    def start(self, tag: str, attrib: dict[str, str]) -> None:
        match tag:
            case "Annotation":
                assert (
                    self.stack[-1] == "Annotations"
                ), "Annotation outside annotations container"

                self.annotations.append(
                    Annotation(
                        annotation_type=attrib["Type"],
                        name=attrib["Name"],
                        color=attrib["Color"],
                        group=(
                            None
                            if attrib["PartOfGroup"] == "None"
                            else attrib["PartOfGroup"]
                        ),
                    )
                )
            case "Coordinate":
                assert (
                    self.stack[-1] == "Coordinates"
                ), "Coordinate outside coordinates container"

                self.annotations[-1].add_coordinate(
                    Coordinate(
                        order=int(attrib["Order"]),
                        x=float(attrib["X"]),
                        y=float(attrib["Y"]),
                    )
                )
            case "Group":
                self.annotation_groups.append(
                    AnnotationGroup(
                        name=attrib["Name"],
                        color=attrib["Color"],
                        group=(
                            None
                            if attrib["PartOfGroup"] == "None"
                            else attrib["PartOfGroup"]
                        ),
                    )
                )

        self.stack.append(tag)

    def end(self, tag):
        assert (
            self.stack.pop() == tag
        ), "Element in stack doesn't match the processed tag"

    def data(self, data):
        pass

    def close(self):
        pass
