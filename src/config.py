from dataclasses import dataclass


@dataclass(frozen=True)
class ScreenConfig:
    width: int = 960
    height: int = 720
    title: str = "Snake Lab (Pygame)"
    fps: int = 60


@dataclass(frozen=True)
class GridConfig:
    cell_size: int = 24
    cols: int = 32
    rows: int = 24
    margin: int = 8


@dataclass(frozen=True)
class RoguelikeConfig:
    floor_duration_sec: int = 60
    event_interval_sec: tuple[int, int] = (20, 35)
    base_map_elements: int = 12
    map_elements_per_floor: int = 3
    max_map_elements: int = 45


@dataclass(frozen=True)
class MapTileProbability:
    wall: float = 0.25
    slow_zone: float = 0.20
    portal: float = 0.10
    grass: float = 0.25
    water: float = 0.10
    brick: float = 0.10


@dataclass(frozen=True)
class DifficultyCurveConfig:
    base_speed_ms: int = 160
    min_speed_ms: int = 50
    speed_decay_factor: float = 0.92
    poison_prob_base: float = 0.15
    poison_prob_max: float = 0.35
    poison_prob_growth: float = 0.03
    extra_food_base: int = 1
    extra_food_max: int = 0
    food_ttl_base_ms: int = 0
    food_ttl_min_ms: int = 8000


@dataclass(frozen=True)
class GameplayConfig:
    initial_snake_length: int = 4
    base_tick_ms: int = 140
    min_tick_ms: int = 65
    speedup_every_score: int = 3
    speedup_step_ms: int = 8
    poison_food_probability: float = 0.2
    boost_duration_sec: float = 4.0
    boost_tick_bonus_ms: int = 25
    slow_zone_tick_multiplier: float = 1.8


@dataclass(frozen=True)
class ColorTheme:
    background: tuple[int, int, int] = (21, 25, 34)
    board: tuple[int, int, int] = (33, 39, 52)
    snake_head: tuple[int, int, int] = (80, 230, 120)
    snake_body: tuple[int, int, int] = (63, 186, 98)
    ai_snake_head: tuple[int, int, int] = (255, 80, 80)
    ai_snake_body: tuple[int, int, int] = (220, 60, 60)
    normal_food: tuple[int, int, int] = (245, 108, 108)
    poison_food: tuple[int, int, int] = (171, 104, 247)
    text_main: tuple[int, int, int] = (230, 232, 240)
    text_muted: tuple[int, int, int] = (166, 171, 189)
    panel: tuple[int, int, int] = (24, 29, 39)
    
    wall: tuple[int, int, int] = (80, 80, 100)
    slow_zone: tuple[int, int, int] = (60, 100, 140)
    portal_a: tuple[int, int, int] = (255, 150, 50)
    portal_b: tuple[int, int, int] = (50, 150, 255)
    grass: tuple[int, int, int] = (40, 120, 60)
    water: tuple[int, int, int] = (30, 80, 160)
    brick: tuple[int, int, int] = (150, 80, 60)
    
    selection_highlight: tuple[int, int, int] = (100, 180, 255)
    event_positive: tuple[int, int, int] = (100, 220, 100)
    event_negative: tuple[int, int, int] = (220, 100, 100)
    fog: tuple[int, int, int] = (10, 10, 20)


SCREEN = ScreenConfig()
GRID = GridConfig()
GAMEPLAY = GameplayConfig()
THEME = ColorTheme()
ROGUELIKE = RoguelikeConfig()
MAP_PROB = MapTileProbability()
DIFFICULTY = DifficultyCurveConfig()
