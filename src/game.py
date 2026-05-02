from __future__ import annotations

import pygame
from random import random

from .config import GAMEPLAY, GRID, SCREEN, ROGUELIKE
from .events import GameState, MapTileType, EventType
from .models import RunStats, GameMap, Food, Vec2, Snake
from .systems import (
    DirectionInputBuffer, RuleSystem, SaveSystem, SpawnSystem,
    MapGenerator, UpgradeSystem, EventSystem, DifficultySystem,
    build_snake_with_bonus, build_ai_snake, AISystem
)
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

        self.snake = build_snake_with_bonus(0)
        self.ai_snake: Optional[Snake] = None
        self.game_map = GameMap()
        self.foods: list[Food] = []
        self.stats = RunStats(high_score=SaveSystem.load_high_score())

        self.tick_accumulator = 0
        self.ai_tick_accumulator = 0
        self.running = True
        
        self._init_new_run()

    def _init_new_run(self) -> None:
        self.snake = build_snake_with_bonus(0)
        self.stats = RunStats(
            high_score=self.stats.high_score,
            next_event_ms=EventSystem.roll_next_event_time(0)
        )
        self.ai_snake = None
        self.ai_tick_accumulator = 0
        self._generate_new_floor()

    def _generate_new_floor(self) -> None:
        self.snake = build_snake_with_bonus(self.stats.upgrades.initial_length_bonus)
        self.ai_snake = build_ai_snake(self.snake)
        self.game_map = MapGenerator.generate(self.stats.floor, self.snake)
        self.stats.floor_elapsed_ms = 0
        self.stats.has_immunity_this_floor = self.stats.upgrades.immunity_first_hit
        self.stats.used_lives_this_floor = 0
        self.stats.next_event_ms = EventSystem.roll_next_event_time(self.stats.elapsed_ms)
        self._spawn_initial_foods()
        self.input_buffer = DirectionInputBuffer()
        self.tick_accumulator = 0
        self.ai_tick_accumulator = 0
        self.stats.dash_multiplier = 1.0
        self.stats.last_direction_key_ms = 0
        
        self.stats.add_log(f"进入第 {self.stats.floor} 层")

    def _spawn_initial_foods(self) -> None:
        self.foods = []
        food = SpawnSystem.spawn_food(self.snake, self.game_map, self.stats)
        self.foods.append(food)

    def run(self) -> None:
        while self.running:
            dt = self.clock.tick(SCREEN.fps)
            self._handle_events()
            self._update(dt)
            self.renderer.draw(
                self.state, self.snake, self.foods, self.stats, 
                self.game_map, self.ai_snake
            )
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
            self._init_new_run()
            self.state = GameState.RUNNING
            return

        if key == pygame.K_p and self.state is GameState.RUNNING:
            self.state = GameState.PAUSED
            return
        if key == pygame.K_p and self.state is GameState.PAUSED:
            self.state = GameState.RUNNING
            return

        if key == pygame.K_r and self.state is GameState.GAME_OVER:
            self._init_new_run()
            self.state = GameState.MENU
            return

        if self.state is GameState.UPGRADE_SELECTION:
            self._handle_upgrade_selection(key)
            return

        if self.state is GameState.EVENT_NOTIFICATION:
            if key in (pygame.K_RETURN, pygame.K_SPACE):
                self.state = GameState.RUNNING
            return

        direction = DirectionInputBuffer.from_key(key)
        if direction is not None:
            if self.stats.has_reverse_controls():
                direction = DirectionInputBuffer.reverse(direction)
            self.input_buffer.enqueue(direction)
            
            time_since_last_key = self.stats.elapsed_ms - self.stats.last_direction_key_ms
            if time_since_last_key <= GAMEPLAY.dash_consecutive_window_ms:
                new_multiplier = self.stats.dash_multiplier - GAMEPLAY.dash_speedup_per_key
                self.stats.dash_multiplier = max(new_multiplier, GAMEPLAY.dash_max_speed_multiplier)
            self.stats.last_direction_key_ms = self.stats.elapsed_ms

    def _handle_upgrade_selection(self, key: int) -> None:
        if key == pygame.K_LEFT:
            self.stats.selected_upgrade_index = max(0, self.stats.selected_upgrade_index - 1)
        elif key == pygame.K_RIGHT:
            self.stats.selected_upgrade_index = min(
                2, self.stats.selected_upgrade_index + 1
            )
        elif key in (pygame.K_RETURN, pygame.K_SPACE):
            if self.stats.pending_upgrade_choices:
                selected = self.stats.pending_upgrade_choices[self.stats.selected_upgrade_index]
                UpgradeSystem.apply_upgrade(selected, self.snake, self.stats)
                self.stats.pending_upgrade_choices = []
                self.stats.selected_upgrade_index = 0
                self.stats.floor += 1
                self._generate_new_floor()
                self.state = GameState.RUNNING

    def _update(self, dt: int) -> None:
        if self.state in (GameState.MENU, GameState.PAUSED, GameState.GAME_OVER,
                          GameState.UPGRADE_SELECTION, GameState.EVENT_NOTIFICATION,
                          GameState.FLOOR_TRANSITION):
            return

        self.stats.elapsed_ms += dt
        self.stats.floor_elapsed_ms += dt
        self.tick_accumulator += dt
        self.ai_tick_accumulator += dt

        if not self.stats.has_freeze_time():
            for food in self.foods[:]:
                if food.ttl_ms > 0:
                    food.ttl_ms -= dt
                    if food.ttl_ms <= 0:
                        self.foods.remove(food)
                        new_food = SpawnSystem.spawn_food(self.snake, self.game_map, self.stats)
                        self.foods.append(new_food)
                        self.stats.add_log("毒果已刷新")

        if self.stats.active_boost_left_ms > 0:
            self.stats.active_boost_left_ms -= dt
        
        time_since_last_key = self.stats.elapsed_ms - self.stats.last_direction_key_ms
        if time_since_last_key > GAMEPLAY.dash_consecutive_window_ms:
            decay_amount = GAMEPLAY.dash_decay_rate_per_sec * (dt / 1000.0)
            new_multiplier = self.stats.dash_multiplier + decay_amount
            self.stats.dash_multiplier = min(new_multiplier, 1.0)

        self.stats.clean_inactive_events()

        if self.stats.elapsed_ms >= self.stats.next_event_ms:
            self._trigger_random_event()

        if self.stats.has_double_food() and len(self.foods) < 2:
            if random() < 0.02:
                new_food = SpawnSystem.spawn_food(self.snake, self.game_map, self.stats)
                self.foods.append(new_food)

        if self.stats.floor_elapsed_ms >= ROGUELIKE.floor_duration_sec * 1000:
            self._enter_upgrade_selection()
            return

        tick_ms = self._current_tick_ms()
        
        if RuleSystem.is_in_slow_zone(self.snake, self.game_map, self.stats):
            tick_ms = int(tick_ms * GAMEPLAY.slow_zone_tick_multiplier)
        
        while self.tick_accumulator >= tick_ms:
            self.tick_accumulator -= tick_ms
            if not self._step():
                return
        
        ai_tick_ms = int(tick_ms * 1.5)
        while self.ai_tick_accumulator >= ai_tick_ms:
            self.ai_tick_accumulator -= ai_tick_ms
            if not self._ai_step():
                return

    def _current_tick_ms(self) -> int:
        return DifficultySystem.get_tick_ms_for_floor(self.stats.floor, self.stats)

    def _trigger_random_event(self) -> None:
        event = EventSystem.generate_random_event(self.stats.elapsed_ms)
        
        definition = EventSystem.EVENT_DEFINITIONS.get(event.event_type, {})
        if definition.get("instant", False):
            EventSystem.apply_instant_event(event, self.snake, self.stats)
        else:
            self.stats.active_events.append(event)
        
        self.stats.pending_event_notification = event
        self.stats.next_event_ms = EventSystem.roll_next_event_time(self.stats.elapsed_ms)
        self.state = GameState.EVENT_NOTIFICATION

    def _enter_upgrade_selection(self) -> None:
        choices = UpgradeSystem.generate_choices(self.stats)
        self.stats.pending_upgrade_choices = choices
        self.stats.selected_upgrade_index = 0
        self.state = GameState.UPGRADE_SELECTION

    def _step(self) -> bool:
        pending_direction = self.input_buffer.pop_or_none()
        if pending_direction is not None:
            self.snake.set_direction(pending_direction)

        old_head = self.snake.head.copy()
        self.snake.move()
        head = self.snake.head

        head = self._handle_wrapping(head)
        self.snake.body[0] = head

        teleport_dest = self.game_map.get_teleport_destination(head)
        if teleport_dest is not None:
            self.snake.body[0] = teleport_dest.copy()
            head = teleport_dest
            if self.stats.upgrades.portal_master:
                self.stats.active_boost_left_ms += 2000
            self.stats.add_log("使用传送门")

        if self.game_map.is_blocking(head):
            if RuleSystem.handle_collision(self.snake, self.stats):
                self._game_over()
                return False
            self.snake.body[0] = old_head
            return True

        if self.snake.collides_with_self():
            if RuleSystem.handle_collision(self.snake, self.stats):
                self._game_over()
                return False
            return True

        if self.ai_snake is not None:
            if AISystem.check_player_collision_with_ai(self.snake, self.ai_snake):
                self.stats.add_log("撞到了机器蛇！")
                self._game_over()
                return False

        for food in self.foods[:]:
            if head.x == food.pos.x and head.y == food.pos.y:
                RuleSystem.apply_food_effect(food, self.snake, self.stats)
                self.foods.remove(food)
                new_food = SpawnSystem.spawn_food(self.snake, self.game_map, self.stats)
                self.foods.append(new_food)
                break

        return True

    def _ai_step(self) -> bool:
        if self.ai_snake is None:
            return True

        direction = AISystem.choose_direction(self.ai_snake, self.snake, self.game_map)
        self.ai_snake.set_direction(direction)

        old_body = [Vec2(s.x, s.y) for s in self.ai_snake.body]

        self.ai_snake.move()
        ai_head = self.ai_snake.head

        ai_head = AISystem.wrap_position(ai_head)
        self.ai_snake.body[0] = ai_head

        has_collision, is_tail_bite = AISystem.is_any_collision(self.ai_snake, self.snake)
        
        if has_collision:
            if is_tail_bite:
                self.stats.add_log("机器蛇咬到了你的尾部！")
                self._game_over()
                return False
            else:
                self.ai_snake.body = old_body
                return True

        return True

    def _handle_wrapping(self, pos: Vec2) -> Vec2:
        new_x = pos.x
        new_y = pos.y

        if pos.x < 0:
            new_x = GRID.cols - 1
        elif pos.x >= GRID.cols:
            new_x = 0

        if pos.y < 0:
            new_y = GRID.rows - 1
        elif pos.y >= GRID.rows:
            new_y = 0

        return Vec2(new_x, new_y)

    def _game_over(self) -> None:
        self.state = GameState.GAME_OVER
        self.stats.add_log("游戏结束")
        if self.stats.score > self.stats.high_score:
            self.stats.high_score = self.stats.score
            SaveSystem.save_high_score(self.stats.high_score)
