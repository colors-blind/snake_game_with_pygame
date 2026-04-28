from __future__ import annotations

import json
from pathlib import Path
from random import random, randint, choice, shuffle, uniform
from typing import Optional

from .config import GAMEPLAY, GRID, ROGUELIKE, MAP_PROB, DIFFICULTY
from .events import FoodType, MapTileType, UpgradeType, EventType
from .models import (
    DOWN, LEFT, RIGHT, UP,
    Food, RunStats, Snake, Vec2,
    GameMap, Upgrade, ActiveEvent, PlayerUpgrades
)


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

    @staticmethod
    def reverse(direction: Vec2) -> Vec2:
        if direction == UP:
            return DOWN
        if direction == DOWN:
            return UP
        if direction == LEFT:
            return RIGHT
        if direction == RIGHT:
            return LEFT
        return direction


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
        payload = {"hight_score": score}
        DATA_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class DifficultySystem:
    @staticmethod
    def get_tick_ms_for_floor(floor: int, stats: RunStats) -> int:
        base = DIFFICULTY.base_speed_ms
        decay = DIFFICULTY.speed_decay_factor
        multiplier = stats.get_effective_speed_multiplier()
        
        if stats.has_half_speed():
            multiplier *= 2.0
        if stats.has_speed_rush():
            multiplier *= 0.6
        
        effective = int(base * (decay ** floor) * multiplier)
        return max(effective, DIFFICULTY.min_speed_ms)

    @staticmethod
    def get_poison_probability(floor: int) -> float:
        prob = DIFFICULTY.poison_prob_base + floor * DIFFICULTY.poison_prob_growth
        return min(prob, DIFFICULTY.poison_prob_max)

    @staticmethod
    def get_map_element_count(floor: int) -> int:
        count = ROGUELIKE.base_map_elements + floor * ROGUELIKE.map_elements_per_floor
        return min(count, ROGUELIKE.max_map_elements)


class MapGenerator:
    @staticmethod
    def generate(floor: int, snake: Snake) -> GameMap:
        game_map = GameMap()
        element_count = DifficultySystem.get_map_element_count(floor)
        
        occupied = {(seg.x, seg.y) for seg in snake.body}
        
        center_x = GRID.cols // 2
        center_y = GRID.rows // 2
        spawn_radius = 5
        
        safe_positions: list[tuple[int, int]] = []
        for x in range(GRID.cols):
            for y in range(GRID.rows):
                if (x, y) not in occupied:
                    dist_from_center = abs(x - center_x) + abs(y - center_y)
                    if dist_from_center > spawn_radius:
                        safe_positions.append((x, y))
        
        shuffle(safe_positions)
        
        tile_weights = [
            (MapTileType.WALL, MAP_PROB.wall),
            (MapTileType.SLOW_ZONE, MAP_PROB.slow_zone),
            (MapTileType.GRASS, MAP_PROB.grass),
            (MapTileType.WATER, MAP_PROB.water),
            (MapTileType.BRICK, MAP_PROB.brick),
        ]
        
        placed = 0
        pos_idx = 0
        
        while placed < element_count and pos_idx < len(safe_positions):
            x, y = safe_positions[pos_idx]
            pos_idx += 1
            
            tile_type = MapGenerator._weighted_choice(tile_weights)
            
            if MapGenerator._would_trap(x, y, tile_type, game_map, GRID.cols, GRID.rows):
                continue
            
            game_map.set_tile(Vec2(x, y), tile_type)
            placed += 1
        
        if random() < MAP_PROB.portal and pos_idx + 1 < len(safe_positions):
            px1, py1 = safe_positions[pos_idx]
            px2, py2 = safe_positions[pos_idx + 1]
            
            portal_a = Vec2(px1, py1)
            portal_b = Vec2(px2, py2)
            
            game_map.set_tile(portal_a, MapTileType.PORTAL_A)
            game_map.set_tile(portal_b, MapTileType.PORTAL_B)
            game_map.portal_a_pos = portal_a
            game_map.portal_b_pos = portal_b
        
        return game_map

    @staticmethod
    def _weighted_choice(weights: list[tuple[MapTileType, float]]) -> MapTileType:
        total = sum(w for _, w in weights)
        r = uniform(0, total)
        cumulative = 0.0
        for tile, weight in weights:
            cumulative += weight
            if r <= cumulative:
                return tile
        return weights[0][0]

    @staticmethod
    def _would_trap(x: int, y: int, tile_type: MapTileType, 
                     game_map: GameMap, cols: int, rows: int) -> bool:
        if tile_type not in (MapTileType.WALL, MapTileType.WATER, MapTileType.BRICK):
            return False
        
        directions = [(0, -1), (0, 1), (-1, 0), (1, 0)]
        exits = 0
        
        for dx, dy in directions:
            nx, ny = x + dx, y + dy
            if 0 <= nx < cols and 0 <= ny < rows:
                neighbor = game_map.get_tile(Vec2(nx, ny))
                if neighbor not in (MapTileType.WALL, MapTileType.WATER, MapTileType.BRICK):
                    exits += 1
        
        return exits < 2


class SpawnSystem:
    @staticmethod
    def spawn_food(snake: Snake, game_map: GameMap, stats: RunStats) -> Food:
        occupied = {(seg.x, seg.y) for seg in snake.body}
        
        if stats.upgrades.food_magnet and len(snake.body) > 0:
            return SpawnSystem._spawn_near_head(snake, game_map, stats, occupied)
        
        return SpawnSystem._spawn_random(snake, game_map, stats, occupied)

    @staticmethod
    def _spawn_random(snake: Snake, game_map: GameMap, stats: RunStats, 
                      occupied: set[tuple[int, int]]) -> Food:
        while True:
            pos = Vec2(randint(0, GRID.cols - 1), randint(0, GRID.rows - 1))
            if (pos.x, pos.y) not in occupied and not game_map.is_blocking(pos):
                break
        
        poison_prob = DifficultySystem.get_poison_probability(stats.floor)
        
        if stats.has_poison_rain():
            poison_prob = min(0.7, poison_prob * 2.5)
        
        kind = FoodType.POISON if random() < poison_prob else FoodType.NORMAL
        
        is_golden = False
        if stats.has_golden_apple_active() and kind == FoodType.NORMAL:
            is_golden = random() < 0.3
        
        return Food(pos=pos, kind=kind, ttl_ms=Food.random_ttl(kind), is_golden=is_golden)

    @staticmethod
    def _spawn_near_head(snake: Snake, game_map: GameMap, stats: RunStats,
                         occupied: set[tuple[int, int]]) -> Food:
        head = snake.head
        radius = 6
        
        candidates: list[Vec2] = []
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                x, y = head.x + dx, head.y + dy
                if 0 <= x < GRID.cols and 0 <= y < GRID.rows:
                    pos = Vec2(x, y)
                    if (x, y) not in occupied and not game_map.is_blocking(pos):
                        candidates.append(pos)
        
        if candidates and random() < 0.6:
            pos = choice(candidates)
        else:
            while True:
                pos = Vec2(randint(0, GRID.cols - 1), randint(0, GRID.rows - 1))
                if (pos.x, pos.y) not in occupied and not game_map.is_blocking(pos):
                    break
        
        poison_prob = DifficultySystem.get_poison_probability(stats.floor)
        
        if stats.has_poison_rain():
            poison_prob = min(0.7, poison_prob * 2.5)
        
        kind = FoodType.POISON if random() < poison_prob else FoodType.NORMAL
        
        is_golden = False
        if stats.has_golden_apple_active() and kind == FoodType.NORMAL:
            is_golden = random() < 0.3
        
        return Food(pos=pos, kind=kind, ttl_ms=Food.random_ttl(kind), is_golden=is_golden)


class UpgradeSystem:
    ALL_UPGRADES = [
        UpgradeType.BODY_PLUS_ONE,
        UpgradeType.INITIAL_LENGTH_BONUS,
        UpgradeType.EXTRA_SCORE_PER_APPLE,
        UpgradeType.POISON_HEALS_INSTEAD,
        UpgradeType.SPEED_BOOST_PERMANENT,
        UpgradeType.SLOW_ZONE_RESISTANCE,
        UpgradeType.EXTRA_LIFE,
        UpgradeType.VISION_BONUS,
        UpgradeType.FOOD_MAGNET,
        UpgradeType.PORTAL_MASTER,
        UpgradeType.IMMUNITY_FIRST_HIT,
        UpgradeType.SCORE_MULTIPLIER,
    ]

    @staticmethod
    def generate_choices(stats: RunStats) -> list[Upgrade]:
        available = [ut for ut in UpgradeSystem.ALL_UPGRADES]
        
        if stats.upgrades.poison_heals:
            available = [ut for ut in available if ut != UpgradeType.POISON_HEALS_INSTEAD]
        if stats.upgrades.vision_bonus:
            available = [ut for ut in available if ut != UpgradeType.VISION_BONUS]
        if stats.upgrades.food_magnet:
            available = [ut for ut in available if ut != UpgradeType.FOOD_MAGNET]
        if stats.upgrades.portal_master:
            available = [ut for ut in available if ut != UpgradeType.PORTAL_MASTER]
        if stats.upgrades.immunity_first_hit:
            available = [ut for ut in available if ut != UpgradeType.IMMUNITY_FIRST_HIT]
        
        shuffle(available)
        selected = available[:3]
        
        return [Upgrade.from_type(ut) for ut in selected]

    @staticmethod
    def apply_upgrade(upgrade: Upgrade, snake: Snake, stats: RunStats) -> None:
        stats.upgrades.apply_upgrade(upgrade.upgrade_type)
        
        if upgrade.upgrade_type == UpgradeType.BODY_PLUS_ONE:
            snake.grow(1)
        
        stats.add_log(f"获得强化: {upgrade.name}")


class EventSystem:
    EVENT_DEFINITIONS: dict[EventType, dict] = {
        EventType.NARROW_VISION: {
            "name": "视野变窄",
            "description": "视野范围缩小，只能看到蛇头周围区域",
            "duration_ms": 20000,
            "is_positive": False,
        },
        EventType.DOUBLE_FOOD: {
            "name": "食物双倍",
            "description": "食物刷新频率大幅提升",
            "duration_ms": 15000,
            "is_positive": True,
        },
        EventType.SPEED_RUSH: {
            "name": "加速冲刺",
            "description": "移动速度大幅提升",
            "duration_ms": 10000,
            "is_positive": True,
        },
        EventType.POISON_RAIN: {
            "name": "毒果雨",
            "description": "毒果出现概率大幅提升",
            "duration_ms": 12000,
            "is_positive": False,
        },
        EventType.GOLDEN_APPLE: {
            "name": "金苹果时刻",
            "description": "有几率出现金苹果，+5分+2身体",
            "duration_ms": 18000,
            "is_positive": True,
        },
        EventType.REVERSE_CONTROLS: {
            "name": "反向控制",
            "description": "方向键上下左右颠倒",
            "duration_ms": 8000,
            "is_positive": False,
        },
        EventType.HALF_SPEED: {
            "name": "时间减速",
            "description": "移动速度降低一半",
            "duration_ms": 12000,
            "is_positive": False,
        },
        EventType.INSTANT_GROWTH: {
            "name": "快速成长",
            "description": "立即+3身体长度",
            "duration_ms": 0,
            "is_positive": True,
            "instant": True,
        },
        EventType.SCORE_BONUS_WAVE: {
            "name": "分数浪潮",
            "description": "接下来的得分x2",
            "duration_ms": 20000,
            "is_positive": True,
        },
        EventType.INVISIBLE_WALLS: {
            "name": "隐形障碍",
            "description": "障碍物暂时不可见（但仍存在）",
            "duration_ms": 10000,
            "is_positive": False,
        },
        EventType.SNAKE_SHUFFLE: {
            "name": "身体洗牌",
            "description": "蛇身体长度随机变化±2",
            "duration_ms": 0,
            "is_positive": False,
            "instant": True,
        },
        EventType.FREEZE_TIME: {
            "name": "时间冻结",
            "description": "食物暂停消失倒计时",
            "duration_ms": 10000,
            "is_positive": True,
        },
    }

    @staticmethod
    def roll_next_event_time(current_ms: int) -> int:
        interval_min, interval_max = ROGUELIKE.event_interval_sec
        interval_sec = uniform(interval_min, interval_max)
        return current_ms + int(interval_sec * 1000)

    @staticmethod
    def generate_random_event(current_ms: int) -> ActiveEvent:
        event_type = choice(list(EventType))
        definition = EventSystem.EVENT_DEFINITIONS.get(event_type, {
            "name": "未知事件",
            "description": "???",
            "duration_ms": 10000,
            "is_positive": False,
        })
        
        return ActiveEvent(
            event_type=event_type,
            start_ms=current_ms,
            duration_ms=definition["duration_ms"],
            is_positive=definition["is_positive"],
            name=definition["name"],
            description=definition["description"],
        )

    @staticmethod
    def apply_instant_event(event: ActiveEvent, snake: Snake, stats: RunStats) -> None:
        definition = EventSystem.EVENT_DEFINITIONS.get(event.event_type, {})
        if not definition.get("instant", False):
            return
        
        if event.event_type == EventType.INSTANT_GROWTH:
            snake.grow(3)
            stats.add_log("事件: 快速成长 +3")
        
        elif event.event_type == EventType.SNAKE_SHUFFLE:
            delta = randint(-2, 2)
            if delta > 0:
                snake.grow(delta)
                stats.add_log(f"事件: 身体洗牌 +{delta}")
            elif delta < 0 and len(snake.body) > abs(delta) + 2:
                snake.body = snake.body[:delta]
                stats.add_log(f"事件: 身体洗牌 {delta}")
            else:
                stats.add_log("事件: 身体洗牌（无变化）")


class RuleSystem:
    @staticmethod
    def out_of_bounds(pos: Vec2) -> bool:
        return pos.x < 0 or pos.y < 0 or pos.x >= GRID.cols or pos.y >= GRID.rows

    @staticmethod
    def apply_food_effect(food: Food, snake: Snake, stats: RunStats) -> None:
        score_multiplier = stats.upgrades.score_multiplier
        
        if stats.has_score_bonus_wave():
            score_multiplier *= 2.0
        
        if food.kind is FoodType.NORMAL:
            base_score = 1 + stats.upgrades.extra_score_per_apple
            if food.is_golden:
                base_score = 5
                snake.grow(2)
                stats.add_log("吃到了金苹果 +5 +2身体")
            else:
                stats.add_log(f"吃到了苹果 +{base_score}")
            
            snake.grow(1)
            stats.score += int(base_score * score_multiplier)
            stats.apples_eaten += 1
            
            if stats.score % GAMEPLAY.speedup_every_score == 0:
                stats.active_boost_left_ms += int(GAMEPLAY.boost_duration_sec * 1000)
                stats.add_log("获得短时加速")
        else:
            if stats.upgrades.poison_heals:
                snake.grow(1)
                stats.add_log("毒果回血 +1")
            else:
                stats.poison_eaten += 1
                penalty = int(2 * score_multiplier)
                stats.score = max(0, stats.score - penalty)
                if len(snake.body) > 3:
                    snake.body = snake.body[:-1]
                stats.add_log(f"误食毒果 -{penalty}")

    @staticmethod
    def handle_collision(snake: Snake, stats: RunStats) -> bool:
        if stats.has_immunity_this_floor and stats.upgrades.immunity_first_hit:
            stats.has_immunity_this_floor = False
            stats.add_log("首击免疫触发！")
            return False
        
        if stats.upgrades.extra_lives > 0:
            stats.upgrades.extra_lives -= 1
            snake.body = snake.body[:min(3, len(snake.body))]
            stats.add_log(f"额外生命触发！剩余: {stats.upgrades.extra_lives}")
            return False
        
        return True

    @staticmethod
    def is_in_slow_zone(snake: Snake, game_map: GameMap, stats: RunStats) -> bool:
        if not game_map.is_slow_zone(snake.head):
            return False
        
        resistance = stats.upgrades.slow_zone_resistance
        if random() < resistance:
            return False
        return True


def build_default_snake() -> Snake:
    center_x = GRID.cols // 2
    center_y = GRID.rows // 2
    body = [Vec2(center_x - i, center_y) for i in range(GAMEPLAY.initial_snake_length)]
    return Snake(body=body, direction=RIGHT)


def build_snake_with_bonus(length_bonus: int) -> Snake:
    center_x = GRID.cols // 2
    center_y = GRID.rows // 2
    length = GAMEPLAY.initial_snake_length + length_bonus
    body = [Vec2(center_x - i, center_y) for i in range(length)]
    return Snake(body=body, direction=RIGHT)
