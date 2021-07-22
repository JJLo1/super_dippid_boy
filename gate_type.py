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
        if gate_type is GateType.TRIANGLE.value:
            return "gates/triangle.png"
        elif gate_type is GateType.CIRCLE.value:
            return "gates/triangle.png"  # TODO replace with circle
        elif gate_type is GateType.LINE.value:
            return "gates/line.png"
        elif gate_type is GateType.RECTANGLE.value:
            return "gates/rectangle.png"
        else:
            print("[WARNING]: Unknown gate type! Using triangle as default.")
            return "gates/triangle.png"
