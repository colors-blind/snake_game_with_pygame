from __future__ import annotations

from dataclasses import dataclass, field
from random import randint, choice
from typing import Optional

from .events import FoodType, MapTileType, UpgradeType, EventType


@dataclass
class Vec2:
    x: int
    y: int

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Vec2):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self) -> int:
        return hash((self.x, self.y))


UP = Vec2(0, -1)
DOWN = Vec2(0, 1)
LEFT = Vec2(-1, 0)
RIGHT = Vec2(1, 0)


@dataclass
class Food:
    pos: Vec2
    kind: FoodType
    ttl_ms: int = 0
    is_golden: bool = False

    @staticmethod
    def random_ttl(kind: FoodType) -> int:
        if kind is FoodType.POISON:
            return randint(6000, 10000)
        return 0


@dataclass
class Snake:
    body: list[Vec2]
    direction: Vec2
    pending_growth: int = 0

    @property
    def head(self) -> Vec2:
        return self.body[0]

    def set_direction(self, next_dir: Vec2) -> None:
        if (self.direction.x + next_dir.x == 0) and (self.direction.y + next_dir.y == 0):
            return
        self.direction = next_dir

    def move(self) -> None:
        new_head = self.head + self.direction
        self.body.insert(0, new_head)
        if self.pending_growth > 0:
            self.pending_growth -= 1
        else:
            self.body.pop()

    def grow(self, amount: int = 1) -> None:
        self.pending_growth += max(0, amount)

    def collides_with_self(self) -> bool:
        head = self.head
        return any(seg.x == head.x and seg.y == head.y for seg in self.body[1:])


@dataclass
class MapTile:
    tile_type: MapTileType
    pos: Vec2


@dataclass
class Upgrade:
    upgrade_type: UpgradeType
    name: str
    description: str
    icon: str = "?"

    @staticmethod
    def from_type(upgrade_type: UpgradeType) -> "Upgrade":
        upgrade_defs = {
            UpgradeType.BODY_PLUS_ONE: {
                "name": "身体+1",
                "description": "立即增加1节身体长度",
                "icon": "🐍"
            },
            UpgradeType.INITIAL_LENGTH_BONUS: {
                "name": "初始长度+2",
                "description": "每新层开始时初始长度+2",
                "icon": "📏"
            },
            UpgradeType.EXTRA_SCORE_PER_APPLE: {
                "name": "苹果额外+1分",
                "description": "每个苹果额外多给1分",
                "icon": "🍎"
            },
            UpgradeType.POISON_HEALS_INSTEAD: {
                "name": "毒果改回血",
                "description": "毒果不再扣血，反而恢复1节身体",
                "icon": "💚"
            },
            UpgradeType.SPEED_BOOST_PERMANENT: {
                "name": "永久微加速",
                "description": "移动速度永久提升10%",
                "icon": "⚡"
            },
            UpgradeType.SLOW_ZONE_RESISTANCE: {
                "name": "减速区抵抗",
                "description": "减速区效果降低50%",
                "icon": "🛡️"
            },
            UpgradeType.EXTRA_LIFE: {
                "name": "额外生命",
                "description": "获得1次免死机会，碰撞后保留3节身体",
                "icon": "❤️"
            },
            UpgradeType.VISION_BONUS: {
                "name": "视野增强",
                "description": "永久扩大视野范围，抵消负面视野事件",
                "icon": "👁️"
            },
            UpgradeType.FOOD_MAGNET: {
                "name": "食物磁铁",
                "description": "食物更频繁在蛇头附近刷新",
                "icon": "🧲"
            },
            UpgradeType.PORTAL_MASTER: {
                "name": "传送门大师",
                "description": "使用传送门后获得2秒加速",
                "icon": "🌀"
            },
            UpgradeType.IMMUNITY_FIRST_HIT: {
                "name": "首击免疫",
                "description": "每层开始时免疫第一次碰撞",
                "icon": "✨"
            },
            UpgradeType.SCORE_MULTIPLIER: {
                "name": "分数倍率",
                "description": "所有得分 x1.5",
                "icon": "⭐"
            },
        }
        definition = upgrade_defs.get(upgrade_type, {
            "name": "未知强化",
            "description": "???",
            "icon": "?"
        })
        return Upgrade(
            upgrade_type=upgrade_type,
            name=definition["name"],
            description=definition["description"],
            icon=definition["icon"]
        )


@dataclass
class ActiveEvent:
    event_type: EventType
    start_ms: int
    duration_ms: int
    is_positive: bool
    name: str
    description: str

    def is_active(self, current_ms: int) -> bool:
        return current_ms < self.start_ms + self.duration_ms

    def remaining_ms(self, current_ms: int) -> int:
        return max(0, self.start_ms + self.duration_ms - current_ms)


@dataclass
class PlayerUpgrades:
    initial_length_bonus: int = 0
    extra_score_per_apple: int = 0
    poison_heals: bool = False
    permanent_speed_bonus: float = 1.0
    slow_zone_resistance: float = 1.0
    extra_lives: int = 0
    vision_bonus: bool = False
    food_magnet: bool = False
    portal_master: bool = False
    immunity_first_hit: bool = False
    score_multiplier: float = 1.0

    def apply_upgrade(self, upgrade_type: UpgradeType) -> None:
        if upgrade_type == UpgradeType.BODY_PLUS_ONE:
            pass
        elif upgrade_type == UpgradeType.INITIAL_LENGTH_BONUS:
            self.initial_length_bonus += 2
        elif upgrade_type == UpgradeType.EXTRA_SCORE_PER_APPLE:
            self.extra_score_per_apple += 1
        elif upgrade_type == UpgradeType.POISON_HEALS_INSTEAD:
            self.poison_heals = True
        elif upgrade_type == UpgradeType.SPEED_BOOST_PERMANENT:
            self.permanent_speed_bonus *= 0.9
        elif upgrade_type == UpgradeType.SLOW_ZONE_RESISTANCE:
            self.slow_zone_resistance *= 0.5
        elif upgrade_type == UpgradeType.EXTRA_LIFE:
            self.extra_lives += 1
        elif upgrade_type == UpgradeType.VISION_BONUS:
            self.vision_bonus = True
        elif upgrade_type == UpgradeType.FOOD_MAGNET:
            self.food_magnet = True
        elif upgrade_type == UpgradeType.PORTAL_MASTER:
            self.portal_master = True
        elif upgrade_type == UpgradeType.IMMUNITY_FIRST_HIT:
            self.immunity_first_hit = True
        elif upgrade_type == UpgradeType.SCORE_MULTIPLIER:
            self.score_multiplier *= 1.5


@dataclass
class RunStats:
    score: int = 0
    high_score: int = 0
    elapsed_ms: int = 0
    floor_elapsed_ms: int = 0
    apples_eaten: int = 0
    poison_eaten: int = 0
    active_boost_left_ms: int = 0
    logs: list[str] = field(default_factory=list)
    
    floor: int = 1
    next_event_ms: int = 0
    has_immunity_this_floor: bool = False
    used_lives_this_floor: int = 0
    active_events: list[ActiveEvent] = field(default_factory=list)
    upgrades: PlayerUpgrades = field(default_factory=PlayerUpgrades)
    
    pending_upgrade_choices: list[Upgrade] = field(default_factory=list)
    selected_upgrade_index: int = 0
    
    pending_event_notification: Optional[ActiveEvent] = None

    def add_log(self, text: str) -> None:
        self.logs.append(text)
        if len(self.logs) > 7:
            self.logs = self.logs[-7:]

    def get_effective_speed_multiplier(self) -> float:
        multiplier = self.upgrades.permanent_speed_bonus
        if self.active_boost_left_ms > 0:
            multiplier *= 0.8
        return multiplier

    def has_narrow_vision(self) -> bool:
        has_narrow = any(
            e.event_type == EventType.NARROW_VISION and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )
        if self.upgrades.vision_bonus:
            return False
        return has_narrow

    def has_double_food(self) -> bool:
        return any(
            e.event_type == EventType.DOUBLE_FOOD and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_golden_apple_active(self) -> bool:
        return any(
            e.event_type == EventType.GOLDEN_APPLE and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_reverse_controls(self) -> bool:
        return any(
            e.event_type == EventType.REVERSE_CONTROLS and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_half_speed(self) -> bool:
        return any(
            e.event_type == EventType.HALF_SPEED and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_speed_rush(self) -> bool:
        return any(
            e.event_type == EventType.SPEED_RUSH and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_poison_rain(self) -> bool:
        return any(
            e.event_type == EventType.POISON_RAIN and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_invisible_walls(self) -> bool:
        return any(
            e.event_type == EventType.INVISIBLE_WALLS and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_freeze_time(self) -> bool:
        return any(
            e.event_type == EventType.FREEZE_TIME and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def has_score_bonus_wave(self) -> bool:
        return any(
            e.event_type == EventType.SCORE_BONUS_WAVE and e.is_active(self.elapsed_ms)
            for e in self.active_events
        )

    def clean_inactive_events(self) -> None:
        self.active_events = [
            e for e in self.active_events if e.is_active(self.elapsed_ms)
        ]


@dataclass
class GameMap:
    tiles: dict[tuple[int, int], MapTileType] = field(default_factory=dict)
    portal_a_pos: Optional[Vec2] = None
    portal_b_pos: Optional[Vec2] = None

    def get_tile(self, pos: Vec2) -> MapTileType:
        return self.tiles.get((pos.x, pos.y), MapTileType.EMPTY)

    def set_tile(self, pos: Vec2, tile_type: MapTileType) -> None:
        if tile_type == MapTileType.EMPTY:
            self.tiles.pop((pos.x, pos.y), None)
        else:
            self.tiles[(pos.x, pos.y)] = tile_type

    def is_blocking(self, pos: Vec2) -> bool:
        tile = self.get_tile(pos)
        return tile in (MapTileType.WALL, MapTileType.WATER, MapTileType.BRICK)

    def is_slow_zone(self, pos: Vec2) -> bool:
        return self.get_tile(pos) == MapTileType.SLOW_ZONE

    def get_teleport_destination(self, pos: Vec2) -> Optional[Vec2]:
        tile = self.get_tile(pos)
        if tile == MapTileType.PORTAL_A and self.portal_b_pos:
            return self.portal_b_pos
        if tile == MapTileType.PORTAL_B and self.portal_a_pos:
            return self.portal_a_pos
        return None
