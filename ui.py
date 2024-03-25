import pygame

from pygame.math import Vector2
from settings import *

def draw_text(surface, font, text, color, x, y, options: str = 'center') -> None:
    assert options in ["center", "topleft"]
    text_surface = font.render(text, True, color)
    text_rect = text_surface.get_rect()
    if options == "topleft":
        text_rect.topleft = (x, y)
    else:
        text_rect.center = (x, y)
    
    surface.blit(text_surface, text_rect)


def draw_lives(surface, img, lives: int) -> None:
    x_offset:int = GAME_W - (img.get_size()[0] * 2 + 20)
    for life in range(lives-1):
        x = x_offset + (life * (img.get_size()[0] + 10))
        surface.blit(img, (x, 8))

class Cursor():
    """A Cursor UI.
    
    A cursor is ui element for which the x will not change and the y will take discrete position given its state and action"""
    def __init__(self, pos, k, y_range, color: tuple=(255, 255, 255), width: int=30, height: int=30) -> None:
        # Color
        self.color: tuple = color
        # Dimension
        self.width: int = width
        self.height: int = height
        # Position
        self.pos = pos
        self.rect = pygame.Rect(self.pos.x, self.pos.y, self.width, self.height)
        # Number of positions
        self.k: int = k
        self.y_min = y_range[0]
        self.y_max = y_range[1]
        # State
        self.index: int = 0
        self.index_pos: dict = {}
        # Create index pos
        self.create_y_pos()
        self.rect.centery = self.index_pos[self.index]
    
    def update(self, key) -> None:
        # Check the key
        if key == pygame.K_DOWN:
            self.index = (self.index + 1) % self.k
        elif key == pygame.K_UP:
            self.index = (self.index - 1) % self.k
        self.rect.centery = self.index_pos[self.index]
    
    def create_y_pos(self) -> None:
        if self.k % 2 == 1:
            for i in range(self.k):
                self.index_pos[i] = self.y_min + (i+1) * (self.y_max - self.y_min)/(self.k+2)
        elif self.k % 2 == 0:
            for i in range(self.k):
                self.index_pos[i] = self.y_min + (i+1) * (self.y_max - self.y_min)/(self.k+1)
    
    def get_index_pos(self) -> dict:
        return self.index_pos
    
    def render(self, surface) -> None:
        pygame.draw.rect(surface, self.color, self.rect)


class TextMenu():
    """A text menu with a cursor with several choices."""
    def __init__(self, menu_option: dict, y_range, x_range, font, color: tuple = (255, 255, 255)) -> None:

        self.color: tuple = color
        self.menu_options: dict = menu_option
        self.y_range = y_range
        self.x_range = x_range
        self.font = font
        self.cursor = Cursor(Vector2((x_range[1]-x_range[0])//4, 0.), len(self.menu_options), y_range, color=self.color)
        self.y_pos: dict = self.cursor.get_index_pos()

    def update(self, event) -> None:

        if event.type == pygame.KEYDOWN:
            self.cursor.update(event.key)
    
    def get_option(self):
        return self.menu_options[self.cursor.index]
    
    def render(self, surface) -> None:
        self.render_options(surface)
        self.cursor.render(surface)

    def render_options(self, surface) -> None:
        for index, val in zip(range(len(self.menu_options)), self.menu_options.values()):
            y = self.y_pos[index]
            draw_text(surface, self.font, str(val), self.color, (self.x_range[1] + self.x_range[0])//2, y)
        


if __name__ == "__main__":
    import sys
    pygame.init()
    SCREEN_W = 600
    SCREEN_H = 600
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    menu = TextMenu({0: "Start", 1: "Credits", 2: "Ranking", 3: "Test"}, [SCREEN_H//4, 3*SCREEN_H//4], [0, SCREEN_W], font)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            menu.update(event)
                
        screen.fill((30, 30, 30))
        menu.render(screen)
        pygame.display.flip()
        clock.tick(60)
