#!/usr/bin/python3
# -*- coding:utf-8 -*-

import random
from assets_loader import ImageHandler, SoundHandler
from obstacle import Obstacle, SharedObstacleState
from game_constants import *
import pygame
# pygame.locals puts a set of useful constants and functions into the global namespace of this script
from pygame.locals import (
    MOUSEBUTTONUP,
    MOUSEBUTTONDOWN,
    KEYUP,
    K_w,
    K_s,
    K_ESCAPE,
    KEYDOWN,
    QUIT,
)

# check imports
if not pygame.font:
    raise SystemExit("[Error]: Pygame Fonts disabled")
if not pygame.mixer:
    raise SystemExit("[Error]: Pygame Sound disabled")


vec = pygame.math.Vector2
random.seed(42)  # set a random seed to make the game deterministic while testing


# TODO move to own file, e.g. "player.py" / "main_character.py"
class SlimeCharacter(pygame.sprite.Sprite):
    """
    The main character of the game.
    """

    def __init__(self, image_handler, sound_handler, sprite_name):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.sound_handler = sound_handler
        self.image, self.rect = image_handler.get_image(sprite_name)  # load the sprite for this game object
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
        self._move()

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
        if angle > 5:
            self._set_movement((0, -5))  # go up (negative as the y-axis is inverted!)
        elif angle > 0:
            self._set_movement((0, -1))
        elif angle == 0:
            self._set_movement((0, 0))
        elif angle < -5:
            self._set_movement((0, 5))
        elif angle < 0:
            self._set_movement((0, 1))


def end_game():
    # stop music
    pygame.mixer.music.stop()
    pygame.mixer.quit()

    pygame.quit()


def setup_game():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))   # setup the game window
    pygame.display.set_caption(GAME_TITLE)

    # setup background
    background_image, background_rect = ImageHandler.load_background_image()
    # scale the background image to fill the entire background
    w, h = screen.get_size()
    background = pygame.transform.smoothscale(background_image, [int(w), int(h)])

    """
    top_border_block = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)  # pygame.SRCALPHA makes it transparent
    top_border_rect = top_border_block.get_rect(topleft=(0, 0))

    bottom_border_block = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)
    bottom_border_rect = bottom_border_block.get_rect(bottomleft=(0, SCREEN_HEIGHT))
    """
    return screen, background, background_rect  # , top_border_rect, bottom_border_rect


def show_initial_scene(screen, background):
    # Display the background
    screen.blit(background, (0, 0))
    # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
    # have changed for them to be visible to the user. With double buffered displays the display must be swapped
    # (or flipped) for the changes to become visible
    pygame.display.flip()


# TODO this main method is far too long -> extract most of it to a main class, e.g. "Game", as in the Praxisseminar
def main():
    pygame.init()  # setup and initialize pygame
    screen, background, background_rect = setup_game()
    background_width, background_height = background.get_size()
    background_area = (0, 10, background_width, background_height)  # cut off 10 pixels at the top of the background

    sound_handler = SoundHandler()
    image_handler = ImageHandler()
    # TODO make sure the transition at the end when replaying is smooth!
    sound_handler.play_sound("mysterious_harp.mp3", play_infinite=True)  # start playing background music

    main_character = SlimeCharacter(image_handler, sound_handler, sprite_name="slime.png")
    obstacles = pygame.sprite.Group()  # for rendering all obstacles
    wall_collidables = pygame.sprite.Group()  # for collision detection
    gate_collidables = pygame.sprite.Group()

    # create an event timer that fires an event each time the specified amount in milliseconds passes,
    # see https://stackoverflow.com/questions/18948981/do-something-every-x-milliseconds-in-pygame
    interval_time = 3000  # random.randrange(2500, 4500)  # every 2.5 until 4.5 seconds
    SPAWN_OBSTACLE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, interval_time)

    # create event to increase the game speed over time
    INCREASE_SPEED_EVENT = pygame.USEREVENT + 2
    pygame.time.set_timer(INCREASE_SPEED_EVENT, 10000)  # increase speed every 10 seconds

    # Clock object used to help control the game's framerate. Used in the main loop to make sure the game doesn't run
    # too fast
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 25)  # TODO show the current point score on the screen
    fps_text_pos = (20, 20)

    show_initial_scene(screen, background)

    background_movement_speed = 1.5
    running = True
    # main game loop
    while running:
        # make sure the game doesn't run faster than the defined frames per second
        clock.tick(FPS)
        current_fps = clock.get_fps()
        text = font.render(f"Current FPS: {current_fps}", True, (255, 0, 0))  # TODO only for testing

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                elif event.key == K_w:
                    main_character.change_movement(angle=2)
                elif event.key == K_s:
                    main_character.change_movement(angle=-2)
            elif event.type == KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    main_character.change_movement(angle=0)
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
            elif event.type == INCREASE_SPEED_EVENT:
                # increase the movement speed of the obstacles
                SharedObstacleState.increase_move_speed()
                # and decrease the spawn time of the next obstacles  # TODO maybe this is too hard?
                interval_time -= 30
                pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, interval_time)

            elif event.type == SPAWN_OBSTACLE_EVENT:
                # create a new obstacle to the right of the current screen whenever our custom event is sent
                new_obstacle = Obstacle(SCREEN_WIDTH + 20, image_handler)
                obstacles.add(new_obstacle)
                wall_collidables.add(*new_obstacle.walls)
                gate_collidables.add(*new_obstacle.gates)

                background.blit(text, fps_text_pos)

        keys = pygame.key.get_pressed()  # checking pressed keys
        if keys[pygame.K_w]:
            main_character.change_movement(angle=10)
        elif keys[pygame.K_s]:
            main_character.change_movement(angle=-10)

        # draw background (erases everything from previous frame (quite inefficient!))
        screen.blit(background, background_rect, area=background_area)
        # more efficient:
        # [screen.blit(background, sprite.rect, sprite.rect) for game_object_group in game_objects for sprite
        #  in game_object_group.sprites()]

        # Implement a scrolling background, see https://stackoverflow.com/questions/51320007/side-scrolling-background
        # the new position of the upcoming background is calculated by simply moving the rect by the width of the image
        # upcoming image is the same as the current one, just offset to the right
        upcoming_background = background_rect.move(background_rect.width, 0)
        screen.blit(background, upcoming_background, area=background_area)

        # move the background position rect to get a scrolling background
        background_rect.move_ip(-background_movement_speed, 0)

        # it the right edge of the "left" image is zero, that means it's fully out of view
        if background_rect.right == 0:
            # so reset the rect and start over
            background_rect.x = 0

        # draw top and bottom border blocks  # TODO quite ugly at the moment
        pygame.draw.rect(screen, (24, 61, 87), (0, 0, SCREEN_WIDTH, 49))
        pygame.draw.rect(screen, (74, 59, 43), (0, SCREEN_HEIGHT-49, SCREEN_WIDTH, 50))

        obstacles.update()
        obstacles.draw(screen)

        # print(f"Number of obstacles: {len(obstacles)}")
        # print(f"Number of walls: {len(wall_collidables)}")

        main_character.update()
        screen.blit(main_character.image, main_character.rect)

        # Check if any obstacles have collided with the player
        if pygame.sprite.spritecollideany(main_character, wall_collidables):
            # If so, then remove the player and stop the loop
            print("Player collided with wall! Game over!")
            main_character.kill()
            running = False
            # TODO show 'You Died' - Message :)

        # if pygame.sprite.spritecollideany(main_character, gate_collidables, check_gate_collision):

        gate_sprite = pygame.sprite.spritecollideany(main_character, gate_collidables)
        if gate_sprite and main_character.get_current_form() is not gate_sprite.get_gate_type():
            print("Gate type:", gate_sprite.get_gate_type())  # linter warning is wrong here, just ignore it
            print("Current player form does not match gate type! Point deduction!")
            # main_character.kill()  # TODO maybe don't kill when wrong form but only decrease points ?
            # running = False

        # Flip the contents of pygame's software double buffer to the screen.
        # This makes everything we've drawn visible all at once.
        pygame.display.flip()
        # pygame.display.update(...)  # can be used instead to update only a part of the display

    # quit the game and clean up after the main loop finished
    end_game()


if __name__ == "__main__":
    main()
