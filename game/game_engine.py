import pygame
import random
import math
from array import array
from .fruit import Fruit

WHITE = (255, 255, 255)
BOMB_BLACK = (30, 30, 30)

FRUIT_COLORS = [
    (220, 60, 60),
    (230, 140, 40),
    (230, 200, 40),
    (90, 180, 90),
]

DIFFICULTIES = {
    "Easy": {
        "spawn_interval": 70,
        "bomb_chance": 0.08,
        "speed_scale": 0.8,
    },
    "Medium": {
        "spawn_interval": 55,
        "bomb_chance": 0.15,
        "speed_scale": 1.0,
    },
    "Hard": {
        "spawn_interval": 35,
        "bomb_chance": 0.25,
        "speed_scale": 1.3,
    },
}


def segment_intersects_circle(start, end, center, radius):
    """Check whether a mouse movement segment crosses a fruit."""
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

    return (
        (closest_x - cx) ** 2 + (closest_y - cy) ** 2
        <= radius ** 2
    )


def create_tone(frequency, duration=0.15, volume=0.35):
    """Generate a simple sound without requiring external audio files."""
    sample_rate = 22050
    samples = int(sample_rate * duration)
    amplitude = int(32767 * volume)

    sound_data = array("h")

    for i in range(samples):
        time_value = i / sample_rate

        # Fade the sound out smoothly.
        fade = 1.0 - (i / samples)

        sample = int(
            amplitude
            * fade
            * math.sin(2 * math.pi * frequency * time_value)
        )

        sound_data.append(sample)

    return pygame.mixer.Sound(buffer=sound_data.tobytes())


class GameEngine:

    def __init__(self, width, height):
        self.width = width
        self.height = height

        self.font = pygame.font.SysFont("Arial", 28)
        self.title_font = pygame.font.SysFont("Arial", 46)
        self.message_font = pygame.font.SysFont("Arial", 24)
        self.small_font = pygame.font.SysFont("Arial", 20)

        # Sound effects
        self.sound_enabled = False
        self.slice_sound = None
        self.bomb_sound = None
        self.game_over_sound = None

        try:
            if pygame.mixer.get_init() is None:
                pygame.mixer.init(
                    frequency=22050,
                    size=-16,
                    channels=1,
                )

            self.slice_sound = create_tone(850, 0.10, 0.25)
            self.bomb_sound = create_tone(110, 0.35, 0.45)
            self.game_over_sound = create_tone(260, 0.45, 0.35)

            self.sound_enabled = True

        except pygame.error:
            print("Sound effects are unavailable. The game will continue silently.")

        self.selected_difficulty = "Medium"
        self.state = "menu"

        self.fruits = []
        self.trail = []

        self.score = 0
        self.lives = 3
        self.game_over_reason = None

        self.apply_difficulty()

    def play_sound(self, sound):
        """Play a sound safely if audio is available."""
        if self.sound_enabled and sound is not None:
            try:
                sound.play()
            except pygame.error:
                pass

    def apply_difficulty(self):
        settings = DIFFICULTIES[self.selected_difficulty]

        self.spawn_interval = settings["spawn_interval"]
        self.bomb_chance = settings["bomb_chance"]
        self.speed_scale = settings["speed_scale"]

    def start_game(self):
        self.fruits = []
        self.trail = []

        self.score = 0
        self.lives = 3
        self.game_over_reason = None
        self._spawn_timer = 0

        self.apply_difficulty()
        self.state = "playing"

    def end_game(self, reason):
        """Finish the game and play the Game Over sound once."""
        if self.state != "game_over":
            self.state = "game_over"
            self.game_over_reason = reason
            self.play_sound(self.game_over_sound)

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
            kind=kind,
        )

        fruit.color = (
            BOMB_BLACK
            if kind == "bomb"
            else random.choice(FRUIT_COLORS)
        )

        self.fruits.append(fruit)

    def handle_event(self, event):

        if event.type == pygame.KEYDOWN:

            if self.state == "menu":

                if event.key == pygame.K_1:
                    self.selected_difficulty = "Easy"

                elif event.key == pygame.K_2:
                    self.selected_difficulty = "Medium"

                elif event.key == pygame.K_3:
                    self.selected_difficulty = "Hard"

                elif event.key in (
                    pygame.K_RETURN,
                    pygame.K_SPACE,
                ):
                    self.start_game()

            elif self.state == "game_over":

                if event.key in (
                    pygame.K_r,
                    pygame.K_RETURN,
                ):
                    self.start_game()

                elif event.key == pygame.K_m:
                    self.state = "menu"

        if self.state == "playing":

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
                fruit.radius,
            )

            if intersects:
                self._slice(fruit)

                if self.state != "playing":
                    break

        self.trail.append(pos)

        if len(self.trail) > 15:
            self.trail.pop(0)

    def _slice(self, fruit):

        if fruit.sliced:
            return

        fruit.sliced = True

        if fruit.kind == "bomb":
            self.play_sound(self.bomb_sound)
            self.end_game("You sliced a bomb!")

        else:
            self.score += 1
            self.play_sound(self.slice_sound)

    def handle_input(self):
        pass

    def update(self):

        if self.state != "playing":
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
            self.end_game("You ran out of lives!")

    def render(self, screen):

        if self.state == "menu":
            self._render_menu(screen)
            return

        for fruit in self.fruits:

            color = getattr(fruit, "color", WHITE)

            pygame.draw.circle(
                screen,
                color,
                (int(fruit.x), int(fruit.y)),
                fruit.radius,
            )

        if self.state == "playing" and len(self.trail) >= 2:

            pygame.draw.lines(
                screen,
                WHITE,
                False,
                self.trail,
                3,
            )

        score_text = self.font.render(
            f"Score: {self.score}",
            True,
            WHITE,
        )

        screen.blit(score_text, (10, 10))

        lives_text = self.font.render(
            f"Lives: {self.lives}",
            True,
            WHITE,
        )

        screen.blit(
            lives_text,
            (self.width - 130, 10),
        )

        if self.state == "game_over":
            self._render_game_over(screen)

    def _render_menu(self, screen):

        title = self.title_font.render(
            "FRUIT SLICE",
            True,
            (255, 200, 70),
        )

        screen.blit(
            title,
            title.get_rect(
                center=(self.width // 2, 140)
            ),
        )

        subtitle = self.message_font.render(
            "Choose your difficulty",
            True,
            WHITE,
        )

        screen.blit(
            subtitle,
            subtitle.get_rect(
                center=(self.width // 2, 220)
            ),
        )

        options = [
            ("1", "Easy", (100, 220, 120)),
            ("2", "Medium", (100, 180, 255)),
            ("3", "Hard", (255, 100, 100)),
        ]

        for index, (key, name, color) in enumerate(options):

            y = 290 + index * 55
            label = f"{key}. {name}"

            if name == self.selected_difficulty:
                label += "  (Selected)"

            text = self.font.render(
                label,
                True,
                color,
            )

            screen.blit(
                text,
                text.get_rect(
                    center=(self.width // 2, y)
                ),
            )

        message = self.small_font.render(
            "Press ENTER or SPACE to start",
            True,
            WHITE,
        )

        screen.blit(
            message,
            message.get_rect(
                center=(self.width // 2, 490)
            ),
        )

    def _render_game_over(self, screen):

        overlay = pygame.Surface(
            (self.width, self.height),
            pygame.SRCALPHA,
        )

        overlay.fill((0, 0, 0, 190))
        screen.blit(overlay, (0, 0))

        title = self.title_font.render(
            "GAME OVER",
            True,
            (255, 90, 90),
        )

        screen.blit(
            title,
            title.get_rect(
                center=(
                    self.width // 2,
                    self.height // 2 - 100,
                )
            ),
        )

        reason = self.message_font.render(
            self.game_over_reason or "The game has ended.",
            True,
            WHITE,
        )

        screen.blit(
            reason,
            reason.get_rect(
                center=(
                    self.width // 2,
                    self.height // 2 - 45,
                )
            ),
        )

        final_score = self.font.render(
            f"Final Score: {self.score}",
            True,
            WHITE,
        )

        screen.blit(
            final_score,
            final_score.get_rect(
                center=(
                    self.width // 2,
                    self.height // 2,
                )
            ),
        )

        replay = self.message_font.render(
            "Press R or ENTER to Play Again",
            True,
            (100, 255, 150),
        )

        screen.blit(
            replay,
            replay.get_rect(
                center=(
                    self.width // 2,
                    self.height // 2 + 55,
                )
            ),
        )

        menu = self.message_font.render(
            "Press M for Difficulty Menu",
            True,
            (180, 200, 255),
        )

        screen.blit(
            menu,
            menu.get_rect(
                center=(
                    self.width // 2,
                    self.height // 2 + 95,
                )
            ),
        )