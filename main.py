#!/usr/bin/python3
# -*- coding:utf-8 -*-

import argparse
import random
import sys
import numpy as np
from DIPPID import SensorUDP
from assets_loader import SoundHandler, ImageHandler
from game_settings import GAME_TITLE, SCREEN_WIDTH, SCREEN_HEIGHT, FPS
from game_utils import draw_gesture
from gate_type import GateType
from obstacle import Obstacle, SharedObstacleState
from gesture_recognizer.dollar_one_recognizer import DollarOneRecognizer
from player_character import PlayerCharacter
import pygame
import pygame_menu
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


# TODO move the SuperDippidBoy class to a 'game.py' file and rename this one to 'system_demo.py', so all game related
#  files can go into their own subfolder
# noinspection PyAttributeOutsideInit
class SuperDippidBoy:

    def __init__(self, debug_active: bool, dippid_port=5700):
        self.debug = debug_active

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

    # --------------------------------------------------------------------------
    #                               Menu code
    # --------------------------------------------------------------------------

    def show_start_screen(self):
        """
        Main loop of the application that shows the menu at the beginning and the end of the game.
        """
        # variables for adding new gestures in debug mode
        self.new_gesture = []
        self.in_add_gesture_submenu = False
        is_drawing = False

        # create submenus
        if self.debug:
            self.create_add_gesture_submenu()
        self.create_available_gestures_submenu()
        self.create_sources_submenu()
        # create main menu
        self.create_main_menu()

        # menu event loop; we break out of it while playing the game and return to it after the game ends
        game_running = True
        while game_running:
            events = pygame.event.get()
            for event in events:
                if event.type == pygame.QUIT:
                    game_running = False

                # the mouse events below are only used in debug mode to add new gestures!
                elif event.type == MOUSEBUTTONDOWN:
                    if self.debug and event.button == 1 and self.in_add_gesture_submenu:
                        # Check if the mouse position is inside the draw area, otherwise ignore it. Without this check
                        # we couldn't click anywhere without resetting the gesture points as well!
                        if (self.draw_area_rect.left <= pygame.mouse.get_pos()[0] <= self.draw_area_rect.right) and \
                                (self.draw_area_rect.top <= pygame.mouse.get_pos()[1] <= self.draw_area_rect.bottom):
                            is_drawing = True
                            self.new_gesture = []  # reset the points

                elif event.type == MOUSEBUTTONUP:
                    if self.debug and event.button == 1:  # if the left mouse button was released
                        is_drawing = False

                elif event.type == MOUSEMOTION:
                    if self.debug and is_drawing and self.in_add_gesture_submenu:
                        self.new_gesture.append((pygame.mouse.get_pos()))  # add the current mouse position as new point

            if self.main_menu.is_enabled():
                self.main_menu.update(events)
                self.main_menu.draw(self.screen)
                # in debug mode: show the new added gestures
                if self.debug and len(self.new_gesture) > 2:  # we need at least two points to draw a line
                    draw_gesture(self.screen, self.new_gesture)

            pygame.display.flip()

        # cleanup and finish application after the main loop ends
        self.end_game()

    def create_add_gesture_submenu(self):
        # create submenu to add a new gesture
        self.add_gesture_submenu = pygame_menu.Menu('Add new gesture', SCREEN_WIDTH, SCREEN_HEIGHT,
                                                    menu_id="add_gesture_submenu",
                                                    theme=pygame_menu.themes.THEME_SOLARIZED)
        self.add_gesture_submenu.add.label("Draw the gesture:", max_char=-1, font_size=20, border_width=0)
        # create the surface area where we can draw new gestures
        screen_scale_factor = 2
        new_gesture_surface = pygame.Surface((SCREEN_WIDTH / screen_scale_factor, SCREEN_HEIGHT / screen_scale_factor))
        self.draw_area_rect = new_gesture_surface.get_rect()
        # fix the start position (per default it would be created at [0, 0])
        self.draw_area_rect.x = SCREEN_WIDTH / screen_scale_factor - self.draw_area_rect.width / screen_scale_factor
        self.draw_area_rect.y = SCREEN_HEIGHT / screen_scale_factor - self.draw_area_rect.height / screen_scale_factor
        new_gesture_surface.fill((255, 255, 255))  # fill background white to make it stand out
        self.add_gesture_submenu.add.surface(new_gesture_surface)

        self.add_gesture_submenu.add.vertical_margin(15)
        self.new_gesture_name = ""
        self.add_gesture_submenu.add.text_input("Enter gesture name: ", border_width=0, maxchar=25,
                                                input_underline_len=33, padding=(5, 5, 5, 5), input_underline='_',
                                                onchange=self.on_gesture_name_change)
        self.add_gesture_submenu.add.vertical_margin(5)
        self.add_gesture_submenu.add.button('Save gesture', self.add_new_gesture, border_width=1)

        # create two labels that are shown conditionally based on whether saving the gesture worked or not
        self.new_gesture_success_label = self.add_gesture_submenu.add.label('Gesture successfully saved!') \
            .update_font({"color": (51, 153, 51), "size": 14})
        self.new_gesture_error_label = self.add_gesture_submenu.add.label(
            'Saving gesture failed! Check the terminal output.').update_font({"color": (255, 0, 0), "size": 14})
        self.new_gesture_success_label.hide()
        self.new_gesture_error_label.hide()

    def create_available_gestures_submenu(self):
        all_gestures = self.gesture_recognizer.get_all_gestures()  # get all known gestures from the gesture recognizer
        if all_gestures:
            self.available_gestures_submenu = pygame_menu.Menu('Available gestures', SCREEN_WIDTH, SCREEN_HEIGHT,
                                                               menu_id="show_gestures_submenu",
                                                               theme=pygame_menu.themes.THEME_SOLARIZED,
                                                               columns=len(all_gestures), rows=2)
            # scaling factors for the size of the display surfaces
            drawing_size_x = 1 / 4
            drawing_size_y = 1 / 2
            for gesture in GateType.values():
                # draw all gestures in a separate column with name + image
                self.available_gestures_submenu.add.label(gesture.capitalize(), font_size=30, border_width=0)
                gesture_surface = pygame.Surface((SCREEN_WIDTH * drawing_size_x, SCREEN_HEIGHT * drawing_size_y))
                gesture_surface.fill((255, 255, 255))
                self.available_gestures_submenu.add.surface(gesture_surface)

                gesture_data = all_gestures.get(gesture)
                if not gesture_data:
                    sys.stderr.write(f"Gesture data for gesture '{gesture}' not found!\n")
                    break
                points = gesture_data["original"]  # get the original "raw" drawing, not the normalized points
                if len(points) > 2:
                    # calculate the new point coordinates for the gestures (that were drawn relative to the whole
                    # screen size) by multiplying each point with the drawing size factor so we get the exact
                    # relative position in the smaller surface area
                    points = [np.array(point) * np.array([drawing_size_x, drawing_size_y]) for point in points]
                    draw_gesture(gesture_surface, points)
        else:
            self.available_gestures_submenu = pygame_menu.Menu('Available gestures', SCREEN_WIDTH, SCREEN_HEIGHT,
                                                               menu_id="show_gestures_submenu",
                                                               theme=pygame_menu.themes.THEME_SOLARIZED)
            self.available_gestures_submenu.add.label("No gestures available!", font_size=40, border_width=0)

    def create_sources_submenu(self):
        # create a small submenu to show the game's asset sources
        self.sources_submenu = pygame_menu.Menu('Sources', SCREEN_WIDTH, SCREEN_HEIGHT, center_content=False,
                                                menu_id="sources_submenu", theme=pygame_menu.themes.THEME_SOLARIZED)
        self.sources_submenu.add.label("Used Assets:", font_size=30, border_width=0)
        self.sources_submenu.add.label("\n- Forest Background Image by edermunizz ("
                                       "https://edermunizz.itch.io/free-pixel-art-forest)"
                                       "\n- Mysterious Harp Loop Music by \"VWolfdog\" ("
                                       "https://opengameart.org/content/soft-mysterious-harp-loop)"
                                       "\n- Wooden Material by \"yamachem\" ("
                                       "https://openclipart.org/detail/226666/flooring-material-02)",
                                       font_size=20, border_width=0)
        # self.sources_submenu.add.button('Return to main menu', pygame_menu.events.BACK)

    def create_main_menu(self):
        # the first screen of the application
        self.main_menu = pygame_menu.Menu('Welcome to SUPER DIPPID BOY', SCREEN_WIDTH, SCREEN_HEIGHT,
                                          theme=pygame_menu.themes.THEME_SOLARIZED)

        # show a dropdown to let the user select the axis around which the DIPPID device should be rotated to control
        # the character
        self.dippid_axis = "x"
        self.main_menu.add.dropselect(title='Choose DIPPID axis: ', items=['x', 'y', 'z'], font_size=20, default=0,
                                      selection_box_height=5, onchange=self.on_axis_changed)
        self.main_menu.add.vertical_margin(5)

        self.main_menu.add.button('Play', self.start_game)
        self.main_menu.add.vertical_margin(50)
        if self.debug:
            self.main_menu.add.button('Add gesture', self.show_submenu, self.add_gesture_submenu)
        self.main_menu.add.button('Show available gestures', self.show_submenu, self.available_gestures_submenu)
        self.main_menu.add.button('Sources', self.show_submenu, self.sources_submenu)
        self.main_menu.add.button('Quit', pygame_menu.events.EXIT)

    def show_submenu(self, menu):
        if self.debug:
            if menu.get_id() == self.add_gesture_submenu.get_id():
                # flag to check whether we are in the add gesture submenu or not; used in the menu event loop to check
                # if drawing a gesture with the mouse should be allowed or not so we react to mouse events only in
                # this submenu
                self.in_add_gesture_submenu = True
            else:
                self.in_add_gesture_submenu = False
                self.new_gesture_success_label.hide()
                self.new_gesture_error_label.hide()

        # protected member access is necessary as we can't open the submenu otherwise if we want to perform an
        # action before, like setting a flag
        self.main_menu._open(menu)

    def on_axis_changed(self, selected_item):
        self.dippid_axis = selected_item[0]  # we get a tuple with (value, index_position)

    def on_gesture_name_change(self, current_text):
        self.new_gesture_name = current_text

    def add_new_gesture(self):
        # check if a name was given for this gesture
        if self.new_gesture_name == "" or self.new_gesture_name.isspace():
            sys.stderr.write("\nThe gesture needs a name!\n")
            self.toggle_save_gesture_status(False)
            return
        # also check if a gesture has actually been drawn
        elif len(self.new_gesture) < 2:
            sys.stderr.write(f"\nMore points for the gesture needed! Currently {len(self.new_gesture)} points.\n")
            self.toggle_save_gesture_status(False)
            return

        # save gesture to file and show status label whether it worked or not
        status = self.gesture_recognizer.save_gesture(self.new_gesture_name, self.new_gesture)
        self.toggle_save_gesture_status(True) if status else self.toggle_save_gesture_status(False)

    def toggle_save_gesture_status(self, success: bool):
        if success:
            self.new_gesture_error_label.hide()
            self.new_gesture_success_label.show()
        else:
            self.new_gesture_success_label.hide()
            self.new_gesture_error_label.show()

    # --------------------------------------------------------------------------
    #                              Actual game code
    # --------------------------------------------------------------------------

    def start_game(self):
        self.main_menu.disable()
        self.main_menu.full_reset()

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

            # if self.debug:
            #     current_fps = self.clock.get_fps()
            #     print(f"Current FPS: {current_fps}")
            self.handle_events()

            self.check_player_movement()
            self.move_background()
            self.update_game_objects()

            # TODO show gesture on separate thread so main loop time isn't blocked by this?
            if self.show_gesture and len(self.gesture_points) > 2:  # we need at least two points to draw a line
                draw_gesture(self.screen, self.gesture_points)

            self.update_score()
            self.check_collisions()

            # Flip the contents of pygame's software double buffer to the screen.
            # This makes everything we've drawn visible all at once.
            pygame.display.flip()

        # clean up after the main loop finished and return to the main menu
        self.return_to_menu()

    def handle_events(self):
        # react to pygame events
        for event in pygame.event.get():
            if event.type == QUIT:
                self.is_running = False

            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    self.is_running = False

            elif event.type == KEYUP:
                if self.debug and (event.key == pygame.K_w or event.key == pygame.K_s):
                    self.main_character.change_movement(angle=0)

            elif event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    print("Left mouse button pressed")
                    # started to draw gesture
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
                    # TODO nur wenn score groß genug ist, auch tatsächlich die Form ändern!
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

    # TODO steuerung über menü dropdown
    def check_player_movement(self):
        if "gravity" in self.dippid_sensor.get_capabilities():
            self.main_character.change_movement(angle=self.dippid_sensor.get_value('gravity')[self.dippid_axis])
        # TODO: check if "angle" is bugged on m5stack, since the values seemed strange
        elif "angle" in self.dippid_sensor.get_capabilities():
            self.main_character.change_movement(angle=self.dippid_sensor.get_value('angle')[self.dippid_axis])
        """
        # alternative:
        if self.dippid_sensor.get_value('gravity')[self.dippid_axis] > 1:
            self.main_character.change_movement(angle=5)
        elif dippid.get_value('gravity')[self.dippid_axis] < -1:
            self.main_character.change_movement(angle=-5)
        else:
            self.main_character.change_movement(angle=0)
        """

        if self.debug:
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

        if self.debug:
            # show player hitbox in debug mode
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
            # self.main_character.kill()
            # self.is_running = False
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

    # --------------------------------------------------------------------------
    #                                 Game end
    # --------------------------------------------------------------------------

    def return_to_menu(self):
        # stop music
        # pygame.mixer.music.stop()
        self.sound_handler.stop_sound("mysterious_harp.mp3")

        # enable main menu again
        self.main_menu.enable()

    def end_game(self):
        pygame.mixer.quit()
        # TODO check that dippid_sensor was successfully connected! -> some error handling for dippid
        self.dippid_sensor.disconnect()  # stop dippid sensor
        pygame.quit()  # quit pygame
        # sys.exit(0)


def main():
    port = args.port
    debug_mode_enabled = args.debug
    if debug_mode_enabled:
        print("[INFO]: You are in DEBUG mode at the moment!")
        random.seed(42)  # set a random seed to make the game deterministic while testing

    pygame.init()  # setup and initialize pygame
    game = SuperDippidBoy(debug_active=debug_mode_enabled, dippid_port=port)
    game.show_start_screen()


if __name__ == "__main__":
    # setup an argument parser to enable command line parameters
    parser = argparse.ArgumentParser(description="Small gesture-based 2D-Side-Scroller made with pygame where the main "
                                                 "character can be controlled via a DIPPID device.")
    parser.add_argument("-d", "--debug", help="Enable debug mode: shows the player's hitbox and allows controlling "
                                              "the main character with 'w' and 's'. Also adds a menu option "
                                              "where new gestures can be added", action="store_true", default=False)
    parser.add_argument("-p", "--port", help="The port on which the DIPPID device sends the data", type=int,
                        default=5700, required=False)
    args = parser.parse_args()

    main()
