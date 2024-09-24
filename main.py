"""Executes all the code and calls upon the other modules"""

import pygame


from inputs import KeyboardState

FPS = 60


def GameLoop():
    """The main loop of the game. Initializes classes and repeatedly updates them"""
    game = GameState()
    clock = pygame.time.Clock()
    graphics = Graphics(game.settings.graphics_settings)
    keyboard_state = KeyboardState()

    while not game.game_exit:
        clock.tick(FPS)

        total_delta_t = clock.get_time()

        audio_instructions, graphics_instructions = game.update(
            total_delta_t, keyboard_state
        )

        graphics.render(graphics_instructions)

        keyboard_state.handle_pygame_events()


def main():
    """Puts everything together and runs the program"""
    pygame.init()
    pygame.display.set_caption("Breakout")
    GameLoop()
    pygame.quit()


if __name__ == "__main__":
    main()
