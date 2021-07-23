#!/usr/bin/python3
# -*- coding:utf-8 -*-

import argparse
import random
import pygame
from game.super_dippid_boy import SuperDippidBoy


# check imports
if not pygame.font:
    raise SystemExit("[Error]: Pygame Fonts disabled")
if not pygame.mixer:
    raise SystemExit("[Error]: Pygame Sound disabled")


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
