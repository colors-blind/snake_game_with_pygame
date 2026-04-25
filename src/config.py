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
class GameplayConfig:
    initial_snake_length: int = 4
    base_tick_ms: int = 140
    min_tick_ms: int = 65
    speedup_every_score: int = 3
    speedup_step_ms: int = 8
    poison_food_probability: float = 0.2
    boost_duration_sec: float = 4.0
    boost_tick_bonus_ms: int = 25


@dataclass(frozen=True)
class ColorTheme:
    background: tuple[int, int, int] = (21, 25, 34)
    board: tuple[int, int, int] = (33, 39, 52)
    snake_head: tuple[int, int, int] = (80, 230, 120)
    snake_body: tuple[int, int, int] = (63, 186, 98)
    normal_food: tuple[int, int, int] = (245, 108, 108)
    poison_food: tuple[int, int, int] = (171, 104, 247)
    text_main: tuple[int, int, int] = (230, 232, 240)
    text_muted: tuple[int, int, int] = (166, 171, 189)
    panel: tuple[int, int, int] = (24, 29, 39)


SCREEN = ScreenConfig()
GRID = GridConfig()
GAMEPLAY = GameplayConfig()
THEME = ColorTheme()
