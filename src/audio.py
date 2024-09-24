"""Deals with playing sounds and music"""

from enum import Enum
from dataclasses import dataclass
import pygame


class Sound(Enum):
    """Stores the sounds that are to be played when certain events occur"""

    START = "start_sound"
    HIT = "hit_sound"
    BLOCK = "block_sound"
    WIN = "win_sound"
    POWERUP = "powerup_sound"


class Music(Enum):
    """Stores the music for different game screens"""

    MENU = "../audio_files/menu.mp3"
    GAME_OVER = "../audio_files/game over.mp3"
    GAME_PLAY = "../audio_files/music.mp3"
    VICTORY = "../audio_files/win music.mp3"
    PRE_LAUNCH_UNIMPLEMENTED = "../audio_files/pre-launch.mp3"


@dataclass
class AudioInstructions:
    """A set of instructions which tell an Audio object what to play

    State is held in the GameState object. Each frame, it returns audio instructions that allow it to communicate with
    an Audio object and tell it what music and sounds to play
    """

    sound_queue: list[Sound]
    new_music: Music

    def merge(self, other: "AudioInstructions") -> "AudioInstructions":
        """Adds two instances of audio instructions together

        This helps when there are multiple events that produce audio instructions. Instead of having one instructions object
        and mutating it, they are just added together to a new object.
        If both have new music, the one in the caller is preserved
        """
        new_queue = self.sound_queue + other.sound_queue
        if self.new_music == None:
            new_music = other.new_music
        else:
            new_music = self.new_music

        return AudioInstructions(new_queue, new_music)


class Audio:
    """Plays sounds and music"""

    def __init__(self):
        start_sound = pygame.mixer.Sound("../audio_files/start effect.mp3")
        hit_sound = pygame.mixer.Sound("../audio_files/paddle hit.mp3")
        block_sound = pygame.mixer.Sound("../audio_files/block hit.mp3")
        win_sound = pygame.mixer.Sound("../audio_files/win sound.wav")
        powerup_sound = pygame.mixer.Sound("../audio_files/powerup sound.mp3")

        # Mappings from the enums inside audio instructions to the actual files
        # This way, the only class that deals with the actual files is Audio, and all other classes
        # only deal with an abstract representation. Very easy to switch music files this way.
        self.__to_sounds = {
            Sound.START: start_sound,
            Sound.HIT: hit_sound,
            Sound.BLOCK: block_sound,
            Sound.WIN: win_sound,
            Sound.POWERUP: powerup_sound,
        }
        self.__to_music = {
            Music.MENU: "../audio_files/menu.mp3",
            Music.GAME_OVER: "../audio_files/game over.mp3",
            Music.GAME_PLAY: "../audio_files/music.mp3",
            Music.VICTORY: "../audio_files/win music.mp3",
            Music.PRE_LAUNCH_UNIMPLEMENTED: "../audio_files/pre-launch.mp3",
        }
        self.__player = pygame.mixer.music
        self.__player.load(self.__to_music[Music.MENU])
        self.__player.play()

    def __change_music(self, music: str):
        self.__player.unload()
        self.__player.load(music)
        self.__player.play(-1)

    def run(self, instructions: AudioInstructions):
        """Takes in audio instructions and plays the sounds/changes the music, as requested"""
        for sound_repr in instructions.sound_queue:
            self.__to_sounds[sound_repr].play()

        if instructions.new_music != None:
            self.__change_music(self.__to_music[instructions.new_music])
