#!/usr/bin/python3
# -*- coding:utf-8 -*-

import pygame
from pygame.locals import *  # optional, puts a set of constants and functions into the global namespace of this script
from assets_loader import ImageHandler, SoundHandler

# check imports
if not pygame.font:
    print('Warning, fonts disabled')
if not pygame.mixer:
    print('Warning, sound disabled')


# global game constants
GAME_TITLE = 'Super-DIPPID-Boy'
WIDTH, HEIGHT = 960, 640
FPS = 60


class SlimeCharacter(pygame.sprite.Sprite):
    """
    The main character of the game.
    """

    def __init__(self, image_handler, sound_handler, sprite_name):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer

        self.sound_handler = sound_handler
        self.image, self.rect = image_handler.get_image(sprite_name)  # load the sprite for this game object
        self.is_jumping = False
        self.movement_x = 0.0
        self.movement_y = 0.0

        self._set_initial_position()

    def _set_initial_position(self):
        screen = pygame.display.get_surface()
        self.area = screen.get_rect()
        # self.image = pygame.transform.rotate(self.image, 180)
        self._initial_pos = (self.area.left + 25, self.area.bottom - 100)
        self.rect.topleft = self._initial_pos

    def update(self):
        # perform per-frame changes on the game object
        # TODO if not self.is_jumping:
        self._move()
        self._check_collisions()

    def _move(self):
        new_position = self.rect.move((self.movement_x, self.movement_y))
        if not self.area.contains(new_position):
            if self.rect.left < self.area.left or self.rect.right > self.area.right:
                self.movement_x *= -1  # invert movement
                new_position = self.rect.move((self.movement_x, self.movement_y))

        self.rect = new_position

    def _check_collisions(self):
        pass

    def play_character_sound(self, sound_name: str):
        self.sound_handler.play_sound(sound_name)

    def _set_movement(self, new_movement):
        self.movement_x, self.movement_y = new_movement

    def change_movement(self, angle):
        if angle > 5:
            self._set_movement((1, -3))  # go up (negative as the y-axis is inverted!)
        elif angle > 0:
            self._set_movement((0, -1))
        elif angle == 0:
            self._set_movement((0, 0))
        elif angle < -5:
            self._set_movement((1, 3))
        elif angle < 0:
            self._set_movement((0, 1))


def end_game():
    pygame.quit()
    # sys.exit(0)


def setup_game():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))  # the display mode has to be set first before the game objects!
    pygame.display.set_caption(GAME_TITLE)
    # pygame.mouse.set_visible(False)

    # setup background
    background_image, background_rect = ImageHandler.load_background_image("forest_background.png")
    # scale background to fill entire background (this does not preserve the original image dimensions!)
    w, h = screen.get_size()
    background = pygame.transform.scale(background_image, [int(w), int(h)])

    return screen, background, background_rect


def show_initial_scene(screen, background):
    # Display The Background
    screen.blit(background, (0, 0))
    # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
    # have changed for them to be visible to the user. With double buffered displays the display must be swapped
    # (or flipped) for the changes to become visible
    pygame.display.flip()


def main():
    pygame.init()  # setup and initialize pygame
    screen, background, background_rect = setup_game()
    background_width, background_height = background.get_size()
    background_area = (0, 10, background_width, background_height)  # cut off 10 pixels at the top of the background

    sound_handler = SoundHandler()
    image_handler = ImageHandler()
    # TODO make sure the transition at the end when replaying is smooth!
    sound_handler.play_sound("mysterious_harp.mp3", play_infinite=True)  # start playing background music

    slime = SlimeCharacter(image_handler, sound_handler, sprite_name="slime.png")
    game_object_sprite = pygame.sprite.RenderPlain(slime)
    game_objects = [game_object_sprite]

    show_initial_scene(screen, background)

    # Clock object used to help control the game's framerate. Used in the main loop to make sure the game doesn't run
    # too fast
    clock = pygame.time.Clock()

    running = True
    # The usual order of things in the game main loop is to check on the state of the computer and user input,
    # move and update the state of all the objects, and then draw them to the screen
    while running:
        # make sure the game doesn't run faster than the defined frames per second
        clock.tick(FPS)

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_w:
                    slime.change_movement(angle=2)
                elif event.key == K_s:
                    slime.change_movement(angle=-2)
            elif event.type == KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    slime.change_movement(angle=0)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    print("You pressed the left mouse button")
                    # TODO start drawing gesture
                elif event.button == 3:
                    print("You pressed the right mouse button")

                pos = pygame.mouse.get_pos()
                print("Clicked at ", pos)
            elif event.type == MOUSEBUTTONUP:
                # TODO gesture finished
                pass

        keys = pygame.key.get_pressed()  # checking pressed keys
        if keys[pygame.K_w]:
            slime.change_movement(angle=10)
        elif keys[pygame.K_s]:
            slime.change_movement(angle=-10)

        # draw background and  (erases everything from previous frame (quite inefficient!))
        screen.blit(background, background_rect, area=background_area)
        # more efficient:
        # [screen.blit(background, sprite.rect, sprite.rect) for game_object_group in game_objects for sprite
        #  in game_object_group.sprites()]

        # the new position of the upcoming background is calculated by simply moving the rect by the width of the image
        # upcoming image is the same as the current one, just offset to the right
        upcoming_background = background_rect.move(background_rect.width, 0)
        screen.blit(background, upcoming_background, area=background_area)

        # move the background position rect to get a scrolling background
        background_rect.move_ip(-1.5, 0)

        # it the right edge of the "left" image is zero, that means it's fully out of view
        if background_rect.right == 0:
            # so reset the rect and start over
            background_rect.x = 0

        for sprite in game_objects:
            sprite.update()
            sprite.draw(screen)

        # Flip the contents of pygame's software double buffer to the screen.
        # This makes everything we've drawn visible all at once.
        pygame.display.flip()

    # quit the game and clean up after the main loop finished
    end_game()


if __name__ == "__main__":
    main()
