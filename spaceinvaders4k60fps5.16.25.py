import pygame
import random
import numpy as np

# Constants
FPS = 60
LOGICAL_WIDTH, LOGICAL_HEIGHT = 160, 144
SCALE = 4
WINDOW_WIDTH, WINDOW_HEIGHT = LOGICAL_WIDTH * SCALE, LOGICAL_HEIGHT * SCALE

# To maintain Game Boy speed, update logic at 60 Hz but scale per-step speeds by 20/60
ORIGINAL_RATE = 20
UPDATE_RATE = 60  # Logic updates per second
SPEED_FACTOR = ORIGINAL_RATE / UPDATE_RATE
SHOOT_CHANCE = 0.0025 * SPEED_FACTOR  # Adjusted alien shooting chance per update

# Colors (Game Boy grayscale palette)
BLACK = (0, 0, 0)
DARK_GRAY = (85, 85, 85)
LIGHT_GRAY = (170, 170, 170)
WHITE = (255, 255, 255)

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
game_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))
clock = pygame.time.Clock()
try:
    font = pygame.font.Font(None, 16)
except pygame.error:
    font = pygame.font.SysFont("arial", 16)

# Player class
class Player:
    def __init__(self):
        self.width, self.height = 16, 8
        self.x = LOGICAL_WIDTH // 2 - self.width // 2
        self.y = LOGICAL_HEIGHT - 20
        self.speed = 1.2 * SPEED_FACTOR
        self.color = WHITE

    def move(self, dx):
        self.x += dx * self.speed
        self.x = max(0, min(self.x, LOGICAL_WIDTH - self.width))

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, LIGHT_GRAY, (self.x + self.width // 2 - 2, self.y - 2, 4, 2))

    def reset(self):
        self.x = LOGICAL_WIDTH // 2 - self.width // 2
        self.y = LOGICAL_HEIGHT - 20

# Alien class
class Alien:
    def __init__(self, x, y):
        self.x, self.y = x, y
        self.width, self.height = 12, 8
        self.color = LIGHT_GRAY
        self.speed = 0.2 * SPEED_FACTOR
        self.direction = 1

    def move(self):
        self.x += self.direction * self.speed
        if self.x <= 0 or self.x >= LOGICAL_WIDTH - self.width:
            self.direction *= -1
            self.y += 15

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        pygame.draw.rect(surface, DARK_GRAY, (self.x + 2, self.y + 2, 2, 2))
        pygame.draw.rect(surface, DARK_GRAY, (self.x + self.width - 4, self.y + 2, 2, 2))

# Bullet class
class Bullet:
    def __init__(self, x, y, direction_y):
        self.x, self.y = x, y
        self.width, self.height = 2, 6
        self.speed = 2.5 * SPEED_FACTOR
        self.direction_y = direction_y
        self.color = WHITE if direction_y == 1 else LIGHT_GRAY

    def move(self):
        self.y -= self.direction_y * self.speed

    def draw(self, surface):
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))

# Barrier class
class Barrier:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 12
        self.max_health = 6
        self.health = self.max_health

    def draw(self, surface):
        ratio = self.health / self.max_health
        if ratio > 2 / 3:
            color = LIGHT_GRAY
        elif ratio > 1 / 3:
            color = DARK_GRAY
        else:
            color = BLACK
        pygame.draw.rect(surface, color, (self.x, self.y, self.width, self.height))

    def hit(self):
        self.health -= 1
        return self.health <= 0

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)

# Sound generator
def generate_sound(frequency, duration=0.1, volume=0.5):
    sample_rate = pygame.mixer.get_init()[0]
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    wave = volume * (np.sign(np.sin(2 * np.pi * frequency * t)))
    wave = (wave * 32767).astype(np.int16)
    stereo_wave = np.column_stack((wave, wave))
    return pygame.mixer.Sound(array=stereo_wave)

# Reset helpers

def reset_aliens():
    aliens_list = []
    for row in range(5):
        for col in range(10):
            x = 10 + col * (12 + 3)
            y = 20 + row * (8 + 7)
            aliens_list.append(Alien(x, y))
    return aliens_list


def reset_barriers(player_y):
    barriers = []
    num_barriers = 4
    spacing = LOGICAL_WIDTH // (num_barriers + 1)
    for i in range(num_barriers):
        bx = spacing * (i + 1) - 12
        by = player_y - 25
        barriers.append(Barrier(bx, by))
    return barriers

# Game init
player = Player()
aliens = reset_aliens()
barriers = reset_barriers(player.y)
player_bullets = []
alien_bullets = []

shoot_sound = generate_sound(880, duration=0.05, volume=0.3)
hit_sound = generate_sound(220, duration=0.1, volume=0.4)
lose_life_sound = generate_sound(110, duration=0.3, volume=0.5)

running = True
score = 0
lives = 3
last_update_time = pygame.time.get_ticks()
update_interval_ms = 1000 / UPDATE_RATE
game_over_flag = False
game_won_flag = False

# Main loop
def main():
    pygame.display.set_caption("Space Invaders - Game Boy Style")
    global running, player_bullets, alien_bullets, aliens, barriers, last_update_time, score, lives, game_over_flag, game_won_flag

    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over_flag or game_won_flag:
                    if event.key == pygame.K_SPACE:
                        player.reset()
                        aliens = reset_aliens()
                        barriers = reset_barriers(player.y)
                        player_bullets = []
                        alien_bullets = []
                        score = 0
                        lives = 3
                        game_over_flag = False
                        game_won_flag = False
                        last_update_time = pygame.time.get_ticks()
                elif not game_over_flag:
                    if event.key == pygame.K_SPACE and len(player_bullets) < 3:
                        bullet_x = player.x + player.width // 2 - Bullet(0, 0, 1).width // 2
                        bullet = Bullet(bullet_x, player.y, 1)
                        player_bullets.append(bullet)
                        shoot_sound.play()

        current_time_ms = pygame.time.get_ticks()
        if not game_over_flag and not game_won_flag and (current_time_ms - last_update_time >= update_interval_ms):
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]: player.move(-1)
            if keys[pygame.K_RIGHT]: player.move(1)

            for alien in aliens[:]:
                alien.move()
                if random.random() < SHOOT_CHANCE and len(alien_bullets) < 5:
                    bullet_x = alien.x + alien.width // 2 - Bullet(0, 0, -1).width // 2
                    alien_bullet = Bullet(bullet_x, alien.y + alien.height, -1)
                    alien_bullets.append(alien_bullet)

            for bullet in player_bullets[:]:
                bullet.move()
                if bullet.y + bullet.height < 0:
                    player_bullets.remove(bullet)
                    continue
                for alien in aliens[:]:
                    if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(
                        pygame.Rect(alien.x, alien.y, alien.width, alien.height)):
                        aliens.remove(alien)
                        player_bullets.remove(bullet)
                        score += 10
                        hit_sound.play()
                        if not aliens: game_won_flag = True
                        break
                for barrier in barriers[:]:
                    if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(barrier.rect):
                        player_bullets.remove(bullet)
                        if barrier.hit(): barriers.remove(barrier)
                        break

            for bullet in alien_bullets[:]:
                bullet.move()
                if bullet.y > LOGICAL_HEIGHT:
                    alien_bullets.remove(bullet)
                    continue
                if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(
                    pygame.Rect(player.x, player.y, player.width, player.height)):
                    alien_bullets.remove(bullet)
                    lives -= 1
                    lose_life_sound.play()
                    if lives > 0: player.reset()
                    else: game_over_flag = True
                    continue
                for barrier in barriers[:]:
                    if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(barrier.rect):
                        alien_bullets.remove(bullet)
                        if barrier.hit(): barriers.remove(barrier)
                        break

            if any(alien.y + alien.height >= player.y for alien in aliens):
                lives -= 1
                lose_life_sound.play()
                if lives > 0:
                    player.reset()
                    aliens = reset_aliens()
                    barriers = reset_barriers(player.y)
                    player_bullets = []
                    alien_bullets = []
                else:
                    game_over_flag = True

            last_update_time = current_time_ms

        # Drawing
        game_surface.fill(BLACK)
        if not game_over_flag and not game_won_flag:
            player.draw(game_surface)
            for alien in aliens: alien.draw(game_surface)
            for barrier in barriers: barrier.draw(game_surface)
            for bullet in player_bullets + alien_bullets: bullet.draw(game_surface)

        score_text_surface = font.render(f"SCORE: {score}", True, WHITE)
        game_surface.blit(score_text_surface, (5, 5))
        for i in range(lives):
            icon_x = LOGICAL_WIDTH - (i + 1) * (16 + 5)
            pygame.draw.rect(game_surface, WHITE, (icon_x, 5, 16, 8))
            pygame.draw.rect(game_surface, LIGHT_GRAY, (icon_x + 8 - 2, 3, 4, 2))

        if game_over_flag:
            surface = font.render("GAME OVER", True, WHITE)
            rect = surface.get_rect(center=(LOGICAL_WIDTH//2, LOGICAL_HEIGHT//2 - 10))
            game_surface.blit(surface, rect)
            surface = font.render("Press SPACE to Restart", True, LIGHT_GRAY)
            rect = surface.get_rect(center=(LOGICAL_WIDTH//2, LOGICAL_HEIGHT//2 + 10))
            game_surface.blit(surface, rect)
        if game_won_flag:
            surface = font.render("YOU WIN!", True, WHITE)
            rect = surface.get_rect(center=(LOGICAL_WIDTH//2, LOGICAL_HEIGHT//2 - 10))
            game_surface.blit(surface, rect)
            surface = font.render(f"Final Score: {score}", True, WHITE)
            rect = surface.get_rect(center=(LOGICAL_WIDTH//2, LOGICAL_HEIGHT//2 + 10))
            game_surface.blit(surface, rect)
            surface = font.render("Press SPACE to Play Again", True, LIGHT_GRAY)
            rect = surface.get_rect(center=(LOGICAL_WIDTH//2, LOGICAL_HEIGHT//2 + 30))
            game_surface.blit(surface, rect)

        scaled = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled, (0, 0))
        pygame.display.flip()
        clock.tick(FPS)

    pygame.quit()

if __name__ == "__main__":
    main()
