import sys
import pygame
from assets_loader import ImageHandler
from game_settings import *
from gate_type import GateType


class PlayerCharacter(pygame.sprite.Sprite):
    """
    The main character of the game.
    """

    def __init__(self, image_handler, sound_handler, graphics_folder):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer

        self.sound_handler = sound_handler
        self.image_handler = image_handler
        # load all sprites for the character
        self.character_images = ImageHandler.get_images_from_directory(graphics_folder)
        self.original_image = self.character_images[0]
        self.rect = self.original_image.get_rect()
        self.image = self.original_image

        self.movement_x = 0.0
        self.movement_y = 0.0
        self.rot = 0
        self.current_image_index = 0
        self.current_frag = 0

        self.__current_form = GateType.TRIANGLE.value
        self._set_initial_position()

    def _set_initial_position(self):
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        self._initial_pos = (self.area.left + 100, self.area.bottom / 2)
        self.rect.topleft = self._initial_pos

    def update(self):
        # perform per-frame changes on the game object
        self._animate_character()
        self._move()
        self._update_rotation()

    def _animate_character(self):
        self.current_frag = self.current_frag+1
        if self.current_frag == 15:
            if self.current_image_index >= len(self.character_images)-1:
                self.current_image_index = 0
            self.current_image_index += 1
            self.current_frag = 0
        self.image = self.character_images[self.current_image_index]

    def _update_rotation(self):
        self.rot = (self.rect.bottom / self.area.bottom)*180+180  # bei 0 = 1 bei self.area.bottom = -1 self.bottom/2 0
        new_image = pygame.transform.rotate(self.image, self.rot)
        new_rect = new_image.get_rect(center=self.image.get_rect(center=self.rect.center).center)
        self.image, self.rect = (new_image, new_rect)

    def _move(self):
        self.rect.move_ip((self.movement_x, self.movement_y))  # 'ip' makes the changes happen 'in-place'
        # make sure that the character cannot leave the game window
        self.rect.clamp_ip((0, 50, SCREEN_WIDTH, SCREEN_HEIGHT - 100))  # TODO magic numbers

    def get_current_form(self):
        print(f"Returning current player form: {self.__current_form}")
        return self.__current_form

    def set_current_form(self, form):
        sys.stderr.write(f"new player form: {form}")
        self.__current_form = form

    def _set_movement(self, new_movement):
        self.movement_x, self.movement_y = new_movement

    def change_movement(self, angle):
        self._set_movement((0, angle))