from enum import Enum


class GateType(Enum):
    # these names must be the same as the ones used for the gestures in gestures.json
    TRIANGLE = "triangle"
    CIRCLE = "circle"
    LINE = "line"
    RECTANGLE = "rectangle"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @staticmethod
    def get_sprite_for_gate_type(gate_type):
        # TODO load different images
        if gate_type is GateType.TRIANGLE.value:
            return "triangle.png"
        elif gate_type is GateType.CIRCLE.value:
            return "portal.png"
        elif gate_type is GateType.LINE.value:
            return "line.png"
        elif gate_type is GateType.RECTANGLE.value:
            return "rectangle.png"
        else:
            print("[WARNING]: Unknown gate type! Using circle as default.")
            return "portal.png"
