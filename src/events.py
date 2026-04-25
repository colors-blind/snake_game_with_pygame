from enum import Enum, auto


class GameState(Enum):
    MENU = auto()
    RUNNING = auto()
    PAUSED = auto()
    GAME_OVER = auto()


class FoodType(Enum):
    NORMAL = auto()
    POISON = auto()
