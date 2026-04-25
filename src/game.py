from __future__ import annotations

import pygame

from .config import GAMEPLAY, SCREEN
from .events import GameState
from .models import RunStats
from .systems import DirectionInputBuffer, RuleSystem, SaveSystem, SpawnSystem, build_default_snake
from .ui import UiRenderer


class SnakeGame:
    def __init__(self) -> None:
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN.width, SCREEN.height))
        pygame.display.set_caption(SCREEN.title)
        self.clock = pygame.time.Clock()

        self.renderer = UiRenderer(self.screen)
        self.state = GameState.MENU
        self.input_buffer = DirectionInputBuffer()

        self.snake = build_default_snake()
        self.food = SpawnSystem.spawn_food(self.snake)
        self.stats = RunStats(high_score=SaveSystem.load_high_score())

        self.tick_accumulator = 0
        self.running = True

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(SCREEN.fps)
            self._handle_events()
            self._update(dt)
            self.renderer.draw(self.state, self.snake, self.food, self.stats)
            pygame.display.flip()
        pygame.quit()

    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                self._handle_keydown(event.key)

    def _handle_keydown(self, key: int) -> None:
        if key == pygame.K_ESCAPE:
            self.running = False
            return

        if self.state is GameState.MENU and key == pygame.K_RETURN:
            self.state = GameState.RUNNING
            return

        if key == pygame.K_p and self.state is GameState.RUNNING:
            self.state = GameState.PAUSED
            return
        if key == pygame.K_p and self.state is GameState.PAUSED:
            self.state = GameState.RUNNING
            return

        if key == pygame.K_r and self.state is GameState.GAME_OVER:
            self._restart()
            return

        direction = DirectionInputBuffer.from_key(key)
        if direction is not None:
            self.input_buffer.enqueue(direction)

    def _update(self, dt: int) -> None:
        if self.state is not GameState.RUNNING:
            return

        self.stats.elapsed_ms += dt
        self.tick_accumulator += dt

        if self.food.ttl_ms > 0:
            self.food.ttl_ms -= dt
            if self.food.ttl_ms <= 0:
                self.food = SpawnSystem.spawn_food(self.snake)
                self.stats.add_log("毒果已刷新")

        if self.stats.active_boost_left_ms > 0:
            self.stats.active_boost_left_ms -= dt

        tick_ms = self._current_tick_ms()
        while self.tick_accumulator >= tick_ms:
            self.tick_accumulator -= tick_ms
            self._step()

    def _current_tick_ms(self) -> int:
        speed_bonus = (self.stats.score // GAMEPLAY.speedup_every_score) * GAMEPLAY.speedup_step_ms
        tick = GAMEPLAY.base_tick_ms - speed_bonus
        if self.stats.active_boost_left_ms > 0:
            tick -= GAMEPLAY.boost_tick_bonus_ms
        return max(tick, GAMEPLAY.min_tick_ms)

    def _step(self) -> None:
        pending_direction = self.input_buffer.pop_or_none()
        if pending_direction is not None:
            self.snake.set_direction(pending_direction)

        self.snake.move()
        head = self.snake.head

        if RuleSystem.out_of_bounds(head) or self.snake.collides_with_self():
            self.state = GameState.GAME_OVER
            self.stats.add_log("碰撞，游戏结束")
            if self.stats.score > self.stats.high_score:
                self.stats.high_score = self.stats.score
                SaveSystem.save_high_score(self.stats.high_score)
            return

        if head.x == self.food.pos.x and head.y == self.food.pos.y:
            RuleSystem.apply_food_effect(self.food, self.snake, self.stats)
            self.food = SpawnSystem.spawn_food(self.snake)

    def _restart(self) -> None:
        self.snake = build_default_snake()
        self.food = SpawnSystem.spawn_food(self.snake)
        self.input_buffer = DirectionInputBuffer()
        self.tick_accumulator = 0
        old_high = self.stats.high_score
        self.stats = RunStats(high_score=old_high)
        self.state = GameState.RUNNING
