import pygame
from assets_loader import ImageHandler
from game_settings import *


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
        if self.current_image_index > len(self.character_images)-1:
            self.current_image_index = 0
        self.image = self.character_images[self.current_image_index]
        self.current_image_index += 1

    def _update_rotation(self):
        self.rot = (self.rect.bottom / self.area.bottom)*180+180  # bei 0 = 1 bei self.area.bottom = -1 self.bottom/2 0
        new_image = pygame.transform.rotate(self.image, self.rot)
        new_rect = self.rect.copy()
        
        new_rect.center = self.rect.center
        self.image, self.rect = (new_image, new_rect)

    def _move(self):
        self.rect.move_ip((self.movement_x, self.movement_y))  # 'ip' makes the changes happen 'in-place'
        """
        if self.rect.left < 0:
            self.rect.left = 0
        if self.rect.right > SCREEN_WIDTH:
            self.rect.right = SCREEN_WIDTH
        if self.rect.top <= 0:
            self.rect.top = 0
        if self.rect.bottom >= SCREEN_HEIGHT:
            self.rect.bottom = SCREEN_HEIGHT
        """
        # make sure that the character cannot leave the game window
        self.rect.clamp_ip((0, 50, SCREEN_WIDTH, SCREEN_HEIGHT - 100))  # TODO magic numbers

    def play_character_sound(self, sound_name: str):
        self.sound_handler.play_sound(sound_name)

    def get_current_form(self):
        pass

    def _set_movement(self, new_movement):
        self.movement_x, self.movement_y = new_movement

    def change_movement(self, angle):
        self._set_movement((0, angle))