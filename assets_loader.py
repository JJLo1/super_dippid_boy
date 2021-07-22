import os
import sys
import pygame
from game_settings import BACKGROUND_MUSIC


class SoundHandler:
    """
    Resource handling class for the game music and all sounds. Loads all defined sound assets on initialization.
    """

    sound_assets = [BACKGROUND_MUSIC]
    sound_dict = dict()

    def __init__(self, assets_folder="assets"):
        self._assets_folder = assets_folder
        self._load_sounds()

    def _load_sounds(self):
        if not pygame.mixer or not pygame.mixer.get_init():
            raise SystemExit("Failed to load the pygame sound modules!")

        for sound_file in self.sound_assets:
            fullname = os.path.join(self._assets_folder, sound_file)
            try:
                sound = pygame.mixer.Sound(fullname)
                self.sound_dict[sound_file] = sound
            except pygame.error as message:
                print('Cannot load sound:', fullname)
                raise SystemExit(message)

    def play_sound(self, sound_name: str, play_infinite=False):
        sound = self.sound_dict.get(sound_name)
        if not sound:
            raise SystemExit(f"Error while trying to load asset! Sound '{sound_name}' not found!")
        # turn music a little bit down
        new_volume = sound.get_volume() / 2
        sound.set_volume(new_volume)
        sound.play(-1) if play_infinite else sound.play()

    def stop_sound(self, sound_name: str):
        sound = self.sound_dict.get(sound_name)
        if not sound:
            sys.stderr.write(f"Error while trying to stop sound '{sound_name}'!")
            return
        sound.fadeout(3)


class ImageHandler:
    """
    Resource handling class for all the images used in the game. Loads all defined image assets on initialization.
    """

    image_assets = ["wooden_material.png", "portal.png", "gates/line.png", "gates/triangle.png", "gates/rectangle.png"]
    image_dict = dict()
    assets_folder = "assets"

    def __init__(self, assets_folder="assets"):
        self.assets_folder = assets_folder
        self._load_images()

    def _load_images(self):
        for image_file in self.image_assets:
            fullname = os.path.join(self.assets_folder, image_file)
            try:
                image = pygame.image.load(fullname)
                if image.get_alpha() is None:
                    # Convert returns us a new Surface of the image, but now converted to the same pixel format as our
                    # display. Since the images will be the same format at the screen, they will blit very quickly.
                    # If we did not convert, the blit() function is slower.
                    image = image.convert()
                else:
                    image = image.convert_alpha()

                self.image_dict[image_file] = image

            except pygame.error as message:
                print('Cannot load image:', fullname)
                raise SystemExit(message)

    # Returning images for the character depending on the current form
    @staticmethod
    def get_images_for_form(form):
        print(f"get images for form : {form}")
        if form == "rectangle":
            directory = "assets/Rectangle"
        if form == "triangle":
            directory = "assets/Triangle"
        else:
            directory = "assets/Circle"
        image_list = []
        for filename in os.listdir(directory):
            image = pygame.image.load(os.path.join(directory, filename))
            image = pygame.transform.scale(image, (50, 50))
            image_list.append(image)
        return image_list

    @staticmethod
    def load_background_image():
        background_image = "forest_background.png"
        fullname = os.path.join(ImageHandler.assets_folder, background_image)
        try:
            image = pygame.image.load(fullname)
            if image.get_alpha() is None:
                image = image.convert()
            else:
                image = image.convert_alpha()
        except pygame.error as message:
            print('Cannot load background image:', fullname)
            raise SystemExit(message)

        return image, image.get_rect()

    def get_image(self, image_name: str):
        image = self.image_dict.get(image_name)
        if not image:
            raise SystemExit(f"Error while trying to load asset! Image '{image_name}' not found!")
        return image
