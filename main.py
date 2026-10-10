import pygame
from game.game_engine import GameEngine

pygame.init()

WIDTH, HEIGHT = 700, 600
SCREEN = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Fruit Slice - Pygame Version")

DARK_BLUE = (20, 25, 45)

clock = pygame.time.Clock()
FPS = 60

def main():
    engine = GameEngine(WIDTH, HEIGHT)
    running = True

    while running:
        SCREEN.fill(DARK_BLUE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                engine.handle_event(event)

        engine.handle_input()
        engine.update()
        engine.render(SCREEN)

        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()


if __name__ == "__main__":
    main()