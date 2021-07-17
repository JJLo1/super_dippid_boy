import random
import pygame
from enum import Enum
from game_constants import SCREEN_HEIGHT


class GateType(Enum):
    CIRCLE = "circle"
    LINE = "line"
    RECTANGLE = "rectangle"

    @classmethod
    def values(cls):
        return list(map(lambda c: c.value, cls))

    @staticmethod
    def get_sprite_for_gate_type(gate_type):
        # TODO load different images
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
        self.gate_type = gate_type

        sprite_name = GateType.get_sprite_for_gate_type(gate_type)
        self.image, image_rect = image_handler.get_image(sprite_name)
        self.rect = image_rect.copy()  # TODO or simply use get_rect()
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])
        # set position
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def get_gate_type(self):
        return self.gate_type

    def update(self):
        self.rect.move_ip(self.speed, 0)
        if self.rect.right < 0:
            self.kill()


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
        if self.rect.right < 0:
            self.kill()  # kill automatically removes this sprite from every sprite group it currently belongs to


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
        self.move_speed = -3.5  # TODO increase this (and the obstacle spawn time) slightly when the game progresses

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
            # print(f"free_space: {free_space}, passage_h: {passage_height}, wall_h: {wall_height}")
        else:
            gate_height = obstacle_area_height / (self.number_of_walls * 3 + self.number_of_gates)
            wall_height = 3 * gate_height  # walls are always 3 times as large as gates

            # print(f"Area: {obstacle_area_height}, gate_h: {gate_height}, wall_h: {wall_height}")
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
        # Create a new transparent image with the combined size.
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        # Now blit all sprites onto the new surface.
        for sprite in self.walls.sprites():
            self.image.blit(sprite.image, (sprite.rect.x - self.rect.left,
                                           sprite.rect.y))
        for sprite in self.gates.sprites():
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

    def update(self):
        # self.x_pos += self.move_speed  # += as move speed is negative!
        for sprite_group in [self.walls, self.gates]:
            sprite_group.update()

        # first_wall = self.walls.sprites()[0]  # safe because we always have at least one wall
        # self.x_pos = first_wall.rect.right

        self.rect.move_ip((self.move_speed, 0))

        if self.rect.right < 0:
            print(f"Obstacle passed out left: len walls: {len(self.walls)}, len_gates: {len(self.gates)}")
            # remove all sprites first before killing the container
            # TODO does this leak memory? call kill of each sprite in the groups manually?
            # self.walls.empty()
            # self.gates.empty()
            self.kill()
