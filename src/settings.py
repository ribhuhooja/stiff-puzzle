"""Provides classes to deal with game settings and the screen in which those settings can be changed"""

from dataclasses import dataclass
import pygame
import copy
from typing import Tuple

from common import Settings, Constants
from inputs import KeyboardState


@dataclass
class SettingsSelector:
    """Data for the settings selector, which indicates which setting to change"""

    x: float
    y: float
    width: int


class SettingsState:
    """Analogous to CoreGameState, this stores data relevant to the settings screen"""

    possible_settings = ["Resolution", "FPS"]
    possible_resolutions = [(800, 600), (1080, 720), (400, 300)]

    # how wide the selector needs be for each setting
    # this is a temporary solution because there aren't too many settings right now
    # if I add lots more settings all this information will probably be wrapped in an object
    selector_width_for_each_setting = [600, 400]

    def __init__(self, settings: Settings):
        self.changed = False
        self.selector_at = 1
        self.selector = SettingsSelector(
            Constants.game_width / 2,
            0.4 * Constants.game_height,
            self.selector_width_for_each_setting[self.selector_at],
        )
        self.temp_fps = settings.fps
        self.temp_resolution = SettingsState.possible_resolutions.index(
            (
                settings.graphics_settings.resolution_width,
                settings.graphics_settings.resolution_height,
            )
        )
        self.settings = settings

    def update(
        self, keyboard_state: KeyboardState
    ) -> Tuple[Settings, list[SettingsSelector]]:
        """Updates the settings screen depending on user input

        Stores its own copy of settings that are changed, updating self.settings only if new settings are chosen
        Temp instance variables store the settings that have been changed but not applied (by pressing enter)
        """

        keys = keyboard_state.new_keys_pressed

        new_settings = copy.deepcopy(self.settings)
        if pygame.K_s in keys and not self.changed:
            self.selector_at += 1
            self.selector_at %= len(SettingsState.possible_settings)
            self.selector.width = self.selector_width_for_each_setting[self.selector_at]
        elif pygame.K_w in keys and not self.changed:
            self.selector_at -= 1
            self.selector_at %= len(SettingsState.possible_settings)
            self.selector.width = self.selector_width_for_each_setting[self.selector_at]
        elif pygame.K_d in keys:
            if self.selector_at == 0:
                self.temp_resolution += 1
                self.temp_resolution %= len(SettingsState.possible_resolutions)
                self.changed = True
            elif self.selector_at == 1:
                self.temp_fps += 1
                self.changed = True
        elif pygame.K_a in keys:
            if self.selector_at == 0:
                self.temp_resolution -= 1
                self.temp_resolution %= len(SettingsState.possible_resolutions)
                self.changed = True
            elif self.selector_at == 1:
                self.temp_fps -= 1
                self.changed = True
        elif pygame.K_RETURN in keys:
            new_settings.fps = self.temp_fps
            (
                new_settings.graphics_settings.resolution_width,
                new_settings.graphics_settings.resolution_height,
            ) = SettingsState.possible_resolutions[self.temp_resolution]
            self.changed = False

        if self.selector_at == 0:
            self.selector.y = 0.4 * Constants.game_height
        elif self.selector_at == 1:
            self.selector.y = 0.7 * Constants.game_height

        if new_settings == self.settings:
            new_settings = None
        else:
            self.settings = copy.deepcopy(new_settings)

        return new_settings, [self.selector]
