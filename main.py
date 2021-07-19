#!/usr/bin/python3
# -*- coding:utf-8 -*-

import random
from DIPPID import SensorUDP
from assets_loader import SoundHandler
from game_utils import draw_gesture
from obstacle import Obstacle, SharedObstacleState
from gesture_recognizer.dollar_one_recognizer import DollarOneRecognizer
from player_character import *
import pygame
from PyQt5 import QtWidgets, uic, QtGui

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


class SuperDippidBoy(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()
        self.start_screen = QtWidgets.QWidget()
        self.__ui = uic.loadUi("assets/start_menu.ui", self)
        self.setFixedSize(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.dippid_sensor = SensorUDP(5700)

        # init gesture recognizer
        self.gesture_recognizer = DollarOneRecognizer()

        self.screen, self.background, self.background_rect = self.setup_game()
        self.background_width, self.background_height = self.background.get_size()
        self.background_area = (
        0, 10, self.background_width, self.background_height)  # cut off 10 pixels at the top of the background
        self.show()

        self.sound_handler = SoundHandler()
        self.image_handler = ImageHandler()
        # TODO make sure the transition at the end when replaying is smooth!
        self.sound_handler.play_sound("mysterious_harp.mp3", play_infinite=True)  # start playing background music
        # self.run_game()
        self.run_start_screen()

    def end_game(self):

        # stop music
        pygame.mixer.music.stop()
        pygame.mixer.quit()
        # stop dippid sensor
        self.dippid_sensor.disconnect()
        # quit pygame
        pygame.quit()
        # quit pyQt
        self.close()
        # TODO finish dippid device as well

    def setup_game(self):
        # pygame needs a display to work properly, but since we use PyQt to display our game we will set it hidden
        screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.HIDDEN)
        pygame.display.set_caption(GAME_TITLE)
        pygame.display.iconify()

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

    def draw_background(self):
        # Display the background
        self.screen.blit(self.background, (0, 0))
        # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
        # have changed for them to be visible to the user. With double buffered displays the display must be swapped
        # (or flipped) for the changes to become visible
        # pygame.display.flip()

    def run_start_screen(self):
        self.draw_background()
        self.menu_widget = self.__ui.GameMenu
        self.menu_widget.move(self.rect().center() - self.menu_widget.rect().center())
        self.__ui.StartGameButton.clicked.connect(self.run_game)

    def run_game(self):
        self.menu_widget.hide()
        main_character = PlayerCharacter(self.image_handler, self.sound_handler, graphics_folder="assets/Triangle")
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

        # Clock object used to help control the game's framerate. Used in the main loop to make sure the game doesn't run
        # too fast
        clock = pygame.time.Clock()

        font = pygame.font.Font(None, 25)  # TODO show the current point score on the screen
        current_points = 0

        self.draw_background()

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
            self.screen.blit(text, (10, 10))

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
                        predicted_gesture = self.gesture_recognizer.predict_gesture(gesture_points)
                        # print(f"\n########Predicted gesture in main: {predicted_gesture}\n#########\n")
                        main_character.set_current_form(predicted_gesture)

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
                    new_obstacle = Obstacle(SCREEN_WIDTH + 20, self.image_handler)
                    obstacles.add(new_obstacle)
                    wall_collidables.add(*new_obstacle.walls)
                    gate_collidables.add(*new_obstacle.gates)

                elif event.type == UPDATE_SCORE_EVENT:
                    current_points += 5
            if "gravity" in self.dippid_sensor.get_capabilities():
                main_character.change_movement(angle=self.dippid_sensor.get_value('gravity')['x'])
            # TODO: check if "angle" is bugged on m5stack, since the values seemed strange
            elif "angle" in self.dippid_sensor.get_capabilities():
                main_character.change_movement(angle=self.dippid_sensor.get_value('angle')['x'])

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

            # draw background (erases everything from previous frame (quite inefficient!))
            self.screen.blit(self.background, self.background_rect, area=self.background_area)
            # more efficient:
            # [screen.blit(background, sprite.rect, sprite.rect) for game_object_group in game_objects for sprite
            #  in game_object_group.sprites()]

            # Implement a scrolling background, see https://stackoverflow.com/questions/51320007/side-scrolling-background
            # the new position of the upcoming background is calculated by simply moving the rect by the width of the image
            # upcoming image is the same as the current one, just offset to the right
            upcoming_background = self.background_rect.move(self.background_rect.width, 0)
            self.screen.blit(self.background, upcoming_background, area=self.background_area)

            # move the background position rect to get a scrolling background
            self.background_rect.move_ip(-background_movement_speed, 0)

            # it the right edge of the "left" image is zero, that means it's fully out of view
            if self.background_rect.right == 0:
                # so reset the rect and start over
                self.background_rect.x = 0

            # draw top and bottom border blocks  # TODO quite ugly at the moment
            pygame.draw.rect(self.screen, (24, 61, 87), (0, 0, SCREEN_WIDTH, 49))
            pygame.draw.rect(self.screen, (74, 59, 43), (0, SCREEN_HEIGHT - 49, SCREEN_WIDTH, 50))

            obstacles.update()
            obstacles.draw(self.screen)

            if show_gesture and len(gesture_points) > 2:  # we need at least two points to draw a line
                draw_gesture(self.screen, gesture_points)
                # pygame.time.set_timer(HIDE_GESTURE_EVENT, 500)  # hide gesture after 500 ms

            main_character.update()
            self.screen.blit(main_character.image, main_character.rect)
            # pygame.draw.rect(self.screen,(255,0,0),main_character.rect)

            text_surface = font.render(f"Score: {current_points}", True, (255, 0, 0))
            self.screen.blit(text_surface, (SCREEN_WIDTH // 2 - 50, 15))

            # Check if any obstacles have collided with the player
            if pygame.sprite.spritecollideany(main_character, wall_collidables):
                # If so, then remove the player and stop the loop
                print("Player collided with wall! Game over!")
                main_character.kill()
            # running = False
            # TODO show 'You Died' - Message :)

            # if pygame.sprite.spritecollideany(main_character, gate_collidables, check_gate_collision):

            gate_sprite = pygame.sprite.spritecollideany(main_character, gate_collidables)
            if gate_sprite:
                curr_form = main_character.get_current_form()
                gate_form = gate_sprite.get_gate_type()
                if curr_form == gate_form:
                    current_points += 20
                else:
                    print("Gate type:", gate_sprite.get_gate_type())  # linter warning is wrong here, just ignore it
                    print("Current player form does not match gate type! Point deduction!")
                    current_points -= 20  # FIXME this is executed 60 times per second  -> change collision detection to
                    # x_pos and right edge of player only?

            # Flip the contents of pygame's software double buffer to the screen.
            # This makes everything we've drawn visible all at once.
            # pygame.display.flip()
            # pygame.display.update(...)  # can be used instead to update only a part of the display
            self.update()

        # quit the game and clean up after the main loop finished
        self.end_game()

    def paintEvent(self, a0: QtGui.QPaintEvent) -> None:
        image_data = self.screen.get_buffer().raw
        image = QtGui.QImage(image_data, self.screen.get_width(), self.screen.get_height(), QtGui.QImage.Format_RGB32)
        qp = QtGui.QPainter()
        qp.begin(self)
        qp.drawImage(0, 0, image)
        qp.end()

    # Overiding close event, so we can close the pygame window and sounds too
    def closeEvent(self, a0: QtGui.QCloseEvent) -> None:
        self.end_game()


# TODO this main method is far too long -> extract most of it to a main class, e.g. "Game", as in the Praxisseminar
def main():
    app = QtWidgets.QApplication(sys.argv)
    pygame.init()  # setup and initialize pygame
    game = SuperDippidBoy()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
