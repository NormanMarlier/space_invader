import pygame

from random import choice
from settings import * #SPACECRAFT_SPEED, LASER_SPEED, LASER_COOLDOWN, ALIEN_SPEED

class Laser(pygame.sprite.Sprite):
    """Laser sprite.
    
    State x_t = (x, y)"""
    def __init__(self, pos, velocity: int, sound: pygame.mixer.Sound) -> None:
        super().__init__()
        self.image = pygame.Surface((4, 20))
        self.image.fill('white')
        self.rect = self.image.get_rect(center=pos)
        self.velocity: int = velocity
        sound.play()

    def update_state(self) -> None:
        """Update the position y of the laser"""
        self.rect.y += self.velocity
    
    def check_pos(self) -> None:
        if self.rect.bottom <= 0:
            self.kill()
    
    def update(self, dt) -> None:
        self.update_state()
        self.check_pos()


class Player(pygame.sprite.Sprite):
    """Player class
    
    State of the player:
    x_t = (rect_x, rect_y, ready)"""
    def __init__(self, pos, x_range, img_dir: str, laser_sound: pygame.mixer.Sound) -> None:
        super().__init__()

        self.image = pygame.image.load(img_dir + "/player.png").convert_alpha()
        self.rect = self.image.get_rect(midbottom=pos)
        self.x_range = x_range
        self.ready: bool = True
        self.current_cooldown: int = 0
        self.lives: int = LIVES

        self.laser_sound = laser_sound
        self.lasers: pygame.sprite.Group = pygame.sprite.Group()
    
    def check_pos(self) -> None:
        if self.rect.left <= self.x_range[0]:
            self.rect.x = self.x_range[0]
        if self.rect.right >= self.x_range[1]:
            self.rect.right = self.x_range[1]
    
    def is_alive(self):
        return True if self.lives > 0 else False
    
    def update_state(self, keys) -> None:
        # Change the position
        if keys[pygame.K_RIGHT]:
            self.rect.x += SPACECRAFT_SPEED
        if keys[pygame.K_LEFT]:
            self.rect.x -= SPACECRAFT_SPEED
        
        # Throw a laser
        if keys[pygame.K_SPACE] and self.ready:
            self.shoot_laser()
            self.ready = False
            self.current_cooldown = pygame.time.get_ticks()
        self.recharge()
    
    def update(self, dt) -> None:
        # Get inputs
        keys = pygame.key.get_pressed()
        # Update state
        self.update_state(keys)
        # Check pos
        self.check_pos()
        # Update laser
        self.lasers.update(dt)
    
    def recharge(self) -> None:
        """Update the state variable 'ready'"""
        if not self.ready:
            current_time = pygame.time.get_ticks()
            if current_time - self.current_cooldown > LASER_COOLDOWN:
                self.ready = True

    def shoot_laser(self):
        self.lasers.add(Laser(self.rect.center, -LASER_SPEED, self.laser_sound))


class Block(pygame.sprite.Sprite):
    """Block sprite"""
    def __init__(self, size, color, x, y) -> None:
        super().__init__()
        self.image = pygame.Surface((size, size))
        self.image.fill(color)
        self.rect = self.image.get_rect(topleft=(x, y))

class Obstacle():
    """Class to handle Obstacle."""
    def __init__(self, block_size: int) -> None:

        self.shape: list = ['  xxxxxx  ',
                      ' xxxxxxxx ',
                      ' xxxxxxxx ',
                      'xxxxxxxxxx',
                      'xxxxxxxxxx',
                      'xxx    xxx',
                      'xx      xx']
        self.block_size: int = block_size
    
    def create_obstacle(self, group: pygame.sprite.Group, x_start, y_start) -> None:
        """Create an obstacle of shape 'shape' and add the group."""
        for row_index, row in enumerate(self.shape):
            for col_index, col in enumerate(row):
                if col == "x":
                    x = x_start + col_index * self.block_size
                    y = y_start + row_index * self.block_size
                    block = Block(self.block_size, (241, 79, 80), x, y)
                    group.add(block)
    
    def create_many_obstacles(self, group: pygame.sprite.Group, x_start: list[int], y_start: list[int]):
        for x, y in zip(x_start, y_start):
            self.create_obstacle(group, x, y)


class Alien(pygame.sprite.Sprite):
    """This class handles the alien.
    
    State x_t = (x, y, alive)
    """
    def __init__(self, x, y, img_dir: str) -> None:
        super().__init__()

        self.image = pygame.image.load(img_dir).convert_alpha()
        self.rect = self.image.get_rect(topleft=(x, y))

        self.value: int
        if "red" in img_dir: self.value = 100
        elif "green" in img_dir: self.value = 200
        else: self.value = 300
    
    def move_down(self, y_offset: int) -> None:
        self.rect.y += y_offset
    
    def update(self, dir: int) -> None:
        self.rect.x += dir * ALIEN_SPEED


class AliensWave():
    """This class handles a wave of aliens."""
    def __init__(self, img_dir: str, laser_sound: pygame.mixer.Sound) -> None:
        self.wave_dir: int = 1
        self.img_dir = img_dir
        self.group: pygame.sprite.Group = pygame.sprite.Group()
        self.laser_sound = laser_sound
        self.lasers: pygame.sprite.Group = pygame.sprite.Group()
        

    def create_wave(self, rows: int, cols: int, x_dist: int = 60, y_dist: int = 48, x_start: int = 70, y_start: int = 100) -> None:
        for row_index, row in enumerate(range(rows)):
            for col_index, col in enumerate(range(cols)):
                # Compute the coordinates
                x: int = col_index * x_dist + x_start
                y: int = row_index * y_dist + y_start
                # Chose the color
                if row_index == 0: alien_sprite = Alien(x, y, self.img_dir + "/yellow.png")
                elif 1 <= row_index <= 2: alien_sprite = Alien(x, y, self.img_dir + "/green.png")
                else: alien_sprite = Alien(x, y, self.img_dir + "/red.png")
                # Add the group
                self.group.add(alien_sprite)

    def check_position(self) -> None:
        # Not optimal but there is a small numbers of aliens
        all_aliens = self.group.sprites()
        for alien in all_aliens:
            if alien.rect.right >= GAME_W:
                self.wave_dir = -1
                self.move_down(ALIEN_MOVE_DOWN_SPEED)
            if alien.rect.left <= 0:
                self.wave_dir = 1
                self.move_down(ALIEN_MOVE_DOWN_SPEED)
    
    def move_down(self, y_offset) -> None:
        """Move down all the aliens in the wave."""
        all_aliens = self.group.sprites() if self.group else []
        for alien in all_aliens:
            alien.move_down(y_offset)
    
    def still_remaining(self) -> bool:
        all_aliens = self.group.sprites() if self.group else []
        condition: bool = False
        for alien in all_aliens:
            condition = condition or alien.rect.top <= GAME_H
        return condition

    def shoot_laser(self) -> None:
        # Shoot a laser
        if self.group.sprites():
            random_alien = choice(self.group.sprites())
            self.lasers.add(Laser(random_alien.rect.center, ALIEN_LASER_SPEED, self.laser_sound))
    
    def clear_wave(self) -> None:
        self.group.empty()
        self.lasers.empty()

    def update(self, dt) -> None:
        self.check_position()
        self.group.update(self.wave_dir)
        self.lasers.update(dt)
    
    def render(self, surface):
        self.group.draw(surface)
        self.lasers.draw(surface)

    
class Extra(pygame.sprite.Sprite):
    """This class handles an extra alien."""
    def __init__(self, side: str, img_dir: str) -> None:
        assert side in ["left", "right"]
        super().__init__()
        self.image = pygame.image.load(img_dir).convert_alpha()
        self.value: int = 500
        if side == "left":
            x = - 50
            self.speed = EXTRA_SPEED
        else:
            x = GAME_W + 50
            self.speed = -1 * EXTRA_SPEED
        
        self.rect = self.image.get_rect(topleft=(x, 60))
    
    def update(self) -> None:
        self.rect.x += self.speed


if __name__ == "__main__":
    import sys
    pygame.init()
    SCREEN_W = 600
    SCREEN_H = 600
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    font = pygame.font.Font(None, 25)
    laser_sound = pygame.mixer.Sound("./assets/audio/laser.wav")
    player_sprite = Player(pygame.math.Vector2(SCREEN_W//2, SCREEN_H), [0, SCREEN_W], "./assets/graphics", laser_sound)
    player = pygame.sprite.GroupSingle(player_sprite)
    obstacles: pygame.sprite.Group = pygame.sprite.Group()
    aliens: pygame.sprite.Group = pygame.sprite.Group()
    aliens.add(Alien(50, 100, "./assets/graphics/red.png"))
    obs_calc = Obstacle(5)
    obs_calc.create_many_obstacles(obstacles, [75, 475], [3*SCREEN_H//4]*2)

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
        player.update(0)
        aliens.update()
        screen.fill((30, 30, 30))
        obstacles.draw(screen)
        aliens.draw(screen)
        player.draw(screen)
        player.sprite.lasers.draw(screen)
        pygame.display.flip()
        clock.tick(60)
