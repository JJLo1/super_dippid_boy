from game_constants import SCREEN_WIDTH, SCREEN_HEIGHT


def get_screen_center_for_surface(surface_rect):
    # Put the center of surface at the center of the display (shifting the surface first is necessary as pygame always
    # uses the top-left corner of the rect)
    surface_center = (
        (SCREEN_WIDTH - surface_rect.get_width()) / 2,
        (SCREEN_HEIGHT - surface_rect.get_height()) / 2
    )
    return surface_center


def check_gate_collision(player, gate):
    # print("Player Rect: ", player.rect)
    # print("Gate Rect: ", gate.rect)

    # if gate.rect.left <= player.rect.x <= gate.rect.right:
    if gate.rect.left == player.rect.x:  # only check once when x positions are equal
        if gate.rect.top <= player.rect.y <= gate.rect.bottom:
            if gate.get_gate_type() is not player.get_current_form():
                # they collide only if the player's current form does not match the gate type
                return True
    return False
