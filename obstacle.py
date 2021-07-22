import random
import pygame
from game_settings import SCREEN_HEIGHT, OBSTACLE_DEFAULT_MOVEMENT_SPEED
from gate_type import GateType


class SharedObstacleState:
    # The obstacle speed needs to be updated for the obstacle class as well as the wall and gate classes at the
    # same time and letting Gate and Wall inherit from Obstacle would violate the Liskov substitution principle.
    # Because of this the 'SharedObstacleState' class acts as a "state-holder" that mediates shared states.
    obstacle_move_speed = OBSTACLE_DEFAULT_MOVEMENT_SPEED

    @classmethod
    def increase_move_speed(cls):
        cls.obstacle_move_speed += 0.5  # TODO probably too much, 0.2 instead?

    @classmethod
    def reset_move_speed(cls):
        cls.obstacle_move_speed = OBSTACLE_DEFAULT_MOVEMENT_SPEED


class Gate(pygame.sprite.Sprite, SharedObstacleState):
    """
    A gate is a special kind of obstacle part where the player must have the correct form to pass through.
    """

    def __init__(self, image_handler, x_pos, y_pos, width, height, gate_type: GateType):
        pygame.sprite.Sprite.__init__(self)
        self.gate_type = gate_type
        # flag to check whether this gate has already collided with the player to prevent more than one collide hit
        self.has_collided = False

        sprite_name = GateType.get_sprite_for_gate_type(gate_type)  # get the correct sprite for this gate type
        self.image = image_handler.get_image(sprite_name)
        # scale the image to the necessary size
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])

        # set the initial position
        self.rect = self.image.get_rect()
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def set_collided(self):
        self.has_collided = True

    def has_already_collided(self):
        return self.has_collided

    def get_gate_type(self):
        return self.gate_type

    def update(self):
        # move the gate a little bit to the left on every frame update
        self.rect.move_ip(-self.obstacle_move_speed, 0)
        # if it is completely outside the left screen edge, remove this gate
        if self.rect.right < 0:
            self.kill()  # kill() automatically removes this sprite from every sprite group it currently belongs to


class Wall(pygame.sprite.Sprite, SharedObstacleState):
    """
    A wall is the standard obstacle part that the player must avoid to progress further.
    """

    def __init__(self, image_handler, x_pos, y_pos, width, height):
        pygame.sprite.Sprite.__init__(self)

        self.image = image_handler.get_image("wooden_material.png")  # load sprite
        self.image = pygame.transform.smoothscale(self.image, [int(width), int(height)])

        # set the initial position
        self.rect = self.image.get_rect()
        self.rect.topleft = (x_pos, y_pos)
        self.rect.width = width
        self.rect.height = height

    def update(self):
        self.rect.move_ip(-self.obstacle_move_speed, 0)
        if self.rect.right < 0:
            self.kill()


class Obstacle(pygame.sprite.Sprite, SharedObstacleState):
    """
    A container class that contains all obstacles in a column by creating a random compound sprite of walls,
    gates and passages.
    """

    obstacle_width = 80  # class variable as the obstacle width stays the same for all obstacles
    gate_offset = 15  # half of the offset is added to each side of the gates so it looks a bit better
    bottom_border = SCREEN_HEIGHT - 50
    top_border = 50
    # obstacles start 50 px below the screen top and end 50px above the bottom
    obstacle_area_height = bottom_border - top_border

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
        self._create_obstacle_parts(part_order)
        self._combine_sprites()

    def _generate_random_parts(self):
        self.number_of_walls = random.randint(1, 3)  # generate a random number of walls between 1 and 3 (inclusive)
        self.number_of_gates = self._get_number_of_gates(self.number_of_walls)
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
        # generate a random order of the walls, gates and passages
        part_order = []
        part_order.extend(["w" for _ in range(self.number_of_walls)])
        part_order.extend(["g" for _ in range(self.number_of_gates)])
        part_order.extend(["p" for _ in range(self.number_of_passages)])
        random.shuffle(part_order)
        return part_order

    def _create_obstacle_parts(self, part_order):
        wall_height, gate_height, passage_height = -1, -1, -1

        # calculate the heights of the obstacle parts to fill the entire height of the column
        if self.number_of_gates == 0:
            passage_height = random.randrange(80, 150)  # produce a pseudo random passage size
            wall_space = (self.obstacle_area_height - passage_height * self.number_of_passages)
            wall_height = wall_space / self.number_of_walls
            # print(f"wall_space: {wall_space}, passage_h: {passage_height}, wall_h: {wall_height}")
        else:
            '''
            Formula used (after the offset has been subtracted):
            (1) column_height = number_walls * wall_size + number_gates * gate_size
            (2) wall_size = 2 * gate_size
            -> with (2) in (1):
                => column_height = gate_size * (2 * number_walls + number_gates)
                => gate_size = column_height / (2 * number_walls + number_gates)
            '''
            # size_factor = 2  # walls are always twice as large as gates
            # TODO set size factor based on the number of generated walls (and gates)
            size_factor = 2 if self.number_of_walls > 1 else 3
            gate_height = (self.obstacle_area_height - self.gate_offset * self.number_of_gates) / (
                        self.number_of_walls * size_factor + self.number_of_gates)
            wall_height = size_factor * gate_height
            # print(f"Area: {obstacle_area_height}, gate_h: {gate_height}, wall_h: {wall_height}")

        self.last_y = self.top_border
        for element in part_order:
            if element == "w":
                # we create a new wall and add its height to the current y-pos so the next part will start below it
                new_wall = Wall(self.image_handler, self.x_pos, self.last_y, self.obstacle_width, wall_height)
                self.walls.add(new_wall)
                self.last_y = self.last_y + wall_height
            elif element == "g":
                # to create a gate, we add half of the offset at the start and at the end and choose a random sprite
                # for the gate type
                self.last_y += self.gate_offset / 2

                gate_type = random.choice(GateType.values())  # get a random gate type
                new_gate = Gate(self.image_handler, self.x_pos, self.last_y, self.obstacle_width, gate_height,
                                gate_type=gate_type)
                self.gates.add(new_gate)
                self.last_y = self.last_y + gate_height + self.gate_offset / 2
            elif element == "p":
                # to create a passage (an empty space where the player can safely pass through) we simply add a
                # randomly generated space between the walls
                self.last_y = self.last_y + passage_height

    def _combine_sprites(self):
        # see https://stackoverflow.com/questions/53233894/pygame-combine-sprites
        self.rect = pygame.Rect(self.x_pos, 0, self.obstacle_width, SCREEN_HEIGHT)

        # Create a new transparent image with the combined size
        self.image = pygame.Surface(self.rect.size, pygame.SRCALPHA)
        # and blit all sprites onto the new surface
        for sprite in self.walls.sprites():
            self.image.blit(sprite.image, (sprite.rect.x - self.rect.left,
                                           sprite.rect.y))
        for sprite in self.gates.sprites():
            self.image.blit(sprite.image, (sprite.rect.x - self.rect.left,
                                           sprite.rect.y))

    def update(self):
        # update the obstacle parts first
        for sprite_group in [self.walls, self.gates]:
            sprite_group.update()

        self.rect.move_ip((-self.obstacle_move_speed, 0))
        if self.rect.right < 0:
            # remove all sprites first before killing the container;
            # not necessary, walls and gates should cleanup themselves
            # self.walls.empty()
            # self.gates.empty()
            self.kill()
