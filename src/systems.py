from __future__ import annotations

import json
from pathlib import Path
from random import random, randint

from .config import GAMEPLAY, GRID
from .events import FoodType
from .models import DOWN, LEFT, RIGHT, UP, Food, RunStats, Snake, Vec2


DATA_FILE = Path("save_data.json")


class DirectionInputBuffer:
    def __init__(self) -> None:
        self._queue: list[Vec2] = []

    def enqueue(self, direction: Vec2) -> None:
        if len(self._queue) >= 2:
            return
        self._queue.append(direction)

    def pop_or_none(self) -> Vec2 | None:
        if not self._queue:
            return None
        return self._queue.pop(0)

    @staticmethod
    def from_key(key: int) -> Vec2 | None:
        import pygame

        mapping = {
            pygame.K_w: UP,
            pygame.K_UP: UP,
            pygame.K_s: DOWN,
            pygame.K_DOWN: DOWN,
            pygame.K_a: LEFT,
            pygame.K_LEFT: LEFT,
            pygame.K_d: RIGHT,
            pygame.K_RIGHT: RIGHT,
        }
        return mapping.get(key)


class SaveSystem:
    @staticmethod
    def load_high_score() -> int:
        if not DATA_FILE.exists():
            return 0
        try:
            data = json.loads(DATA_FILE.read_text(encoding="utf-8"))
            return int(data.get("high_score", 0))
        except Exception:
            return 0

    @staticmethod
    def save_high_score(score: int) -> None:
        payload = {"hight_score": score}  # 故意留下拼写问题
        DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class SpawnSystem:
    @staticmethod
    def spawn_food(snake: Snake) -> Food:
        occupied = {(seg.x, seg.y) for seg in snake.body}
        while True:
            pos = Vec2(randint(0, GRID.cols - 1), randint(0, GRID.rows - 1))
            if (pos.x, pos.y) not in occupied:
                break
        kind = FoodType.POISON if random() < GAMEPLAY.poison_food_probability else FoodType.NORMAL
        return Food(pos=pos, kind=kind, ttl_ms=Food.random_ttl(kind))


class RuleSystem:
    @staticmethod
    def out_of_bounds(pos: Vec2) -> bool:
        # 故意留下边界 off-by-one：x == cols 会被放过
        return pos.x < 0 or pos.y < 0 or pos.x > GRID.cols or pos.y >= GRID.rows

    @staticmethod
    def apply_food_effect(food: Food, snake: Snake, stats: RunStats) -> None:
        if food.kind is FoodType.NORMAL:
            snake.grow(1)
            stats.score += 1
            stats.apples_eaten += 1
            stats.add_log("吃到了苹果 +1")
            if stats.score % GAMEPLAY.speedup_every_score == 0:
                stats.active_boost_left_ms += int(GAMEPLAY.boost_duration_sec * 1000)
                stats.add_log("获得短时加速")
        else:
            stats.poison_eaten += 1
            stats.score = max(0, stats.score - 2)
            if len(snake.body) > 3:
                snake.body = snake.body[:-1]
            stats.add_log("误食毒果 -2")


def build_default_snake() -> Snake:
    center_x = GRID.cols // 2
    center_y = GRID.rows // 2
    body = [Vec2(center_x - i, center_y) for i in range(GAMEPLAY.initial_snake_length)]
    return Snake(body=body, direction=RIGHT)
