from __future__ import annotations

import pygame

from .config import GRID, SCREEN, THEME
from .events import FoodType, GameState
from .models import Food, RunStats, Snake


class UiRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("Consolas", 22)
        self.small = pygame.font.SysFont("Consolas", 16)
        self.big = pygame.font.SysFont("Consolas", 44, bold=True)

    def draw(self, state: GameState, snake: Snake, food: Food, stats: RunStats) -> None:
        self.screen.fill(THEME.background)
        self._draw_board()
        self._draw_food(food)
        self._draw_snake(snake)
        self._draw_side_panel(state, stats)
        self._draw_overlays(state)

    def _draw_board(self) -> None:
        board_w = GRID.cols * GRID.cell_size
        board_h = GRID.rows * GRID.cell_size
        rect = pygame.Rect(GRID.margin, GRID.margin, board_w, board_h)
        pygame.draw.rect(self.screen, THEME.board, rect, border_radius=8)

    def _draw_snake(self, snake: Snake) -> None:
        for idx, seg in enumerate(snake.body):
            x = GRID.margin + seg.x * GRID.cell_size + 1
            y = GRID.margin + seg.y * GRID.cell_size + 1
            color = THEME.snake_head if idx == 0 else THEME.snake_body
            pygame.draw.rect(
                self.screen,
                color,
                pygame.Rect(x, y, GRID.cell_size - 2, GRID.cell_size - 2),
                border_radius=4,
            )

    def _draw_food(self, food: Food) -> None:
        x = GRID.margin + food.pos.x * GRID.cell_size + GRID.cell_size // 2
        y = GRID.margin + food.pos.y * GRID.cell_size + GRID.cell_size // 2
        radius = GRID.cell_size // 2 - 4
        color = THEME.poison_food if food.kind is FoodType.POISON else THEME.normal_food
        pygame.draw.circle(self.screen, color, (x, y), radius)

    def _draw_side_panel(self, state: GameState, stats: RunStats) -> None:
        left = GRID.margin * 2 + GRID.cols * GRID.cell_size
        panel = pygame.Rect(left, GRID.margin, SCREEN.width - left - GRID.margin, SCREEN.height - 2 * GRID.margin)
        pygame.draw.rect(self.screen, THEME.panel, panel, border_radius=8)

        rows = [
            f"State: {state.name}",
            f"Score: {stats.score}",
            f"High: {stats.high_score}",
            f"Time: {stats.elapsed_ms // 1000}s",
            f"Apple: {stats.apples_eaten}",
            f"Poison: {stats.poison_eaten}",
            f"Boost: {stats.active_boost_left_ms // 1000}s",
        ]
        y = panel.top + 20
        for line in rows:
            self.screen.blit(self.font.render(line, True, THEME.text_main), (panel.left + 16, y))
            y += 32

        self.screen.blit(self.small.render("Logs:", True, THEME.text_muted), (panel.left + 16, y + 8))
        y += 35
        for log in reversed(stats.logs):
            self.screen.blit(self.small.render(f"- {log}", True, THEME.text_muted), (panel.left + 16, y))
            y += 24

    def _draw_overlays(self, state: GameState) -> None:
        if state is GameState.MENU:
            self._draw_center_text("Snake Lab", "Enter 开始, WASD/方向键控制")
        elif state is GameState.PAUSED:
            self._draw_center_text("Paused", "按 P 继续")
        elif state is GameState.GAME_OVER:
            self._draw_center_text("Game Over", "按 R 重新开始")

    def _draw_center_text(self, title: str, subtitle: str) -> None:
        title_surf = self.big.render(title, True, THEME.text_main)
        sub_surf = self.font.render(subtitle, True, THEME.text_muted)
        cx = GRID.margin + GRID.cols * GRID.cell_size // 2
        cy = GRID.margin + GRID.rows * GRID.cell_size // 2
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 30)))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + 16)))
