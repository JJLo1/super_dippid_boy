from enum import Enum


class GateType(Enum):
    CIRCLE = "circle"
    LINE = "line"
    RECTANGLE = "rectangle"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @staticmethod
    def get_sprite_for_gate_type(gate_type):
        # TODO load different images
        if gate_type is GateType.CIRCLE.value:
            return "portal.png"
        elif gate_type is GateType.LINE.value:
            return "portal.png"
        elif gate_type is GateType.RECTANGLE.value:
            return "portal.png"
        else:
            print("[WARNING]: Unknown gate type! Using circle as default.")
            return "portal.png"
