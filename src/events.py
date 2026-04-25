from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    FLOOR_TRANSITION = auto()
    UPGRADE_SELECTION = auto()
    EVENT_NOTIFICATION = auto()


class FoodType(Enum):
    NORMAL = auto()
    POISON = auto()


class MapTileType(Enum):
    EMPTY = auto()
    WALL = auto()
    SLOW_ZONE = auto()
    PORTAL_A = auto()
    PORTAL_B = auto()
    GRASS = auto()
    WATER = auto()
    BRICK = auto()


class UpgradeType(Enum):
    BODY_PLUS_ONE = auto()
    INITIAL_LENGTH_BONUS = auto()
    EXTRA_SCORE_PER_APPLE = auto()
    POISON_HEALS_INSTEAD = auto()
    SPEED_BOOST_PERMANENT = auto()
    SLOW_ZONE_RESISTANCE = auto()
    EXTRA_LIFE = auto()
    VISION_BONUS = auto()
    FOOD_MAGNET = auto()
    PORTAL_MASTER = auto()
    IMMUNITY_FIRST_HIT = auto()
    SCORE_MULTIPLIER = auto()


class EventType(Enum):
    NARROW_VISION = auto()
    DOUBLE_FOOD = auto()
    SPEED_RUSH = auto()
    POISON_RAIN = auto()
    INVISIBLE_WALLS = auto()
    SNAKE_SHUFFLE = auto()
    GOLDEN_APPLE = auto()
    FREEZE_TIME = auto()
    REVERSE_CONTROLS = auto()
    HALF_SPEED = auto()
    INSTANT_GROWTH = auto()
    SCORE_BONUS_WAVE = auto()
