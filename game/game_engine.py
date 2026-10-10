import pygame
import random
from .fruit import Fruit

# Game Engine

WHITE = (255, 255, 255)
BOMB_BLACK = (30, 30, 30)
FRUIT_COLORS = [
    (220, 60, 60),
    (230, 140, 40),
    (230, 200, 40),
    (90, 180, 90),
]


def segment_intersects_circle(start, end, center, radius):
    """Check whether a mouse movement segment intersects a circle."""
    sx, sy = start
    ex, ey = end
    cx, cy = center

    dx = ex - sx
    dy = ey - sy

    if dx == 0 and dy == 0:
        return (sx - cx) ** 2 + (sy - cy) ** 2 <= radius ** 2

    t = ((cx - sx) * dx + (cy - sy) * dy) / (
        dx * dx + dy * dy
    )

    t = max(0.0, min(1.0, t))

    closest_x = sx + t * dx
    closest_y = sy + t * dy

    distance_squared = (
        (closest_x - cx) ** 2
        + (closest_y - cy) ** 2
    )

    return distance_squared <= radius ** 2


class GameEngine:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.fruits = []
        self.trail = []

        self.spawn_interval = 55
        self._spawn_timer = 0
        self.bomb_chance = 0.15
        self.speed_scale = 1.0

        self.lives = 3
        self.score = 0

        self.font = pygame.font.SysFont("Arial", 28)
        self.game_over_font = pygame.font.SysFont("Arial", 48)
        self.message_font = pygame.font.SysFont("Arial", 24)

        self.game_over = False
        self.game_over_reason = None

    def spawn_fruit(self):
        x = random.randint(60, self.width - 60)

        vy = -random.uniform(13, 16) * self.speed_scale
        vx = random.uniform(-2, 2)
        gravity = 0.35

        kind = (
            "bomb"
            if random.random() < self.bomb_chance
            else "fruit"
        )

        fruit = Fruit(
            x,
            self.height + 30,
            vx,
            vy,
            gravity,
            kind=kind
        )

        fruit.color = (
            BOMB_BLACK
            if kind == "bomb"
            else random.choice(FRUIT_COLORS)
        )

        self.fruits.append(fruit)

    def handle_event(self, event):
        if self.game_over:
            return

        if event.type == pygame.MOUSEMOTION:
            self._handle_motion(event.pos)

    def _handle_motion(self, pos):
        previous_pos = self.trail[-1] if self.trail else pos

        for fruit in self.fruits:
            if fruit.sliced:
                continue

            intersects = segment_intersects_circle(
                previous_pos,
                pos,
                (fruit.x, fruit.y),
                fruit.radius
            )

            if intersects:
                self._slice(fruit)

                if self.game_over:
                    break

        self.trail.append(pos)

        if len(self.trail) > 15:
            self.trail.pop(0)

    def _slice(self, fruit):
        if fruit.sliced:
            return

        fruit.sliced = True

        if fruit.kind == "bomb":
            self.game_over = True
            self.game_over_reason = "You sliced a bomb!"
        else:
            self.score += 1

    def handle_input(self):
        # No continuous keyboard input is needed for Task 2.
        pass

    def update(self):
        if self.game_over:
            return

        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.spawn_fruit()

        still_alive = []

        for fruit in self.fruits:
            fruit.update()

            if fruit.sliced:
                continue

            if fruit.off_screen(self.height):
                if fruit.kind == "fruit":
                    self.lives -= 1

                continue

            still_alive.append(fruit)

        self.fruits = still_alive

        if self.lives <= 0:
            self.lives = 0
            self.game_over = True
            self.game_over_reason = "You ran out of lives!"

    def render(self, screen):
        for fruit in self.fruits:
            color = getattr(fruit, "color", WHITE)

            pygame.draw.circle(
                screen,
                color,
                (int(fruit.x), int(fruit.y)),
                fruit.radius
            )

        if not self.game_over and len(self.trail) >= 2:
            pygame.draw.lines(
                screen,
                WHITE,
                False,
                self.trail,
                3
            )

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )
        screen.blit(score_text, (10, 10))

        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE
        )
        screen.blit(
            lives_text,
            (self.width - 130, 10)
        )

        if self.game_over:
            self._render_game_over(screen)

    def _render_game_over(self, screen):
        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA
        )
        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        title = self.game_over_font.render(
            "GAME OVER",
            True,
            (255, 90, 90)
        )
        screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, self.height // 2 - 90)
            )
        )

        reason = self.message_font.render(
            self.game_over_reason or "The game has ended.",
            True,
            WHITE
        )
        screen.blit(
            reason,
            reason.get_rect(
                center=(self.width // 2, self.height // 2 - 35)
            )
        )

        final_score = self.font.render(
            f"Final Score: {self.score}",
            True,
            WHITE
        )
        screen.blit(
            final_score,
            final_score.get_rect(
                center=(self.width // 2, self.height // 2 + 15)
            )
        )

        exit_message = self.message_font.render(
            "Close the window to exit",
            True,
            (200, 200, 200)
        )
        screen.blit(
            exit_message,
            exit_message.get_rect(
                center=(self.width // 2, self.height // 2 + 70)
            )
        )