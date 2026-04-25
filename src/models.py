from __future__ import annotations

from dataclasses import dataclass, field
from random import randint

from .events import FoodType


@dataclass
class Vec2:
    x: int
    y: int

    def __add__(self, other: "Vec2") -> "Vec2":
        return Vec2(self.x + other.x, self.y + other.y)

    def copy(self) -> "Vec2":
        return Vec2(self.x, self.y)


UP = Vec2(0, -1)
DOWN = Vec2(0, 1)
LEFT = Vec2(-1, 0)
RIGHT = Vec2(1, 0)


@dataclass
class Food:
    pos: Vec2
    kind: FoodType
    ttl_ms: int = 0

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
class RunStats:
    score: int = 0
    high_score: int = 0
    elapsed_ms: int = 0
    apples_eaten: int = 0
    poison_eaten: int = 0
    active_boost_left_ms: int = 0
    logs: list[str] = field(default_factory=list)

    def add_log(self, text: str) -> None:
        self.logs.append(text)
        if len(self.logs) > 7:
            self.logs = self.logs[-7:]
