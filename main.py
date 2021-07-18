#!/usr/bin/python3
# -*- coding:utf-8 -*-

import random
from DIPPID import SensorUDP
from assets_loader import ImageHandler, SoundHandler
from obstacle import Obstacle, SharedObstacleState
from game_constants import *
import pygame
# pygame.locals puts a set of useful constants and functions into the global namespace of this script
from pygame.locals import (
    MOUSEBUTTONUP,
    MOUSEBUTTONDOWN,
    MOUSEMOTION,
    KEYUP,
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


def end_game(dippid_sensor):
    # stop music
    pygame.mixer.music.stop()
    pygame.mixer.quit()

    pygame.quit()

    # TODO finish dippid device as well
    dippid_sensor.disconnect()
    # sys.exit(0)


def setup_game():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))   # setup the game window
    pygame.display.set_caption(GAME_TITLE)

    # setup background
    background_image, background_rect = ImageHandler.load_background_image()
    # scale the background image to fill the entire background
    w, h = screen.get_size()
    background = pygame.transform.smoothscale(background_image, [int(w), int(h)])

    return screen, background, background_rect


def show_initial_scene(screen, background):
    # Display the background
    screen.blit(background, (0, 0))
    # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
    # have changed for them to be visible to the user. With double buffered displays the display must be swapped
    # (or flipped) for the changes to become visible
    pygame.display.flip()


"""
    def set_custom_filter(self, point_filter):
        self.custom_filter = point_filter

    def get_current_points(self):
        return self.points

    def reset_current_points(self):
        self.points = []
"""


def draw_gesture(surface, points):
    # pygame.draw.aalines(surface, (255, 0, 0), closed=False, points=points, blend=1)  # anti-aliased lines
    pygame.draw.lines(surface, (255, 0, 0), closed=False, points=points, width=3)


# TODO this main method is far too long -> extract most of it to a main class, e.g. "Game", as in the Praxisseminar
def main():
    dippid = SensorUDP(5700)  # TODO port should be given as argument to program and error handling + start screen

    pygame.init()  # setup and initialize pygame
    screen, background, background_rect = setup_game()
    background_width, background_height = background.get_size()
    background_area = (0, 10, background_width, background_height)  # cut off 10 pixels at the top of the background

    sound_handler = SoundHandler()
    image_handler = ImageHandler()
    # TODO make sure the transition at the end when replaying is smooth!
    sound_handler.play_sound("mysterious_harp.mp3", play_infinite=True)  # start playing background music

    main_character = SlimeCharacter(image_handler, sound_handler, graphics_folder="graphics/triangle")
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

    UPDATE_SCORE_EVENT = pygame.USEREVENT + 3
    pygame.time.set_timer(UPDATE_SCORE_EVENT, 1000)  # update score each second

    # HIDE_GESTURE_EVENT = pygame.USEREVENT + 4

    # Clock object used to help control the game's framerate. Used in the main loop to make sure the game doesn't run
    # too fast
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 25)
    current_points = 0

    show_initial_scene(screen, background)

    is_drawing = False
    show_gesture = False
    gesture_points = []

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
            elif event.type == KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    main_character.change_movement(angle=0)
            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    print("You pressed the left mouse button")
                    # started drawing gesture
                    is_drawing = True
                    show_gesture = True
                    gesture_points = []  # reset the points
                elif event.button == 3:
                    print("You pressed the right mouse button")
            elif event.type == MOUSEBUTTONUP:
                # gesture finished
                if event.button == 1:  # if the left mouse button was released
                    is_drawing = False
                    show_gesture = False
                    # draw_gesture(screen, gesture_points)  # too early to show gesture
            elif event.type == MOUSEMOTION:
                if is_drawing:
                    gesture_points.append((pygame.mouse.get_pos()))
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

            elif event.type == UPDATE_SCORE_EVENT:
                current_points += 5
            """
            elif event.type == HIDE_GESTURE_EVENT:
                show_gesture = False
                pygame.time.set_timer(HIDE_GESTURE_EVENT, 0)  # stop timer
            """

        main_character.change_movement(angle=dippid.get_value('gravity')['x'])
        """
        # alternative:
        if dippid.get_value('gravity')['y'] > 1:
            main_character.change_movement(angle=5)
        elif dippid.get_value('gravity')['y'] < -1:
            main_character.change_movement(angle=-5)
        else:
            main_character.change_movement(angle=0)
        """

        keys = pygame.key.get_pressed()  # checking pressed keys
        if keys[pygame.K_w]:
            main_character.change_movement(angle=10)
        elif keys[pygame.K_s]:
            main_character.change_movement(angle=-10)

        # draw background (erases everything from previous frame (TODO quite inefficient!))
        screen.blit(background, background_rect, area=background_area)

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

        if show_gesture and len(gesture_points) > 2:  # we need at least two points to draw a line
            draw_gesture(screen, gesture_points)
            # pygame.time.set_timer(HIDE_GESTURE_EVENT, 500)  # hide gesture after 500 ms

        main_character.update()
        screen.blit(main_character.image, main_character.rect)

        text_surface = font.render(f"Score: {current_points}", True, (255, 0, 0))
        screen.blit(text_surface, (SCREEN_WIDTH // 2 - 50, 15))

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
            current_points -= 20  # FIXME this is executed 60 times per second

        # Flip the contents of pygame's software double buffer to the screen.
        # This makes everything we've drawn visible all at once.
        pygame.display.flip()

    # quit the game and clean up after the main loop finished
    end_game(dippid)


if __name__ == "__main__":
    main()
