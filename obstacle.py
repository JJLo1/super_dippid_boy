import random
import pygame
from game_settings import SCREEN_HEIGHT
from gate_type import GateType


class SharedObstacleState:
    # The obstacle speed needs to be updated for the obstacle class as well as the wall and gate classes at the
    # same time and letting Gate and Wall inherit from Obstacle would violate the Liskov substitution principle.
    # Because of this the 'SharedObstacleState' class acts as a "state-holder" that mediates shared states.
    obstacle_move_speed = 3.5

    @classmethod
    def increase_move_speed(cls):
        cls.obstacle_move_speed += 0.5  # TODO probably too much, 0.2 instead?


class Gate(pygame.sprite.Sprite, SharedObstacleState):
    def __init__(self, image_handler, x_pos, y_pos, width, height, gate_type: GateType):
        pygame.sprite.Sprite.__init__(self)
        self.gate_type = gate_type

        sprite_name = GateType.get_sprite_for_gate_type(gate_type)
        self.image = image_handler.get_image(sprite_name)
        self.rect = self.image.get_rect()
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])
        # set initial position
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def get_gate_type(self):
        return self.gate_type

    def update(self):
        self.rect.move_ip(-self.obstacle_move_speed, 0)
        if self.rect.right < 0:
            self.kill()


class Wall(pygame.sprite.Sprite, SharedObstacleState):
    def __init__(self, image_handler, x_pos, y_pos, width, height):
        pygame.sprite.Sprite.__init__(self)

        self.image = image_handler.get_image("wooden_material.png")
        self.rect = self.image.get_rect()
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])
        # set initial position
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def update(self):
        self.rect.move_ip(-self.obstacle_move_speed, 0)
        if self.rect.right < 0:
            self.kill()  # kill() automatically removes this sprite from every sprite group it currently belongs to


class Obstacle(pygame.sprite.Sprite, SharedObstacleState):
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

        # list of all "wall-like" parts of the obstacle that must be avoided by the player
        self.walls = pygame.sprite.Group()
        # list of all parts that represent a gate / passage where a player has to perform a certain gesture
        self.gates = pygame.sprite.Group()

        self._create_obstacle()

    def _create_obstacle(self):
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
        gate_offset = 15  # half of the offset is added to each side of the gates so it looks a bit better

        wall_height, gate_height, passage_height = -1, -1, -1
        # calculate the heights of the obstacle parts to fill the entire height
        if self.number_of_gates == 0:
            passage_height = random.randrange(50, 100)  # produce a pseudo random passage size
            free_space = (obstacle_area_height - passage_height * self.number_of_passages)
            wall_height = free_space / self.number_of_walls
            # print(f"free_space: {free_space}, passage_h: {passage_height}, wall_h: {wall_height}")
        else:
            size_factor = 2  # walls are always twice as large as gates
            gate_height = (obstacle_area_height - gate_offset * self.number_of_gates) / (
                    self.number_of_walls * size_factor + self.number_of_gates)
            wall_height = size_factor * gate_height
            # print(f"Area: {obstacle_area_height}, gate_h: {gate_height}, wall_h: {wall_height}")

        self.last_y = self.top_border
        for element in part_order:
            if element == "w":
                new_wall = Wall(self.image_handler, self.x_pos, self.last_y, self.obstacle_width, wall_height)
                self.walls.add(new_wall)
                self.last_y = self.last_y + wall_height
            elif element == "g":
                self.last_y += gate_offset / 2

                gate_type = random.choice(GateType.values())  # get a random gate type
                new_gate = Gate(self.image_handler, self.x_pos, self.last_y, self.obstacle_width, gate_height,
                                gate_type=gate_type)
                self.gates.add(new_gate)
                self.last_y = self.last_y + gate_height + gate_offset / 2
            elif element == "p":
                # simply add a random space between the walls to create a passage
                self.last_y = self.last_y + passage_height

        self._combine_sprites()

    def _generate_random_parts(self):
        self.number_of_walls = random.randint(1, 3)  # generate a random number of walls between 1 and 3 (inclusive)
        # print(f"Number of walls: {self.number_of_walls}")
        self.number_of_gates = self._get_number_of_gates(self.number_of_walls)
        # print(f"Number of gates: {self.number_of_gates}")
        if self.number_of_gates == 0:
            # if there are no gates there must be some other passages where the user can go through
            self.number_of_passages = random.randint(1, 2)  # more than two passages aren't needed

    @staticmethod
    def _get_number_of_gates(num_walls: int):
        # we can always generate at maximum `num_walls + 1` gates (or none at all) as long as the walls are disjoint
        if num_walls == 1:
            # if we have 1 wall, we could only generate 0, 1 or 2 gates; here we either take 0 or 1
            return random.randint(0, 1)
        elif num_walls == 2:
            # if we have 2 walls, we can generate up to 3 gates but more than 2 gates in the same column look weird
            # so here we simply choose between 0 and 2 gates
            return random.randint(0, 2)
        elif num_walls == 3:
            # if we have 3 walls, we could generate up to 4 gates but we take between 0 and 2 gates as well for now
            return random.randint(0, 2)

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

    def update(self):
        for sprite_group in [self.walls, self.gates]:
            sprite_group.update()

        self.rect.move_ip((-self.obstacle_move_speed, 0))

        if self.rect.right < 0:
            # print(f"Obstacle passed out left: len walls: {len(self.walls)}, len_gates: {len(self.gates)}")
            # remove all sprites first before killing the container
            # self.walls.empty()
            # self.gates.empty()
            self.kill()
