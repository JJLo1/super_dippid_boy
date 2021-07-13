#!/usr/bin/python3
# -*- coding:utf-8 -*-
"""
Template for a standard pygame project based on the information in https://www.pygame.org/docs/tut/MakeGames.html.
Created by Michael Meckl.
"""

import os
import sys
import pygame
# from pygame.compat import geterror
from pygame.locals import *  # optional, puts a set of constants and functions into the global namespace of this script

# check imports
if not pygame.font:
    print('Warning, fonts disabled')
if not pygame.mixer:
    print('Warning, sound disabled')


# 1. Define resource handling classes; define some classes to handle your most basic resources, which will be loading
# images and sounds, as well as connecting and disconnecting to and from networks, loading save game files, and any
# other resources you might have.
class GameMusic:
    def __init__(self):
        self._load_music()

    def _load_music(self, asset_folder="assets"):
        class NoneSound:
            """
            Small class instance that has a dummy play method to be used if loading the pygame sound module has failed.
            This will act enough like a normal Sound object for this game to run without any extra error checking.
            """
            def play(self): pass

        if not pygame.mixer or not pygame.mixer.get_init():
            return NoneSound()

        name = ""  # sound assets
        fullname = os.path.join(asset_folder, name)
        try:
            sound = pygame.mixer.Sound(fullname)
        except pygame.error as message:
            print('Cannot load sound:', fullname)
            raise SystemExit(message)
        return sound

    def play(self, sound):
        pass


class GameImages:
    def __init__(self):
        self._load_images()

    def _load_images(self, asset_folder="assets", color_key=None):
        name = ""  # load image assets
        fullname = os.path.join(asset_folder, name)
        try:
            image = pygame.image.load(fullname)
            if image.get_alpha() is None:
                # Convert returns us a new Surface of the image, but now converted to the same pixel format as our
                # display. Since the images will be the same format at the screen, they will blit very quickly. If we
                # did not convert, the blit() function is slower.
                image = image.convert()
            else:
                image = image.convert_alpha()
        except pygame.error as message:
            print('Cannot load image:', name)
            raise SystemExit(message)
            # raise SystemExit(str(geterror()))

        return image, image.get_rect()

    def get(self, image_name: str):
        pass


# 2. Game object classes; define the classes for your game object. In the pong example, these will be one for the
# player's bat (which you can initialise multiple times, one for each player in the game), and one for the ball
# (which can again have multiple instances). If you're going to have a nice in-game menu, it's also a good idea to
# make a menu class.
class GenericGameObject(pygame.sprite.Sprite):
    """
    add documentation here
    """

    def __init__(self):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self._setup_game_object()

    def _setup_game_object(self):
        # load sprite for this game object, etc.
        pass

    def update(self):
        # perform per-frame changes on the game object
        pass


# 3. Any other game functions; define other necessary functions, such as scoreboards, menu handling, etc. Any code that
# you could put into the main game logic, but that would make understanding said logic harder, should be put into
# its own function. So as plotting a scoreboard isn't game logic, it should be moved into a function.
def end_game():
    pygame.quit()


# 4. Initialise the game, including the pygame objects themselves, the background, the game objects (initialising
# instances of the classes) and any other little bits of code you might want to add in.
def setup_game():
    screen = pygame.display.set_mode((640, 480))
    pygame.display.set_caption('My Game')
    # pygame.mouse.set_visible(False)

    # fill background
    background = pygame.Surface(screen.get_size())
    background = background.convert()
    background.fill((250, 250, 250))  # fill background white

    return screen, background


def load_game_objects():
    game_obj = GenericGameObject()
    game_object_sprite = pygame.sprite.RenderPlain(game_obj)  # create a special render group
    return [game_object_sprite]


def show_initial_scene(screen, background):
    # Display The Background
    screen.blit(background, (0, 0))
    # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
    # have changed for them to be visible to the user. With double buffered displays the display must be swapped
    # (or flipped) for the changes to become visible
    pygame.display.flip()


# 5. The main loop, into which you put any input handling (i.e. watching for users hitting keys/mouse buttons),
# the code for updating the game objects, and finally for updating the screen.
def main():
    pygame.init()  # setup and initialize pygame
    screen, background = setup_game()
    game_objects = load_game_objects()
    show_initial_scene(screen, background)

    # setup main loop and start the game
    # Clock object used to help control our game's framerate. we will use it in the main loop of our game to make sure
    # it doesn't run too fast
    clock = pygame.time.Clock()

    going = True
    # The usual order of things in the game main loop is to check on the state of the computer and user input,
    # move and update the state of all the objects, and then draw them to the screen
    while going:
        # We also make a call to our clock object, which will make sure our game doesn't run faster than 60 frames
        # per second
        clock.tick(60)

        for event in pygame.event.get():
            if event.type == QUIT:
                going = False
            elif event.type == KEYDOWN and event.key == K_ESCAPE:
                going = False
            elif event.type == MOUSEBUTTONDOWN:
                # do sth
                pass
            elif event.type == MOUSEBUTTONUP:
                # do sth else
                pass

        # draw the current scene
        screen.blit(background, (0, 0))  # erase everything from previous frame (quite inefficient!)
        # more efficient:
        # [screen.blit(background, sprite.rect, sprite.rect) for game_object_group in game_objects for sprite
        #  in game_object_group.sprites()]

        for sprite in game_objects:
            sprite.update()
            # sprite.draw(screen)

        # Flip the contents of pygame's software double buffer to the screen.
        # This makes everything we've drawn visible all at once.
        pygame.display.flip()

    # quit the game and clean up
    end_game()


if __name__ == "__main__":
    main()
