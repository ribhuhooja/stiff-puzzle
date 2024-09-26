"""Executes all the code and calls upon the other modules"""

import pygame


from inputs import KeyboardState

FPS = 60


def render(screen, block):
    pygame.draw.rect(screen, (0, 0, 0), (0, 0, 800, 600))
    pygame.draw.rect(screen, (255, 255, 255), block)
    pygame.display.update()


def GameLoop():
    """The main loop of the game. Initializes classes and repeatedly updates them"""
    clock = pygame.time.Clock()
    screen = pygame.display.set_mode((800, 600))
    keyboard_state = KeyboardState()

    block_x = 400
    block_y = 500

    block_vx = 0  # velocity
    block_ax = 0  # acceleration

    while not keyboard_state.quit:
        clock.tick(FPS)

        total_delta_t = clock.get_time()

        render(screen, (block_x, block_y, 50, 25))

        keyboard_state.handle_pygame_events()

        if pygame.K_d in keyboard_state.get_keys():
            block_ax = 0.0001
        elif pygame.K_a in keyboard_state.get_keys():
            block_ax = -0.0001
        else:
            block_ax = -1 * block_vx  # drag

        block_vx += block_ax * total_delta_t
        block_x += block_vx * total_delta_t

        print(block_vx)


def main():
    """Puts everything together and runs the program"""
    pygame.init()
    pygame.display.set_caption("Breakout")
    GameLoop()
    pygame.quit()


if __name__ == "__main__":
    main()
