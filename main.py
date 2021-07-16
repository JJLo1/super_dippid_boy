#!/usr/bin/python3
# -*- coding:utf-8 -*-

import random
from enum import Enum
from assets_loader import ImageHandler, SoundHandler
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


# global game constants
GAME_TITLE = "SUPER DIPPID BOY"
SCREEN_WIDTH, SCREEN_HEIGHT = 960, 640
FPS = 60  # the fps our game should run at
vec = pygame.math.Vector2


random.seed(42)  # set a random seed to make the game deterministic while testing


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
        self._check_collisions()

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
        self.rect.clamp_ip(self.area)

    def _check_collisions(self):
        pass

    def play_character_sound(self, sound_name: str):
        self.sound_handler.play_sound(sound_name)

    def _set_movement(self, new_movement):
        self.movement_x, self.movement_y = new_movement

    def change_movement(self, angle):
        if angle > 5:
            self._set_movement((0, -3))  # go up (negative as the y-axis is inverted!)
        elif angle > 0:
            self._set_movement((0, -1))
        elif angle == 0:
            self._set_movement((0, 0))
        elif angle < -5:
            self._set_movement((0, 3))
        elif angle < 0:
            self._set_movement((0, 1))


class GateType(Enum):
    CIRCLE = "circle"
    LINE = "line"
    RECTANGLE = "rectangle"
    # TODO ...

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))


def get_sprite_for_gate_type(gate_type: GateType):
    # TODO
    if gate_type is GateType.CIRCLE.value:
        return "portal.png"
    elif gate_type is GateType.LINE.value:
        return "portal.png"
    elif gate_type is GateType.RECTANGLE.value:
        return "portal.png"
    else:
        print("[WARNING]: Unknown gate type! Using circle as default.")
        return "portal.png"


class Gate(pygame.sprite.Sprite):
    def __init__(self, image_handler, x_pos, y_pos, width, height, move_speed, gate_type: GateType):
        pygame.sprite.Sprite.__init__(self)
        self.speed = move_speed

        sprite_name = get_sprite_for_gate_type(gate_type)
        self.image, image_rect = image_handler.get_image(sprite_name)
        self.rect = image_rect.copy()  # TODO or simply use get_rect()
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])
        # set position
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def update(self):
        self.rect.move_ip(self.speed, 0)


class Wall(pygame.sprite.Sprite):
    def __init__(self, image_handler, x_pos, y_pos, width, height, move_speed):
        pygame.sprite.Sprite.__init__(self)
        self.speed = move_speed

        self.image, image_rect = image_handler.get_image("wooden_material.png")
        self.rect = image_rect.copy()  # make a local copy so we don't change the reference!
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])
        # set position
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def update(self):
        self.rect.move_ip(self.speed, 0)


class Obstacle(pygame.sprite.Sprite):
    """
    A container class for all obstacles in the game.
    """

    obstacle_width = 80  # class variable as the obstacle width stays the same for all obstacles

    def __init__(self, x_start_pos, image_handler):
        pygame.sprite.Sprite.__init__(self)
        self.x_pos = x_start_pos
        self.image_handler = image_handler

        self.number_of_walls = 0
        self.number_of_gates = 0
        self.number_of_passages = 0
        self.move_speed = -2.5

        # list of all "wall-like" parts of the obstacle that must be avoided by the player
        self.walls = pygame.sprite.Group()
        # list of all parts that represent a gate / passage where a player has to perform a certain gesture
        self.gates = pygame.sprite.Group()

        self._create_obstacle()

    def _create_obstacle(self):
        print("\n#######################\n")
        self._generate_random_parts()
        # small sanity check for the creation logic
        if self.number_of_passages > 0:
            assert self.number_of_gates == 0, "Number_of_gates wasn't 0 even though some passages were created!"
        elif self.number_of_gates > 0:
            assert self.number_of_passages == 0, "Number_of_passages wasn't 0 even though there are more than 0 gates!"

        part_order = self._generate_random_order()

        # generate the positions of the parts (starting 50 px below the screen top and ending 50px above the bottom)
        self.bottom_border = SCREEN_HEIGHT - 50
        self.top_border = 50
        obstacle_area_height = self.bottom_border - self.top_border

        wall_height, gate_height, passage_height = -1, -1, -1
        # calculate the heights of the obstacle parts to fill the entire height
        if self.number_of_gates == 0:
            passage_height = random.randrange(50, 100)  # produce a pseudo random passage size
            free_space = (obstacle_area_height - passage_height * self.number_of_passages)
            wall_height = free_space / self.number_of_walls
            print(f"free_space: {free_space}, passage_h: {passage_height}, wall_h: {wall_height}")
        else:
            gate_height = obstacle_area_height / (self.number_of_walls * 3 + self.number_of_gates)
            wall_height = 3 * gate_height  # walls are always 3 times as large as gates

            print(f"Area: {obstacle_area_height}, gate_h: {gate_height}, wall_h: {wall_height}")
            # offset = 10  # 10 px offset for the gates so it looks a bit better

        self.last_y = self.top_border
        for element in part_order:
            if element == "w":
                new_wall = Wall(self.image_handler, self.x_pos, self.last_y, self.obstacle_width, wall_height,
                                self.move_speed)
                self.walls.add(new_wall)
                self.last_y = self.last_y + wall_height
            elif element == "g":
                # TODO self.last_y + offset

                gate_type = random.choice(GateType.values())  # get a random gate type
                new_gate = Gate(self.image_handler, self.x_pos, self.last_y, self.obstacle_width, gate_height,
                                self.move_speed, gate_type=gate_type)
                self.gates.add(new_gate)
                self.last_y = self.last_y + gate_height
            elif element == "p":
                # simply add a random space between the walls to create a passage
                self.last_y = self.last_y + passage_height

        self._combine_sprites()

    def _generate_random_order(self):
        # generate a random order of the walls, gates and optionally passages
        part_order = []
        part_order.extend(["w" for _ in range(self.number_of_walls)])
        part_order.extend(["g" for _ in range(self.number_of_gates)])
        part_order.extend(["p" for _ in range(self.number_of_passages)])
        random.shuffle(part_order)
        return part_order

    def _combine_sprites(self):
        # see https://stackoverflow.com/questions/53233894/pygame-combine-sprites
        self.rect = pygame.Rect(self.x_pos, 0, self.obstacle_width, SCREEN_HEIGHT)
        """
        self.rect = self.walls.sprites()[0].rect.copy()
        for sprite in self.walls.sprites()[1:]:
            self.rect.union_ip(sprite.rect)
        for gate_sprite in self.gates.sprites():
            self.rect.union_ip(gate_sprite.rect)
        """
        # Create a new transparent image with the combined size.
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        # Now blit all sprites onto the new surface.
        for sprite in self.walls.sprites():
            print(f"WALL Pos: y:{sprite.rect.y} ({sprite.rect})")
            self.image.blit(sprite.image, (sprite.rect.x - self.rect.left,
                                           sprite.rect.y))
        for sprite in self.gates.sprites():
            print(f"GATE Pos: y:{sprite.rect.y} ({sprite.rect})")
            self.image.blit(sprite.image, (sprite.rect.x - self.rect.left,
                                           sprite.rect.y))

    def _generate_random_parts(self):
        self.number_of_walls = random.randint(1, 3)  # generate a random number of walls between 1 and 3 (inclusive)
        print(f"Number of walls: {self.number_of_walls}")
        self.number_of_gates = self._get_number_of_gates(self.number_of_walls)
        print(f"Number of gates: {self.number_of_gates}")
        if self.number_of_gates == 0:
            # if there are no gates there must be some other passages where the user can go through
            self.number_of_passages = random.randint(1, 2)  # more than two passages aren't needed

    @staticmethod
    def _get_number_of_gates(num_walls: int):
        # we can always generate at max `num_walls + 1` gates (or none at all) as long as the walls are disjoint
        if num_walls == 1:
            # if we have 1 wall, we could only generate 0, 1 or 2 gates
            return random.randint(0, 2)
        elif num_walls == 2:
            # if we have 2 walls, we can generate up to 3 gates
            return random.randint(0, 3)
        elif num_walls == 3:
            # if we have 3 walls, we could generate up to 4 gates but more than 3 gates in the same column look weird
            # so here we simply choose between 0 and 3 gates as well for now
            return random.randint(0, 3)

    """
    def draw_at(self, game_window):
        for wall in self.walls:
            wall_x, wall_y, wall_width, wall_height = wall
            wall_x = self.x_pos
            filled_rect = pygame.Rect(wall_x, wall_y, wall_width, wall_height)
            pygame.draw.rect(game_window, (139, 69, 19), filled_rect)

        for gate in self.gates:
            gate_x, gate_y, gate_width, gate_height = gate
            gate_x = self.x_pos
            pygame.draw.ellipse(game_window, (255, 0, 0), (gate_x, gate_y, gate_width, gate_height))

    def draw_parts(self, surface):
        self.walls.draw(surface)
        self.gates.draw(surface)
    """

    def update(self):
        # self.x_pos += self.move_speed  # += as move speed is negative!
        # for sprite_group in [self.walls, self.gates]:
        #    sprite_group.update()

        # first_wall = self.walls.sprites()[0]  # safe because we always have at least one wall
        # self.x_pos = first_wall.rect.right

        self.rect.move_ip((self.move_speed, 0))

        if self.rect.right < 0:
            # remove all sprites first before killing the container
            # TODO does this leak memory? call kill of each sprite in the groups manually?
            self.walls.empty()
            self.gates.empty()
            # self.kill()


def get_screen_center_for_surface(surface_rect):
    # Put the center of surface at the center of the display (shifting the surface first is necessary as pygame always
    # uses the top-left corner of the rect)
    surface_center = (
        (SCREEN_WIDTH - surface_rect.get_width()) / 2,
        (SCREEN_HEIGHT - surface_rect.get_height()) / 2
    )
    return surface_center


def end_game():
    # stop music
    pygame.mixer.music.stop()
    pygame.mixer.quit()

    pygame.quit()


def setup_game():
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))   # setup the game window
    pygame.display.set_caption(GAME_TITLE)
    # pygame.mouse.set_visible(False)

    # setup background
    background_image, background_rect = ImageHandler.load_background_image()
    # scale the background image to fill the entire background
    w, h = screen.get_size()
    background = pygame.transform.smoothscale(background_image, [int(w), int(h)])

    top_border_block = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)  # pygame.SRCALPHA makes it transparent
    top_border_rect = top_border_block.get_rect(topleft=(0, 0))

    bottom_border_block = pygame.Surface((SCREEN_WIDTH, 50), pygame.SRCALPHA)  # TODO -50 ?
    bottom_border_rect = bottom_border_block.get_rect(bottomleft=(0, SCREEN_HEIGHT))

    return screen, background, background_rect, top_border_rect, bottom_border_rect


def show_initial_scene(screen, background):
    # Display the background
    screen.blit(background, (0, 0))
    # Changes to the display surface are not immediately visible. Normally, a display must be updated in areas that
    # have changed for them to be visible to the user. With double buffered displays the display must be swapped
    # (or flipped) for the changes to become visible
    pygame.display.flip()


def main():
    pygame.init()  # setup and initialize pygame
    screen, background, background_rect, top_border_rect, bottom_border_rect = setup_game()
    background_width, background_height = background.get_size()
    background_area = (0, 10, background_width, background_height)  # cut off 10 pixels at the top of the background

    sound_handler = SoundHandler()
    image_handler = ImageHandler()
    # TODO make sure the transition at the end when replaying is smooth!
    sound_handler.play_sound("mysterious_harp.mp3", play_infinite=True)  # start playing background music

    main_character = SlimeCharacter(image_handler, sound_handler, sprite_name="slime.png")
    obstacles = pygame.sprite.Group()
    collidables = pygame.sprite.Group()

    # create an event timer that fires an event each time the specified amount in milliseconds passes,
    # see https://stackoverflow.com/questions/18948981/do-something-every-x-milliseconds-in-pygame
    interval_time = random.randrange(2500, 4500)  # every 2.5 until 4.5 seconds
    SPAWN_OBSTACLE_EVENT = pygame.USEREVENT + 1
    pygame.time.set_timer(SPAWN_OBSTACLE_EVENT, interval_time)

    # Clock object used to help control the game's framerate. Used in the main loop to make sure the game doesn't run
    # too fast
    clock = pygame.time.Clock()

    font = pygame.font.Font(None, 25)
    fps_text_pos = (20, 20)

    show_initial_scene(screen, background)

    running = True
    # main game loop
    while running:
        # make sure the game doesn't run faster than the defined frames per second
        clock.tick(FPS)
        current_fps = clock.get_fps()
        text = font.render(f"Current FPS: {current_fps}", True, (255, 0, 0))  # TODO

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
            elif event.type == SPAWN_OBSTACLE_EVENT:
                # create a new obstacle to the right of the current screen whenever our custom event is sent
                new_obstacle = Obstacle(SCREEN_WIDTH + 20, image_handler)
                obstacles.add(new_obstacle)
                collidables.add(*new_obstacle.walls)

                # text.get_rect().move_ip(-1.5, 0)
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
        background_rect.move_ip(-1.5, 0)

        # it the right edge of the "left" image is zero, that means it's fully out of view
        if background_rect.right == 0:
            # so reset the rect and start over
            background_rect.x = 0

        # TODO draw blocks at all??
        # screen.blit(background, top_border_rect)
        # screen.blit(background, bottom_border_rect)

        # text.get_rect().move_ip(-1.5, 0)
        # background.blit(text, fps_text_pos)

        """
        for obstacle in obstacles:
            if obstacle.x_pos < obstacle.obstacle_width * -1:  # obstacle.x_pos < 0:
                obstacles.remove(obstacle)
        """
        obstacles.update()
        obstacles.draw(screen)

        main_character.update()
        screen.blit(main_character.image, main_character.rect)

        # Check if any obstacles have collided with the player
        if pygame.sprite.spritecollideany(main_character, collidables):
            # If so, then remove the player and stop the loop
            main_character.kill()
            running = False

        # Flip the contents of pygame's software double buffer to the screen.
        # This makes everything we've drawn visible all at once.
        pygame.display.flip()
        # pygame.display.update(...)  # can be used instead to update only a part of the display

    # quit the game and clean up after the main loop finished
    end_game()


if __name__ == "__main__":
    main()
