"""Provides a class to hold the state data for the program"""

from enum import Enum
from typing import Tuple
import copy
import pygame

from common import GameFsmState, Constants
from settings import SettingsState
from audio import AudioInstructions, Music, Sound
from graphics import GraphicsInstructions
from inputs import KeyboardState
from core_game_state import CoreGameState
from screen_content import screen_content


class GameState:
    """Holds all state data for the program"""

    def __init__(self):
        self.game_fsm_state = GameFsmState.MENU
        self.game_exit = False
        self.settings = copy.deepcopy(Constants.default_settings)
        self.settings_state = None

    def update(
        self, total_delta_t: float, keyboard_state: KeyboardState
    ) -> Tuple[AudioInstructions, GraphicsInstructions]:
        """Updates the game state data, taking in the time between frames and keyboard inputs"""

        # The keys currently pressed
        keys = keyboard_state.get_keys()

        # This will be built upon and return to Graphics to play
        graphics_instructions = GraphicsInstructions([], [], None)

        next_fsm_state = self.__next_fsm_state(keyboard_state)

        transition_audio_instructions = AudioInstructions([], None)
        collision_sounds = AudioInstructions([], None)

        # If appropriate, do a state transition and queue all the required audiovisual changes
        if next_fsm_state != None:
            transition_audio_instructions = state_transition_audio(
                self.game_fsm_state, next_fsm_state
            )
            self.__on_transition(next_fsm_state)

        objects = []
        ui_elements = []

        # If the game is being played (i.e. not in a menu screen type of state)
        # Update the game physics and get the objects to render and sounds to play from that
        if self.game_fsm_state in [
            GameFsmState.PLAY,
            GameFsmState.PAUSE,
            GameFsmState.PRE_PLAY,
        ]:
            sounds, objects = self.core_game_state.update(
                total_delta_t, keys, self.game_fsm_state
            )
            collision_sounds = AudioInstructions(sounds, None)

        # deals with the settings menu state
        elif self.game_fsm_state == GameFsmState.SETTINGS:
            # Update settings if needed
            new_settings, ui_elements = self.settings_state.update(keyboard_state)
            if new_settings != None:
                # Settings mutates its own copy of the settings, only updating GameState's copy of settings
                # Once a change is made
                self.settings = copy.deepcopy(new_settings)
                graphics_instructions += GraphicsInstructions(
                    [], [], new_settings.graphics_settings
                )

        # Stores the UI elements to render depending on the current screen
        screen_ui = (
            screen_content(self.game_fsm_state)
            if self.game_fsm_state != GameFsmState.SETTINGS
            else screen_content(GameFsmState.SETTINGS, self.settings_state)
        )
        screen_graphics = GraphicsInstructions(
            objects,
            screen_ui,
        )
        ui_graphics = GraphicsInstructions([], ui_elements)

        # Merge the graphics and audio instructions from separate sources into singular returnable objects
        audio_instructions = transition_audio_instructions.merge(collision_sounds)
        graphics_instructions += screen_graphics + ui_graphics

        return audio_instructions, graphics_instructions

    def __initialize_game(self):
        """Called when a game first starts, building a CoreGameState object"""
        self.core_game_state = CoreGameState()

    def __next_fsm_state(self, keyboard_state: KeyboardState) -> GameFsmState | None:
        """Checks whether we need to do a screen transition. If yes, it returns the next GameFsmState"""
        keys = keyboard_state.get_keys()

        if self.game_fsm_state == GameFsmState.MENU:
            if pygame.K_p in keyboard_state.new_keys_pressed:
                return GameFsmState.PRE_PLAY
            elif pygame.K_q in keys:
                return GameFsmState.QUIT
            elif pygame.K_i in keys:
                return GameFsmState.INSTRUCTIONS
            elif pygame.K_s in keys:
                return GameFsmState.SETTINGS

        elif self.game_fsm_state == GameFsmState.INSTRUCTIONS:
            if pygame.K_m in keys:
                return GameFsmState.MENU

        elif self.game_fsm_state == GameFsmState.SETTINGS:
            if pygame.K_m in keys:
                return GameFsmState.MENU

        elif self.game_fsm_state in [
            GameFsmState.GAME_OVER,
            GameFsmState.GAME_WIN,
        ]:
            if pygame.K_r in keys:
                return GameFsmState.PRE_PLAY
            elif pygame.K_q in keys:
                return GameFsmState.QUIT

        elif self.game_fsm_state == GameFsmState.PLAY:
            if self.core_game_state.game_over():
                return GameFsmState.GAME_OVER
            elif self.core_game_state.game_win():
                return GameFsmState.GAME_WIN
            elif self.core_game_state.start_new_life():
                return GameFsmState.PRE_PLAY
            elif pygame.K_p in keyboard_state.new_keys_pressed:
                return GameFsmState.PAUSE

        elif self.game_fsm_state == GameFsmState.PAUSE:
            if pygame.K_p in keyboard_state.new_keys_pressed:
                return GameFsmState.PLAY

        elif self.game_fsm_state == GameFsmState.PRE_PLAY:
            if pygame.K_l in keys:
                return GameFsmState.PLAY

        if keyboard_state.quit:
            self.game_exit = True

    def __on_transition(self, next_state: GameFsmState):
        """If we do need to do a screen transition, this executes the necessary effects"""
        if next_state == GameFsmState.PRE_PLAY:
            if self.game_fsm_state in [
                GameFsmState.MENU,
                GameFsmState.GAME_OVER,
                GameFsmState.GAME_WIN,
            ]:
                self.__initialize_game()
            elif self.game_fsm_state == GameFsmState.PLAY:
                self.core_game_state.make_new_ball()

        elif (
            next_state == GameFsmState.PLAY
            and self.game_fsm_state == GameFsmState.PRE_PLAY
        ):
            self.core_game_state.ball.y_vel = Constants.init_y_vel_ball

        elif next_state == GameFsmState.GAME_OVER:
            self.core_game_state = None

        elif next_state == GameFsmState.SETTINGS:
            self.settings_state = SettingsState(self.settings)

        if next_state == GameFsmState.QUIT:
            self.game_exit = True

        self.game_fsm_state = next_state


def state_transition_audio(
    current_state: GameFsmState,
    target_state: GameFsmState,
) -> AudioInstructions:
    """Returns audio instructions corresponding to a state transition i.e. changing the music"""
    sounds = []
    new_music = None
    if target_state == GameFsmState.GAME_WIN:
        sounds.append(Sound.WIN)
        new_music = Music.VICTORY
    elif target_state == GameFsmState.GAME_OVER:
        new_music = Music.GAME_OVER
    elif target_state == GameFsmState.PRE_PLAY and current_state != GameFsmState.PLAY:
        new_music = Music.GAME_PLAY
    return AudioInstructions(sounds, new_music)
