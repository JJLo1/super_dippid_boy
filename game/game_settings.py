"""
global game constants
"""

GAME_TITLE = "SUPER DIPPID BOY"
SCREEN_WIDTH, SCREEN_HEIGHT = 1280, 680
FPS = 60  # the fps our game should run at
BACKGROUND_IMAGE = "forest_background.png"
BACKGROUND_MUSIC = "rainy_village_8_bit_lofi.wav"  # mp3 does not work in virtualBox
BACKGROUND_MOVEMENT_SPEED = 1.5
OBSTACLE_DEFAULT_MOVEMENT_SPEED = 3.5
BORDER_HEIGHT = 50
OBSTACLE_PART_HEIGHT = 145  # preferably a denominator of SCREENHEIGHT-2*BORDERHEIGHT
MAX_HOLES_IN_OBSTACLE = 2
