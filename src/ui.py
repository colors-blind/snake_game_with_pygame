from __future__ import annotations

import pygame

from .config import GRID, SCREEN, THEME, ROGUELIKE
from .events import FoodType, GameState, MapTileType, EventType
from .models import Food, RunStats, Snake, GameMap, ActiveEvent, Upgrade


class UiRenderer:
    def __init__(self, screen: pygame.Surface) -> None:
        self.screen = screen
        self.font = pygame.font.SysFont("Consolas", 22)
        self.small = pygame.font.SysFont("Consolas", 16)
        self.big = pygame.font.SysFont("Consolas", 44, bold=True)
        self.medium = pygame.font.SysFont("Consolas", 28, bold=True)
        self.icon_font = pygame.font.SysFont("Segoe UI Emoji", 32)

    def draw(
        self, 
        state: GameState, 
        snake: Snake, 
        foods: list[Food], 
        stats: RunStats,
        game_map: GameMap
    ) -> None:
        self.screen.fill(THEME.background)
        self._draw_board()
        self._draw_map(game_map, snake, stats)
        self._draw_foods(foods)
        self._draw_snake(snake, stats)
        
        if stats.has_narrow_vision():
            self._draw_fog(snake)
        
        self._draw_side_panel(state, stats)
        self._draw_overlays(state, stats)

    def _draw_board(self) -> None:
        board_w = GRID.cols * GRID.cell_size
        board_h = GRID.rows * GRID.cell_size
        rect = pygame.Rect(GRID.margin, GRID.margin, board_w, board_h)
        pygame.draw.rect(self.screen, THEME.board, rect, border_radius=8)

    def _draw_map(self, game_map: GameMap, snake: Snake, stats: RunStats) -> None:        
        for (x, y), tile_type in game_map.tiles.items():
            if stats.has_invisible_walls() and tile_type in (MapTileType.WALL, MapTileType.WATER, MapTileType.BRICK):
                continue
            
            color = self._get_tile_color(tile_type)
            if color is None:
                continue
            
            px = GRID.margin + x * GRID.cell_size
            py = GRID.margin + y * GRID.cell_size
            
            if tile_type in (MapTileType.WALL, MapTileType.BRICK):
                pygame.draw.rect(self.screen, color, pygame.Rect(px, py, GRID.cell_size, GRID.cell_size))
                self._draw_tile_pattern(tile_type, px, py)
            elif tile_type == MapTileType.WATER:
                pygame.draw.rect(self.screen, color, pygame.Rect(px, py, GRID.cell_size, GRID.cell_size))
            elif tile_type == MapTileType.SLOW_ZONE:
                pygame.draw.rect(self.screen, color, pygame.Rect(px + 2, py + 2, GRID.cell_size - 4, GRID.cell_size - 4), border_radius=4)
            elif tile_type == MapTileType.GRASS:
                pygame.draw.rect(self.screen, color, pygame.Rect(px, py, GRID.cell_size, GRID.cell_size))
                self._draw_grass_pattern(px, py)
            elif tile_type in (MapTileType.PORTAL_A, MapTileType.PORTAL_B):
                center_x = px + GRID.cell_size // 2
                center_y = py + GRID.cell_size // 2
                radius = GRID.cell_size // 2 - 2
                pygame.draw.circle(self.screen, color, (center_x, center_y), radius)
                pygame.draw.circle(self.screen, THEME.board, (center_x, center_y), radius - 4)

    def _get_tile_color(self, tile_type: MapTileType) -> tuple[int, int, int] | None:
        color_map = {
            MapTileType.WALL: THEME.wall,
            MapTileType.SLOW_ZONE: THEME.slow_zone,
            MapTileType.PORTAL_A: THEME.portal_a,
            MapTileType.PORTAL_B: THEME.portal_b,
            MapTileType.GRASS: THEME.grass,
            MapTileType.WATER: THEME.water,
            MapTileType.BRICK: THEME.brick,
        }
        return color_map.get(tile_type)

    def _draw_tile_pattern(self, tile_type: MapTileType, px: int, py: int) -> None:
        if tile_type == MapTileType.BRICK:
            mid_y = py + GRID.cell_size // 2
            pygame.draw.line(self.screen, (100, 50, 40), (px, mid_y), (px + GRID.cell_size, mid_y), 2)
            mid_x = px + GRID.cell_size // 2
            pygame.draw.line(self.screen, (100, 50, 40), (mid_x, py), (mid_x, mid_y), 2)
            q1 = px + GRID.cell_size // 4
            q3 = px + GRID.cell_size * 3 // 4
            pygame.draw.line(self.screen, (100, 50, 40), (q1, mid_y), (q1, py + GRID.cell_size), 2)
            pygame.draw.line(self.screen, (100, 50, 40), (q3, mid_y), (q3, py + GRID.cell_size), 2)

    def _draw_grass_pattern(self, px: int, py: int) -> None:
        grass_color = (50, 150, 70)
        points = [
            (px + 4, py + GRID.cell_size),
            (px + 6, py + GRID.cell_size - 8),
            (px + 8, py + GRID.cell_size),
        ]
        pygame.draw.polygon(self.screen, grass_color, points)
        points2 = [
            (px + 12, py + GRID.cell_size),
            (px + 16, py + GRID.cell_size - 10),
            (px + 20, py + GRID.cell_size),
        ]
        pygame.draw.polygon(self.screen, grass_color, points2)

    def _draw_snake(self, snake: Snake, stats: RunStats) -> None:
        for idx, seg in enumerate(snake.body):
            x = GRID.margin + seg.x * GRID.cell_size + 1
            y = GRID.margin + seg.y * GRID.cell_size + 1
            color = THEME.snake_head if idx == 0 else THEME.snake_body
            
            if stats.has_immunity_this_floor and stats.upgrades.immunity_first_hit:
                if idx == 0:
                    pygame.draw.rect(
                        self.screen,
                        THEME.selection_highlight,
                        pygame.Rect(x - 2, y - 2, GRID.cell_size, GRID.cell_size),
                        border_radius=4,
                        width=2
                    )
            
            pygame.draw.rect(
                self.screen,
                color,
                pygame.Rect(x, y, GRID.cell_size - 2, GRID.cell_size - 2),
                border_radius=4,
            )

    def _draw_foods(self, foods: list[Food]) -> None:
        for food in foods:
            x = GRID.margin + food.pos.x * GRID.cell_size + GRID.cell_size // 2
            y = GRID.margin + food.pos.y * GRID.cell_size + GRID.cell_size // 2
            radius = GRID.cell_size // 2 - 4
            
            if food.is_golden:
                color = (255, 215, 0)
                pygame.draw.circle(self.screen, color, (x, y), radius + 2)
                pygame.draw.circle(self.screen, (255, 255, 200), (x, y), radius - 2)
            else:
                color = THEME.poison_food if food.kind is FoodType.POISON else THEME.normal_food
                pygame.draw.circle(self.screen, color, (x, y), radius)
            
            if food.kind == FoodType.POISON and food.ttl_ms > 0:
                ttl_ratio = food.ttl_ms / 10000
                bar_width = int(GRID.cell_size * ttl_ratio)
                bar_rect = pygame.Rect(
                    GRID.margin + food.pos.x * GRID.cell_size,
                    GRID.margin + food.pos.y * GRID.cell_size - 4,
                    bar_width,
                    3
                )
                pygame.draw.rect(self.screen, (200, 100, 100), bar_rect)

    def _draw_fog(self, snake: Snake) -> None:
        if not snake.body:
            return
        
        head_x = GRID.margin + snake.head.x * GRID.cell_size + GRID.cell_size // 2
        head_y = GRID.margin + snake.head.y * GRID.cell_size + GRID.cell_size // 2
        visible_radius = GRID.cell_size * 6
        
        board_w = GRID.cols * GRID.cell_size
        board_h = GRID.rows * GRID.cell_size
        board_rect = pygame.Rect(GRID.margin, GRID.margin, board_w, board_h)
        
        fog_surface = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        
        pygame.draw.rect(fog_surface, (*THEME.fog, 230), fog_surface.get_rect())
        
        hole_surface = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        pygame.draw.circle(hole_surface, (0, 0, 0, 0), (head_x, head_y), visible_radius)
        pygame.draw.circle(hole_surface, (*THEME.fog, 100), (head_x, head_y), visible_radius + 20, width=20)
        
        fog_surface.blit(hole_surface, (0, 0), special_flags=pygame.BLEND_RGBA_MIN)
        
        self.screen.blit(fog_surface, (0, 0))

    def _draw_side_panel(self, state: GameState, stats: RunStats) -> None:
        left = GRID.margin * 2 + GRID.cols * GRID.cell_size
        panel = pygame.Rect(left, GRID.margin, SCREEN.width - left - GRID.margin, SCREEN.height - 2 * GRID.margin)
        pygame.draw.rect(self.screen, THEME.panel, panel, border_radius=8)

        floor_remaining = max(0, ROGUELIKE.floor_duration_sec * 1000 - stats.floor_elapsed_ms) // 1000
        
        rows = [
            f"State: {state.name}",
            f"Floor: {stats.floor}",
            f"Floor Time: {floor_remaining}s",
            f"Score: {stats.score}",
            f"High: {stats.high_score}",
            f"Time: {stats.elapsed_ms // 1000}s",
            f"Apple: {stats.apples_eaten}",
            f"Poison: {stats.poison_eaten}",
        ]
        
        if stats.upgrades.extra_lives > 0:
            rows.append(f"Lives: {'❤️' * stats.upgrades.extra_lives}")
        
        y = panel.top + 20
        for line in rows:
            self.screen.blit(self.font.render(line, True, THEME.text_main), (panel.left + 16, y))
            y += 28

        if stats.active_events:
            y += 8
            self.screen.blit(self.small.render("Active Events:", True, THEME.text_muted), (panel.left + 16, y))
            y += 20
            
            for event in stats.active_events:
                remaining = event.remaining_ms(stats.elapsed_ms) // 1000
                color = THEME.event_positive if event.is_positive else THEME.event_negative
                event_text = f"  {event.name}: {remaining}s"
                self.screen.blit(self.small.render(event_text, True, color), (panel.left + 16, y))
                y += 18

        if stats.upgrades.initial_length_bonus > 0 or stats.upgrades.extra_score_per_apple > 0:
            y += 8
            self.screen.blit(self.small.render("Upgrades:", True, THEME.text_muted), (panel.left + 16, y))
            y += 20
            
            if stats.upgrades.initial_length_bonus > 0:
                self.screen.blit(self.small.render(f"  Init +{stats.upgrades.initial_length_bonus}", True, THEME.text_muted), (panel.left + 16, y))
                y += 18
            if stats.upgrades.extra_score_per_apple > 0:
                self.screen.blit(self.small.render(f"  +{stats.upgrades.extra_score_per_apple} per apple", True, THEME.text_muted), (panel.left + 16, y))
                y += 18
            if stats.upgrades.poison_heals:
                self.screen.blit(self.small.render(f"  Poison heals", True, THEME.text_muted), (panel.left + 16, y))
                y += 18
            if stats.upgrades.vision_bonus:
                self.screen.blit(self.small.render(f"  Vision bonus", True, THEME.text_muted), (panel.left + 16, y))
                y += 18
            if stats.upgrades.score_multiplier > 1.0:
                self.screen.blit(self.small.render(f"  Score x{stats.upgrades.score_multiplier:.1f}", True, THEME.text_muted), (panel.left + 16, y))
                y += 18

        self.screen.blit(self.small.render("Logs:", True, THEME.text_muted), (panel.left + 16, y + 8))
        y += 35
        for log in reversed(stats.logs):
            self.screen.blit(self.small.render(f"- {log}", True, THEME.text_muted), (panel.left + 16, y))
            y += 24

    def _draw_overlays(self, state: GameState, stats: RunStats) -> None:
        if state is GameState.MENU:
            self._draw_center_text("Snake Roguelike", "Enter 开始, WASD/方向键控制")
        elif state is GameState.PAUSED:
            self._draw_center_text("Paused", "按 P 继续")
        elif state is GameState.GAME_OVER:
            self._draw_game_over(stats)
        elif state is GameState.UPGRADE_SELECTION:
            self._draw_upgrade_selection(stats)
        elif state is GameState.EVENT_NOTIFICATION:
            self._draw_event_notification(stats)

    def _draw_center_text(self, title: str, subtitle: str) -> None:
        title_surf = self.big.render(title, True, THEME.text_main)
        sub_surf = self.font.render(subtitle, True, THEME.text_muted)
        cx = GRID.margin + GRID.cols * GRID.cell_size // 2
        cy = GRID.margin + GRID.rows * GRID.cell_size // 2
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, cy - 30)))
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(cx, cy + 16)))

    def _draw_game_over(self, stats: RunStats) -> None:
        overlay = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 180), overlay.get_rect())
        self.screen.blit(overlay, (0, 0))
        
        cx = GRID.margin + GRID.cols * GRID.cell_size // 2
        
        title_surf = self.big.render("Game Over", True, THEME.event_negative)
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 200)))
        
        lines = [
            f"Final Floor: {stats.floor}",
            f"Final Score: {stats.score}",
            f"Apples: {stats.apples_eaten}",
        ]
        
        y = 280
        for line in lines:
            surf = self.medium.render(line, True, THEME.text_main)
            self.screen.blit(surf, surf.get_rect(center=(cx, y)))
            y += 40
        
        restart_surf = self.font.render("按 R 返回菜单", True, THEME.text_muted)
        self.screen.blit(restart_surf, restart_surf.get_rect(center=(cx, y + 30)))

    def _draw_upgrade_selection(self, stats: RunStats) -> None:
        overlay = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 200), overlay.get_rect())
        self.screen.blit(overlay, (0, 0))
        
        cx = GRID.margin + GRID.cols * GRID.cell_size // 2
        
        title_surf = self.big.render(f"Floor {stats.floor} Complete!", True, THEME.selection_highlight)
        self.screen.blit(title_surf, title_surf.get_rect(center=(cx, 100)))
        
        subtitle_surf = self.font.render("选择一项强化 (← → 选择, Enter 确认)", True, THEME.text_muted)
        self.screen.blit(subtitle_surf, subtitle_surf.get_rect(center=(cx, 150)))
        
        if not stats.pending_upgrade_choices:
            return
        
        card_width = 200
        card_height = 220
        spacing = 30
        total_width = 3 * card_width + 2 * spacing
        start_x = cx - total_width // 2
        start_y = 200
        
        for i, upgrade in enumerate(stats.pending_upgrade_choices):
            is_selected = i == stats.selected_upgrade_index
            card_x = start_x + i * (card_width + spacing)
            card_rect = pygame.Rect(card_x, start_y, card_width, card_height)
            
            border_color = THEME.selection_highlight if is_selected else THEME.text_muted
            border_width = 4 if is_selected else 2
            pygame.draw.rect(self.screen, THEME.panel, card_rect, border_radius=12)
            pygame.draw.rect(self.screen, border_color, card_rect, border_radius=12, width=border_width)
            
            icon_surf = self.icon_font.render(upgrade.icon, True, THEME.text_main)
            icon_rect = icon_surf.get_rect(center=(card_x + card_width // 2, start_y + 40))
            self.screen.blit(icon_surf, icon_rect)
            
            name_surf = self.medium.render(upgrade.name, True, THEME.text_main)
            name_rect = name_surf.get_rect(center=(card_x + card_width // 2, start_y + 90))
            self.screen.blit(name_surf, name_rect)
            
            desc_lines = self._wrap_text(upgrade.description, card_width - 20, self.small)
            desc_y = start_y + 130
            for line in desc_lines:
                line_surf = self.small.render(line, True, THEME.text_muted)
                line_rect = line_surf.get_rect(center=(card_x + card_width // 2, desc_y))
                self.screen.blit(line_surf, line_rect)
                desc_y += 22

    def _draw_event_notification(self, stats: RunStats) -> None:
        event = stats.pending_event_notification
        if not event:
            return
        
        overlay = pygame.Surface((SCREEN.width, SCREEN.height), pygame.SRCALPHA)
        pygame.draw.rect(overlay, (0, 0, 0, 150), overlay.get_rect())
        self.screen.blit(overlay, (0, 0))
        
        cx = GRID.margin + GRID.cols * GRID.cell_size // 2
        cy = GRID.margin + GRID.rows * GRID.cell_size // 2
        
        box_rect = pygame.Rect(cx - 200, cy - 100, 400, 200)
        pygame.draw.rect(self.screen, THEME.panel, box_rect, border_radius=16)
        
        border_color = THEME.event_positive if event.is_positive else THEME.event_negative
        pygame.draw.rect(self.screen, border_color, box_rect, border_radius=16, width=3)
        
        event_type_text = "正面事件" if event.is_positive else "负面事件"
        type_surf = self.font.render(event_type_text, True, border_color)
        self.screen.blit(type_surf, type_surf.get_rect(center=(cx, cy - 70)))
        
        name_surf = self.big.render(event.name, True, THEME.text_main)
        self.screen.blit(name_surf, name_surf.get_rect(center=(cx, cy - 20)))
        
        desc_lines = self._wrap_text(event.description, 360, self.font)
        desc_y = cy + 20
        for line in desc_lines:
            line_surf = self.font.render(line, True, THEME.text_muted)
            self.screen.blit(line_surf, line_surf.get_rect(center=(cx, desc_y)))
            desc_y += 28
        
        if event.duration_ms > 0:
            duration_text = f"持续: {event.duration_ms // 1000}秒"
            dur_surf = self.small.render(duration_text, True, THEME.text_muted)
            self.screen.blit(dur_surf, dur_surf.get_rect(center=(cx, desc_y + 10)))
            desc_y += 30
        
        continue_surf = self.small.render("按 Enter 或 Space 继续", True, THEME.text_muted)
        self.screen.blit(continue_surf, continue_surf.get_rect(center=(cx, cy + 75)))

    def _wrap_text(self, text: str, max_width: int, font: pygame.font.Font) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current_line = ""
        
        for word in words:
            test_line = current_line + (" " if current_line else "") + word
            if font.size(test_line)[0] <= max_width:
                current_line = test_line
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines
