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
        new_position = self.rect.move((5, 0))
        if not self.area.contains(new_position):
            if self.rect.left < self.area.left or self.rect.right > self.area.right:
                new_position = self.rect.move(self._initial_pos)

        self.rect = new_position

    def _check_collisions(self):
        pass

    def play_character_sound(self, sound_name: str):
        self.sound_handler.play_sound(sound_name)

    def jump(self):
        self.is_jumping = True
        # TODO


def end_game():
    pygame.quit()
    # sys.exit(0)


def setup_game():
    screen = pygame.display.set_mode((WIDTH, HEIGHT))  # the display mode has to be set first before the game objects!
    pygame.display.set_caption(GAME_TITLE)
    # pygame.mouse.set_visible(False)

    # setup background
    background_image, background_rect = ImageHandler.load_background_image("")
    # background = pygame.Surface(screen.get_size())
    # background = background_image.convert()
    # background.fill((250, 250, 250))  # fill background white

    # scale background to fill entire background (this does not preserve the original image dimensions!)
    w, h = screen.get_size()
    background = pygame.transform.scale(background_image, [int(w), int(h)])

    # w, h = background.get_size()
    # screen = pygame.display.set_mode((w, h))

    return screen, background


def show_initial_scene(screen, background):
    # Display The Background
    screen.blit(background, (0, 0))
    # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
    # have changed for them to be visible to the user. With double buffered displays the display must be swapped
    # (or flipped) for the changes to become visible
    pygame.display.flip()


def main():
    pygame.init()  # setup and initialize pygame
    screen, background = setup_game()
    background_width, background_height = background.get_size()

    sound_handler = SoundHandler()
    image_handler = ImageHandler()
    # sound_handler.play_sound("house_lo.wav")  # start playing background music

    slime = SlimeCharacter(image_handler, sound_handler, sprite_name="")
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
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                running = False
            elif event.type == MOUSEBUTTONDOWN:
                slime.jump()
            elif event.type == MOUSEBUTTONUP:
                # TODO
                # slime.play_character_sound("")
                pass

        # draw the current scene
        # erase everything from previous frame (quite inefficient!)
        screen.blit(background, (0, 0), (0, 10, background_width, background_height))  # cut off 10 pixels at the top
        # more efficient:
        # [screen.blit(background, sprite.rect, sprite.rect) for game_object_group in game_objects for sprite
        #  in game_object_group.sprites()]

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
