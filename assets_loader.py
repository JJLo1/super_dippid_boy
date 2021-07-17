import os
import pygame


class SoundHandler:
    """
    Resource handling class for the game music and all sounds. Loads all defined sound assets on initialization.
    """

    sound_assets = ["mysterious_harp.mp3"]
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
        sound = self.sound_dict.get(sound_name)  # TODO error handling
        sound.play(-1) if play_infinite else sound.play()


class ImageHandler:
    """
    Resource handling class for all the images used in the game. Loads all defined image assets on initialization.
    """

    image_assets = ["slime.png", "slime-move.png"]
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

                self.image_dict[image_file] = (image, image.get_rect())

            except pygame.error as message:
                print('Cannot load image:', fullname)
                raise SystemExit(message)

    @staticmethod
    def get_images_from_directory(directory):
        image_list = []
        for filename in os.listdir(directory):
            image = pygame.image.load(os.path.join(directory, filename))
            image = pygame.transform.scale(image, (50, 50))
            image_list.append(image)
        return image_list

    @staticmethod
    def load_background_image(name):
        fullname = os.path.join(ImageHandler.assets_folder, name)
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
        return self.image_dict.get(image_name)  # TODO error handling
