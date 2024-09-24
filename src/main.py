"""Executes all the code and calls upon the other modules"""

import pygame


from game_state import GameState
from graphics import Graphics
from audio import Audio
from inputs import KeyboardState


def check_invariants(game: GameState, graphics: Graphics):
    """Makes sure that certain conditions are true, so that the game is consistent"""
    assert game.settings.graphics_settings == graphics.graphics_settings
    if game.settings_state != None:
        assert game.settings == game.settings_state.settings


def GameLoop():
    """The main loop of the game. Initializes classes and repeatedly updates them"""
    game = GameState()
    clock = pygame.time.Clock()
    audio = Audio()
    graphics = Graphics(game.settings.graphics_settings)
    keyboard_state = KeyboardState()

    while not game.game_exit:
        clock.tick(game.settings.fps)

        total_delta_t = clock.get_time()

        audio_instructions, graphics_instructions = game.update(
            total_delta_t, keyboard_state
        )

        audio.run(audio_instructions)
        graphics.render(graphics_instructions)

        keyboard_state.handle_pygame_events()
        check_invariants(game, graphics)


def main():
    """Puts everything together and runs the program"""
    pygame.init()
    pygame.display.set_caption("Breakout")
    GameLoop()
    pygame.quit()


if __name__ == "__main__":
    main()
