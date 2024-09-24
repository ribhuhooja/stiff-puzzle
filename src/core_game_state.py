"""Provide a class to hold the state of actual level objects"""

from dataclasses import dataclass
from enum import Enum
import random
from typing import Tuple
import pygame

from common import (
    Colors,
    Constants,
    Block,
    Paddle,
    Ball,
    GameFsmState,
    BallModifier,
    BlockType,
    PowerupType,
    Powerup,
    GameObject,
)
from audio import Sound


class CoreGameState:
    """Holds the state for the game objects, independent of other considerations

    This class only exists when the game is being played (as opposed to being in a menu) and deals with
    updating the physics of the game, collision detection, removing blocks, spawning powerups, etc.
    """

    def __init__(self):
        self.lives = Constants.initial_lives
        self.paddle = Paddle(
            Constants.game_width / 2 - 50,
            0.9 * Constants.game_height,
            100,
            10,
            0,
            self.lives,
        )
        self.ball = Ball(
            Constants.game_width / 2,
            self.paddle.y - Constants.ball_radius,
            random.uniform(
                -1 * Constants.init_max_x_vel_ball,
                Constants.init_max_x_vel_ball,
            ),
            0,
            Constants.ball_radius,
        )

        self.blocks = self.__generate_blocks(9, 5)
        self.__set_special_blocks()
        self.__update_block_effects()
        self.powerups = []
        self.new_life = False

    def update(
        self, total_delta_t: float, keys: list[int], game_fsm_state
    ) -> Tuple[list[Sound], list[GameObject]]:
        """Given the current gameFSMstate, update the game physics and data. Also return the sounds to play and objects to render"""
        delta_t = total_delta_t / Constants.update_repetitions
        output_sounds = []

        # Update repetitions: when the time step is too large, the physics does not work correctly
        # because the forces are too large and cause the paddle to overshoot. The only way to reduce timestep
        # is to increase the framerate of the game, which is not feasible beyond a certain limit.
        # So instead, the physics of the game is updated at much smaller timesteps, multiple times each frame

        if game_fsm_state == GameFsmState.PLAY:
            for _ in range(Constants.update_repetitions):
                self.__update_game_physics(delta_t, keys, output_sounds)

        return output_sounds, self.__game_objects_to_render()

    def game_over(self) -> bool:
        """Returns whether the game is over"""
        condition = self.lives == 0
        return condition

    def game_win(self) -> bool:
        """Returns whether the game has been won"""
        condition = len(self.blocks) == 0
        return condition

    def start_new_life(self) -> bool:
        """Returns whether to continue the game with one fewer life

        Each time the bal falls off, one life is removed. At this point, the game goes into the
        PRE_PLAY state and does not resume until L is pressed and the ball is launched. This function helps
        GameState know when to do that.
        """
        if self.new_life == True:
            self.new_life = False
            return True
        else:
            return False

    def make_new_ball(self):
        """When one ball falls off, make another one"""
        self.ball = Ball(
            self.paddle.x + self.paddle.width / 2,
            self.paddle.y - Constants.ball_radius,
            random.uniform(
                -1 * Constants.init_max_x_vel_ball,
                Constants.init_max_x_vel_ball,
            ),
            0,
            Constants.ball_radius,
        )

    def __update_game_physics(
        self, delta_t: float, keys: list[int], output_sounds: list[Sound]
    ):
        """Updates the game physics based on how much time has passed and what keys are pressed. Returns sounds."""
        if pygame.K_a in keys:
            impulse_sign = -1
        elif pygame.K_d in keys:
            impulse_sign = +1
        else:
            impulse_sign = 0

        self.paddle.x_vel += delta_t * (
            impulse_sign * Constants.user_impulse_per_millisecond
            - Constants.air_resistance_coefficient * self.paddle.x_vel
        )
        self.paddle.x += delta_t * self.paddle.x_vel

        if self.paddle.x > Constants.game_width - self.paddle.width:
            self.paddle.x = Constants.game_width - self.paddle.width
        elif self.paddle.x < 0:
            self.paddle.x = 0

        if self.ball != None:
            self.__update_ball(self.ball, delta_t, output_sounds)

        for powerup in self.powerups:
            self.__update_powerup(powerup, delta_t, output_sounds)

    def __game_objects_to_render(self) -> list[GameObject]:
        """Returns a list of objects for Graphics to render"""
        return [self.paddle] + [self.ball] + self.blocks + self.powerups

    def __get_block_from_id(self, id: Tuple[int, int]) -> Block | None:
        """Finds a block from its index (id) in the list of blocks

        We cannot simply index into the list of blocks, because that list mutates as blocks are destroyed.
        The block ID is the INTIAL index of the block, and doesn't change. Its actual index changes whenever any block is destroyed.
        """
        for block in self.blocks:
            if block.block_id == id:
                return block

        return None

    def __generate_blocks(self, num_cols, num_rows) -> list[Block]:
        """Generates the blocks for a level"""
        blocks = []
        gap = 2
        for i in range(num_cols):
            for j in range(num_rows):
                blocks.append(
                    Block(
                        (Constants.game_width / num_cols) * i + gap,
                        (Constants.game_height / (3 * num_rows)) * j + gap,
                        (Constants.game_width / num_cols) - 2 * gap,
                        (Constants.game_height / (3 * num_rows)) - 2 * gap,
                        (i, j),
                        BlockType.NORMAL,
                        1,
                        0,
                        Colors.generate_random_block_color(),
                    )
                )

        return blocks

    def __set_special_blocks(self):
        """Creates special blocks

        For now the location of special blocks is either random (powerup blocks)
        or hardcoded (protector blocks). Later, this will be stored in a LevelData class
        and blocks will be generated from there
        """
        for block in self.blocks:
            block.block_type = BlockType.normal_or_powerup(
                Constants.powerup_probability
            )

            if block.block_id[1] in [0, 2]:
                block.health += 1
            if block.block_id in [(4, 2)]:
                block.block_type = BlockType.PROTECTOR

    def __collision_check_ball_block(self, ball: Ball, block: Block) -> bool:
        """Checks for collision between a ball and a block. Also executes the effects of the collision.

        Collision effects include making the ball bounce back, destroying the block or reducing its health.
        When a ball is PIERCING, it reduces the amount of blocks that can be pierced before bouncing back.
        The return value is used by __update_physics() to decide whether to queue a sound to be played or not.
        """
        collision_type = None
        if (
            block.x - ball.radius < ball.x < block.x + block.width + ball.radius
            and block.y - ball.radius < ball.y < block.y + block.height + ball.radius
        ):
            if ball.y > block.y + block.height and ball.y_vel < 0:
                collision_type = "vertical"
            elif ball.y < block.y and ball.y_vel > 0:
                collision_type = "vertical"
            elif ball.x > block.x + block.width and ball.x_vel < 0:
                collision_type = "horizontal"
            elif ball.x < block.x and ball.x_vel > 0:
                collision_type = "horizontal"

        if collision_type != None:
            if ball.modifier == BallModifier.PIERCING:
                if (ball.blocks_pierced < ball.max_blocks_can_pierce) and (
                    block.health <= 1 or block.protection <= 0
                ):
                    ball.blocks_pierced += 1
                else:
                    ball.blocks_pierced = 0
                    if collision_type == "vertical":
                        ball.y_vel *= -1
                    elif collision_type == "horizontal":
                        ball.x_vel *= -1

            else:
                if collision_type == "vertical":
                    ball.y_vel *= -1
                elif collision_type == "horizontal":
                    ball.x_vel *= -1

            return True  # This should flag the block sound to be played

    def __collision_check_ball_wall(self, ball: Ball):
        """Executes collision effects if a ball hits a wall"""
        if ball.x < ball.radius and ball.x_vel < 0:
            ball.x_vel *= -1
        elif ball.x > Constants.game_width - ball.radius and ball.x_vel > 0:
            ball.x_vel *= -1
        if ball.y < ball.radius and ball.y_vel < 0:
            ball.y_vel *= -1

    def __collision_check_ball_paddle(self, ball: Ball, paddle: Paddle) -> bool:
        """Executes collision effects if a ball hits the paddle. Returns true if it does.

        The return calue is used by __update_physics to check whether the paddle_hit sound should be played or not
        """
        collision_occurred = False
        if ball.y_vel <= 0:
            return False

        if (
            paddle.y - ball.radius <= ball.y <= paddle.y + paddle.height
            and paddle.x - ball.radius
            <= ball.x
            <= paddle.x + paddle.width + ball.radius
        ):
            if ball.y <= paddle.y:
                ball.y_vel *= -1
                ball.x_vel += paddle.x_vel / 5
                collision_occurred = True
            elif ball.y >= paddle.y and (
                ball.x < paddle.x or ball.x > paddle.x + paddle.width
            ):
                ball.y_vel *= -1
                ball.x_vel += paddle.x_vel
                collision_occurred = True
        return collision_occurred  # This should flag the paddle sound to be played

    def __collision_check_powerup_paddle(self, powerup: Powerup, paddle: Paddle):
        """Executes collision effects when the paddle cllects a powerup

        The return value is used to queue a sound to be played
        """
        if (
            paddle.y - powerup.hitbox_radius
            <= powerup.y
            <= paddle.y + paddle.height + powerup.hitbox_radius
            and paddle.x - powerup.hitbox_radius
            <= powerup.x
            <= paddle.x + paddle.width + powerup.hitbox_radius
        ):
            self.powerups.remove(powerup)
            return True

    def __update_block_from_collision(self, block: Block, output_sounds: list[Sound]):
        """Updates the state of a block upon collision"""
        if block.protection == 0:
            block.health -= 1

        if block.health <= 0:
            self.__break_block(block)
            output_sounds.append(Sound.BLOCK)
            self.__update_block_effects()

    def __update_block_effects(self):
        """Each time a block is destroyed, other blocks near it may be changed

        Currently this deals with protector blocks, because when they are destroyed they stop protecting
        the blocks below them
        """
        # Reset all block effects, and then reapply them if necessary
        # This is slightly awkward, but is currently the quickest way to do this because the protector block
        # which potentially got destroyed no longer exists. So there is no way to query its neighbors
        # If more complex effects are added this method will have to change
        for block in self.blocks:
            block.protection = 0

        for block in self.blocks:
            if block.block_type == BlockType.PROTECTOR:
                i, j = block.block_id
                self.__get_block_from_id((i, j + 1)).protection += 1
                self.__get_block_from_id((i - 1, j + 1)).protection += 1
                self.__get_block_from_id((i + 1, j + 1)).protection += 1

    def __break_block(self, block: Block):
        """Breaks a block, removing it from the list of blocks

        While this is a simple way to remove a block from the game, it causes issues, such as the __update_block_effects
        method being needlessly complicated. It also precludes effects like reviving blocks. This method will probably be
        changed to keep a block in the list but just "switch it off." As an added bonus, that will reduce the need for the
        (extremely awkward) __get_block_by_id method
        """
        if block.block_type == BlockType.POWERUP:
            self.__spawn_powerup(
                block.x + block.width / 2,
                block.y + block.height / 2,
                block.height / 2,
            )
        self.blocks.remove(block)

    def __update_ball(self, ball: Ball, delta_t: float, output_sounds: list[Sound]):
        """Updates the ball data, depending on time step. Queues sounds to be played if necessary.

        Passing around a mutable output sound object is slightly awkward, but the simplest way to do this because
        it persists over a single frame whereas update methods are called 50 times a frame
        """
        ball.y_vel += Constants.gravity * delta_t
        if ball.x_vel > 0.1:
            ball.x_vel = 0.1
        elif ball.x_vel < -0.1:
            ball.x_vel = -0.1

        if ball.y > Constants.game_height + ball.radius:
            self.lives -= 1
            self.__new_life()

        else:
            ball.y += ball.y_vel * delta_t
            ball.x += ball.x_vel * delta_t
            if self.__collision_check_ball_paddle(ball, self.paddle):
                output_sounds.append(Sound.HIT)
            self.__collision_check_ball_wall(ball)
            for block in self.blocks:
                if self.__collision_check_ball_block(ball, block):
                    self.__update_block_from_collision(block, output_sounds)

            if ball.modifier == BallModifier.PIERCING:
                ball.modifier_active_for -= delta_t
                if ball.modifier_active_for <= 0:
                    ball.modifier_active_for = 0
                    ball.modifier = None

    def __spawn_powerup(self, x, y, hitbox_radius):
        """Spawns a powerup"""
        ptype = random.choices(list(PowerupType), Constants.powerup_type_probabilities)[
            0
        ]
        self.powerups.append(Powerup(ptype, x, y, hitbox_radius))

    def __update_powerup(
        self, powerup: Powerup, delta_t: float, output_sounds: list[Sound]
    ):
        """Updates te location of a powerup. If it hits, executes the effect"""
        powerup.y += delta_t * Constants.powerup_fall_speed
        if self.__collision_check_powerup_paddle(powerup, self.paddle):
            output_sounds.append(Sound.POWERUP)
            if powerup.powerup_type == PowerupType.PIERCING:
                self.ball.make_piercing(3000, 1)
            elif powerup.powerup_type == PowerupType.LIFE:
                self.lives += 1
                self.paddle.lives += 1

    def __new_life(self):
        """Removes the current ball from play, and does some data bookkeeping

        This is called when a ball falls off the screen. Because CoreGameState does not have access to the
        state data requird to actually start a new life, it simply queues the change (as a boolean variable).
        This is checked by the GameState class (which does have access to the required state data) which then
        executes the necessary code.
        """
        self.paddle.lives = self.lives
        self.ball = None
        self.new_life = True
