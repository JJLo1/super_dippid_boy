#!/usr/bin/python3
# -*- coding:utf-8 -*-

import random
from DIPPID import SensorUDP
from assets_loader import SoundHandler, ImageHandler
from game_settings import GAME_TITLE, SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game_utils import draw_gesture
from obstacle import Obstacle, SharedObstacleState
from gesture_recognizer.dollar_one_recognizer import DollarOneRecognizer
from player_character import PlayerCharacter
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


random.seed(42)  # set a random seed to make the game deterministic while testing


# noinspection PyAttributeOutsideInit
class SuperDippidBoy:

    def __init__(self, dippid_port=5700):
        # init dippid  # TODO error handling
        self.dippid_sensor = SensorUDP(dippid_port)

        # init gesture recognizer
        self.gesture_recognizer = DollarOneRecognizer()
        # setup the pygame window
        self.setup_game_window()
        # and resource handlers
        self.sound_handler = SoundHandler()
        self.image_handler = ImageHandler()

    def setup_game_window(self):
        # setup the pygame window
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)

        # setup background
        background_image, self.background_rect = ImageHandler.load_background_image()
        # scale the background image to fill the entire background
        w, h = self.screen.get_size()
        self.background = pygame.transform.smoothscale(background_image, [int(w), int(h)])
        self.background_width, self.background_height = self.background.get_size()
        # cut off 10 pixels at the top of the background so it looks a bit better
        self.background_area = (0, 10, self.background_width, self.background_height)

    def draw_background(self):
        # Display the background
        self.screen.blit(self.background, (0, 0))
        # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
        # have changed for them to be visible to the user. With double buffered displays the display must be swapped
        # (or flipped) for the changes to become visible:
        pygame.display.flip()

    def show_start_screen(self):
        self.draw_background()
        # TODO show menu

        self.start_game()

    def start_game(self):
        # TODO make sure the transition at the end when replaying is smooth!
        self.sound_handler.play_sound("mysterious_harp.mp3", play_infinite=True)  # start playing background music

        self.main_character = PlayerCharacter(self.image_handler, self.sound_handler, graphics_folder="assets/Triangle")
        self.obstacles = pygame.sprite.Group()  # for rendering all obstacles
        self.wall_collidables = pygame.sprite.Group()  # for collision detection
        self.gate_collidables = pygame.sprite.Group()

        self.font = pygame.font.Font(None, 25)
        self.current_points = 0

        self.background_movement_speed = 1.5
        # Clock object used to help control the game's framerate. Used in the main loop to make sure the game doesn't
        # run too fast
        self.clock = pygame.time.Clock()

        self.create_custom_events()
        self.run_game_loop()

    def create_custom_events(self):
        # create an event timer that fires an event each time the specified amount in milliseconds passes,
        # see https://stackoverflow.com/questions/18948981/do-something-every-x-milliseconds-in-pygame
        self.interval_time = 3000  # random.randrange(2500, 4500)  # every 2.5 until 4.5 seconds
        self.SPAWN_OBSTACLE_EVENT = pygame.USEREVENT + 1
        pygame.time.set_timer(self.SPAWN_OBSTACLE_EVENT, self.interval_time)

        # create event to increase the game speed over time
        self.INCREASE_SPEED_EVENT = pygame.USEREVENT + 2
        pygame.time.set_timer(self.INCREASE_SPEED_EVENT, 10000)  # increase speed every 10 seconds

        self.UPDATE_SCORE_EVENT = pygame.USEREVENT + 3
        pygame.time.set_timer(self.UPDATE_SCORE_EVENT, 1000)  # update score each second

    def run_game_loop(self):
        """
        Main game loop
        """
        self.draw_background()

        self.is_drawing = False
        self.show_gesture = False
        self.gesture_points = []

        self.is_running = True
        while self.is_running:
            # make sure the game doesn't run faster than the defined frames per second
            self.clock.tick(FPS)
            # current_fps = self.clock.get_fps()
            # print(f"Current FPS: {current_fps}")

            self.handle_events()

            self.check_player_movement()
            self.move_background()
            self.update_game_objects()

            # TODO show gesture on separate thread so main loop time isn't blocked by this?
            if self.show_gesture and len(self.gesture_points) > 2:  # we need at least two points to draw a line
                draw_gesture(self.screen, self.gesture_points)
                # pygame.time.set_timer(HIDE_GESTURE_EVENT, 500)  # hide gesture after 500 ms

            self.update_score()
            self.check_collisions()

            # Flip the contents of pygame's software double buffer to the screen.
            # This makes everything we've drawn visible all at once.
            pygame.display.flip()

        # quit the game and clean up after the main loop finished
        self.end_game()

    def handle_events(self):
        # react to pygame events
        for event in pygame.event.get():
            if event.type == QUIT:
                self.is_running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.is_running = False

            elif event.type == KEYUP:
                if event.key == pygame.K_w or event.key == pygame.K_s:
                    self.main_character.change_movement(angle=0)  # TODO for debugging only

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    print("Left mouse button pressed")
                    # started drawing gesture
                    self.is_drawing = True
                    self.show_gesture = True
                    self.gesture_points = []  # reset the points
                elif event.button == 3:
                    print("Right mouse button pressed")

            elif event.type == MOUSEBUTTONUP:
                # gesture finished
                if event.button == 1:  # if the left mouse button was released
                    self.is_drawing = False
                    self.show_gesture = False
                    predicted_gesture = self.gesture_recognizer.predict_gesture(self.gesture_points)
                    # print(f"\n########Predicted gesture in main: {predicted_gesture}\n#########\n")
                    self.main_character.set_current_form(predicted_gesture)

            elif event.type == MOUSEMOTION:
                if self.is_drawing:
                    self.gesture_points.append((pygame.mouse.get_pos()))

            elif event.type == self.INCREASE_SPEED_EVENT:
                # increase the movement speed of the obstacles
                SharedObstacleState.increase_move_speed()
                # and decrease the spawn time of the next obstacles  # TODO maybe this is too hard?
                self.interval_time -= 30
                pygame.time.set_timer(self.SPAWN_OBSTACLE_EVENT, self.interval_time)

            elif event.type == self.SPAWN_OBSTACLE_EVENT:
                # create a new obstacle to the right of the current screen whenever our custom event is sent
                new_obstacle = Obstacle(SCREEN_WIDTH + 20, self.image_handler)
                self.obstacles.add(new_obstacle)
                self.wall_collidables.add(*new_obstacle.walls)
                self.gate_collidables.add(*new_obstacle.gates)

            elif event.type == self.UPDATE_SCORE_EVENT:
                self.current_points += 5

    def check_player_movement(self):
        if "gravity" in self.dippid_sensor.get_capabilities():
            self.main_character.change_movement(angle=self.dippid_sensor.get_value('gravity')['x'])
        # TODO: check if "angle" is bugged on m5stack, since the values seemed strange
        elif "angle" in self.dippid_sensor.get_capabilities():
            self.main_character.change_movement(angle=self.dippid_sensor.get_value('angle')['x'])
        """
        # alternative:
        if self.dippid_sensor.get_value('gravity')['y'] > 1:
            self.main_character.change_movement(angle=5)
        elif dippid.get_value('gravity')['y'] < -1:
            self.main_character.change_movement(angle=-5)
        else:
            self.main_character.change_movement(angle=0)
        """

        # TODO only for easier debugging:
        keys = pygame.key.get_pressed()  # checking pressed keys
        if keys[pygame.K_w]:
            self.main_character.change_movement(angle=-10)
        elif keys[pygame.K_s]:
            self.main_character.change_movement(angle=10)

    def move_background(self):
        # draw background (erases everything from previous frame; quite inefficient but works for now)
        self.screen.blit(self.background, self.background_rect, area=self.background_area)

        # Implement a scrolling background,
        # see https://stackoverflow.com/questions/51320007/side-scrolling-background
        # The new position of the upcoming background is calculated by moving the rect by the width of the image.
        # Upcoming image is the same as the current one, just offset to the right.
        upcoming_background = self.background_rect.move(self.background_rect.width, 0)
        self.screen.blit(self.background, upcoming_background, area=self.background_area)

        # move the background position rect to get a scrolling background
        self.background_rect.move_ip(-self.background_movement_speed, 0)

        # it the right edge of the "left" image is zero, that means it's fully out of view
        if self.background_rect.right == 0:
            # so reset the rect and start over
            self.background_rect.x = 0

    def update_game_objects(self):
        # draw top and bottom border blocks  # TODO quite ugly at the moment
        pygame.draw.rect(self.screen, (24, 61, 87), (0, 0, SCREEN_WIDTH, 49))
        pygame.draw.rect(self.screen, (74, 59, 43), (0, SCREEN_HEIGHT - 49, SCREEN_WIDTH, 50))

        # update obstacles
        self.obstacles.update()
        self.obstacles.draw(self.screen)

        # update the main character
        self.main_character.update()
        self.screen.blit(self.main_character.image, self.main_character.rect)
        # TODO debug: show hitbox of player character
        hitbox = (self.main_character.rect.x, self.main_character.rect.y, self.main_character.rect.width,
                  self.main_character.rect.height)
        pygame.draw.rect(self.screen, (255, 0, 0), hitbox, 2)

    def update_score(self):
        text_surface = self.font.render(f"Score: {self.current_points}", True, (255, 0, 0))
        self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - 50, 15))  # center score at the top

    def check_collisions(self):
        # Check if any obstacles have collided with the player
        if pygame.sprite.spritecollideany(self.main_character, self.wall_collidables):
            # If so, then remove the player and stop the loop
            print("Player collided with wall! Game over!")
            self.main_character.kill()
            self.is_running = False
            # TODO show 'You Died' - Message :)

        # if pygame.sprite.spritecollideany(main_character, self.gate_collidables, check_gate_collision):

        gate_sprite = pygame.sprite.spritecollideany(self.main_character, self.gate_collidables)
        if gate_sprite:
            curr_form = self.main_character.get_current_form()
            gate_form = gate_sprite.get_gate_type()
            if curr_form == gate_form:
                self.current_points += 20
            else:
                print("Gate type:", gate_sprite.get_gate_type())  # linter warning is wrong here, just ignore it
                print("Current player form does not match gate type! Point deduction!")
                self.current_points -= 20  # FIXME this is executed 60 times per second  -> change collision detection
                # to x_pos and right edge of player only?

    def end_game(self):
        # stop music
        pygame.mixer.music.stop()
        pygame.mixer.quit()

        # stop dippid sensor
        # TODO check that dippid_sensor was successfully connected! -> some error handling for dippid
        self.dippid_sensor.disconnect()
        # quit pygame
        pygame.quit()
        # sys.exit(0)


def main():
    pygame.init()  # setup and initialize pygame
    game = SuperDippidBoy()
    game.show_start_screen()


if __name__ == "__main__":
    main()
