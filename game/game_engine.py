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
    """
    Check whether the line segment between two mouse positions
    intersects a circular fruit or bomb.
    """
    sx, sy = start
    ex, ey = end
    cx, cy = center

    dx = ex - sx
    dy = ey - sy

    # Handle the case where the mouse has not moved.
    if dx == 0 and dy == 0:
        distance_squared = (sx - cx) ** 2 + (sy - cy) ** 2
        return distance_squared <= radius ** 2

    # Find the closest point on the mouse movement segment
    # to the centre of the fruit.
    t = ((cx - sx) * dx + (cy - sy) * dy) / (
        dx * dx + dy * dy
    )

    # Restrict the closest point to the actual line segment.
    t = max(0.0, min(1.0, t))

    closest_x = sx + t * dx
    closest_y = sy + t * dy

    # Check whether the closest point lies inside the circle.
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
        self.game_over = False

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
        if event.type == pygame.MOUSEMOTION:
            self._handle_motion(event.pos)

    def _handle_motion(self, pos):
        """
        Detect slices along the entire mouse movement path,
        rather than checking only the current mouse position.
        """

        # Use the previous mouse position as the start of the swipe.
        # If there is no previous position, use the current position.
        previous_pos = self.trail[-1] if self.trail else pos

        for fruit in self.fruits:

            # Do not slice an object more than once.
            if fruit.sliced:
                continue

            # Check whether the mouse movement crosses the fruit.
            intersects = segment_intersects_circle(
                previous_pos,
                pos,
                (fruit.x, fruit.y),
                fruit.radius
            )

            if intersects:
                self._slice(fruit)

        # Store the mouse position for the next movement event.
        self.trail.append(pos)

        # Keep only the most recent mouse positions.
        if len(self.trail) > 15:
            self.trail.pop(0)

    def _slice(self, fruit):
        fruit.sliced = True

        if fruit.kind == "bomb":
            self.game_over = True
        else:
            self.score += 1

    def handle_input(self):
        # The game is mouse-driven, so no continuous keyboard
        # input needs to be processed here.
        pass

    def update(self):
        if self.game_over:
            return

        # Spawn fruits periodically.
        self._spawn_timer += 1

        if self._spawn_timer >= self.spawn_interval:
            self._spawn_timer = 0
            self.spawn_fruit()

        still_alive = []

        for fruit in self.fruits:
            fruit.update()

            # Remove sliced fruits and bombs.
            if fruit.sliced:
                continue

            # Reduce lives when a fruit leaves the screen.
            if fruit.off_screen(self.height):
                if fruit.kind == "fruit":
                    self.lives -= 1

                continue

            still_alive.append(fruit)

        self.fruits = still_alive

        # End the game when all lives are lost.
        if self.lives <= 0:
            self.game_over = True

    def render(self, screen):

        # Draw all fruits and bombs.
        for fruit in self.fruits:
            color = getattr(fruit, "color", WHITE)

            pygame.draw.circle(
                screen,
                color,
                (int(fruit.x), int(fruit.y)),
                fruit.radius
            )

        # Draw the mouse trail.
        if len(self.trail) >= 2:
            pygame.draw.lines(
                screen,
                WHITE,
                False,
                self.trail,
                3
            )

        # Display the score.
        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE
        )

        screen.blit(score_text, (10, 10))

        # Display remaining lives.
        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE
        )

        screen.blit(
            lives_text,
            (self.width - 130, 10)
        )

        # Keep the original terminal Game Over message.
        if (
            self.game_over
            and not getattr(self, "_game_over_logged", False)
        ):
            print("Game over! Final score:", self.score)
            self._game_over_logged = True