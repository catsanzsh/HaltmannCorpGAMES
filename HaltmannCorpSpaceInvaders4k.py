import pygame
import random
import numpy as np

# Constants
FPS = 60
LOGICAL_WIDTH, LOGICAL_HEIGHT = 160, 144
SCALE = 4
WINDOW_WIDTH, WINDOW_HEIGHT = LOGICAL_WIDTH * SCALE, LOGICAL_HEIGHT * SCALE
UPDATE_RATE = 20  # Logic updates per second for Game Boy feel

# Colors (Game Boy grayscale palette)
BLACK = (0, 0, 0)
DARK_GRAY = (85, 85, 85)
LIGHT_GRAY = (170, 170, 170)
WHITE = (255, 255, 255)

# Initialize Pygame
pygame.init()
pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)  # Initialize mixer with common parameters
screen = pygame.display.set_mode((WINDOW_WIDTH, WINDOW_HEIGHT))
game_surface = pygame.Surface((LOGICAL_WIDTH, LOGICAL_HEIGHT))  # Low-resolution surface for game rendering
clock = pygame.time.Clock()
# Use a default system font if None is specified, with a small size for Game Boy style
try:
    font = pygame.font.Font(None, 16)
except pygame.error:  # Fallback if default font is not found (less common, but good practice)
    font = pygame.font.SysFont("arial", 16)


# Player class
class Player:
    def __init__(self):
        # Player properties
        self.width, self.height = 16, 8
        self.x = LOGICAL_WIDTH // 2 - self.width // 2  # Centered horizontally
        self.y = LOGICAL_HEIGHT - 20  # Positioned near the bottom
        self.speed = 1.2  # Slightly slower for Game Boy feel
        self.color = WHITE

    def move(self, dx):
        # Move player horizontally, constrained by screen boundaries
        self.x += dx * self.speed
        if self.x < 0:
            self.x = 0
        elif self.x > LOGICAL_WIDTH - self.width:
            self.x = LOGICAL_WIDTH - self.width

    def draw(self, surface):
        # Draw player rectangle (body)
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        # Draw player's cannon
        pygame.draw.rect(surface, LIGHT_GRAY, (self.x + self.width // 2 - 2, self.y - 2, 4, 2))

    def reset(self):
        # Reset player to initial position
        self.x = LOGICAL_WIDTH // 2 - self.width // 2
        self.y = LOGICAL_HEIGHT - 20


# Alien class
class Alien:
    def __init__(self, x, y):
        # Alien properties
        self.x, self.y = x, y
        self.width, self.height = 12, 8
        self.color = LIGHT_GRAY
        self.speed = 0.2  # Much slower for Game Boy feel
        self.direction = 1  # 1 for right, -1 for left

    def move(self):
        # Move alien horizontally
        self.x += self.direction * self.speed
        # If alien hits screen edge, reverse direction and move down
        if self.x <= 0 or self.x >= LOGICAL_WIDTH - self.width:
            self.direction *= -1
            self.y += 15  # Larger step down for classic feel

    def draw(self, surface):
        # Draw alien rectangle (body)
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))
        # Draw alien's "eyes" for detail
        pygame.draw.rect(surface, DARK_GRAY, (self.x + 2, self.y + 2, 2, 2))
        pygame.draw.rect(surface, DARK_GRAY, (self.x + self.width - 4, self.y + 2, 2, 2))


# Bullet class
class Bullet:
    def __init__(self, x, y, direction_y):
        # Bullet properties
        self.x, self.y = x, y
        self.width, self.height = 2, 6
        self.speed = 2.5  # Slightly slower for Game Boy feel
        self.direction_y = direction_y  # 1 for up (player), -1 for down (alien)
        # Color depends on who shot the bullet
        self.color = WHITE if direction_y == 1 else LIGHT_GRAY

    def move(self):
        # Move bullet vertically
        self.y -= self.direction_y * self.speed

    def draw(self, surface):
        # Draw bullet rectangle
        pygame.draw.rect(surface, self.color, (self.x, self.y, self.width, self.height))


# Barrier class (protective bunkers in front of the player)
class Barrier:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.width = 24
        self.height = 12
        self.max_health = 6  # Number of hits barrier can sustain
        self.health = self.max_health

    def draw(self, surface):
        # Change color based on remaining health
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
        return self.health <= 0  # Returns True if destroyed

    @property
    def rect(self):
        return pygame.Rect(self.x, self.y, self.width, self.height)


# Generate chiptune-like sound (square wave)
def generate_sound(frequency, duration=0.1, volume=0.5):
    sample_rate = pygame.mixer.get_init()[0]  # Get sample rate from initialized mixer
    n_samples = int(sample_rate * duration)
    t = np.linspace(0, duration, n_samples, False)
    # Generate square wave: sign of sine wave
    wave = volume * (np.sign(np.sin(2 * np.pi * frequency * t)))
    # Scale to 16-bit integer range
    wave = (wave * 32767).astype(np.int16)
    # Create stereo wave by stacking two mono waves
    stereo_wave = np.column_stack((wave, wave))
    sound = pygame.mixer.Sound(array=stereo_wave)
    return sound


# Helper functions

def reset_aliens():
    aliens_list = []
    for row in range(5):  # 5 rows of aliens
        for col in range(10):  # 10 aliens per row
            x = 10 + col * (12 + 3)  # Alien width + spacing
            y = 20 + row * (8 + 7)  # Alien height + spacing
            aliens_list.append(Alien(x, y))
    return aliens_list


def reset_barriers(player_y):
    barriers = []
    num_barriers = 4
    spacing = LOGICAL_WIDTH // (num_barriers + 1)
    for i in range(num_barriers):
        bx = spacing * (i + 1) - 12  # Center barrier
        by = player_y - 25  # Positioned above the player
        barriers.append(Barrier(bx, by))
    return barriers


# --- Game Objects and State Variables ---
player = Player()
aliens = reset_aliens()
barriers = reset_barriers(player.y)
player_bullets = []
alien_bullets = []

# Sounds
shoot_sound = generate_sound(880, duration=0.05, volume=0.3)  # Higher pitch for player shot
hit_sound = generate_sound(220, duration=0.1, volume=0.4)  # Lower pitch for alien hit
lose_life_sound = generate_sound(110, duration=0.3, volume=0.5)  # Sound for losing a life

# Game state
running = True
score = 0
lives = 3
last_update_time = pygame.time.get_ticks()  # Time of the last logic update
update_interval_ms = 1000 / UPDATE_RATE  # Milliseconds per logic update
game_over_flag = False
game_won_flag = False


def main():
    pygame.display.set_caption("Space Invaders - Game Boy Style")
    global running, player_bullets, alien_bullets, aliens, barriers, last_update_time, score, lives, game_over_flag, game_won_flag

    while running:
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if game_over_flag or game_won_flag:  # If game is over or won, allow restart with space
                    if event.key == pygame.K_SPACE:
                        # Reset game state
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
                elif not game_over_flag:  # Only allow shooting if game is active
                    if event.key == pygame.K_SPACE and len(player_bullets) < 3:  # Limit player bullets on screen
                        bullet_x = player.x + player.width // 2 - Bullet(0, 0, 1).width // 2  # Center bullet
                        bullet = Bullet(bullet_x, player.y, 1)
                        player_bullets.append(bullet)
                        shoot_sound.play()

        current_time_ms = pygame.time.get_ticks()

        # --- Game Logic Update (runs at UPDATE_RATE) ---
        if not game_over_flag and not game_won_flag and (current_time_ms - last_update_time >= update_interval_ms):
            # Player movement from held keys
            keys = pygame.key.get_pressed()
            if keys[pygame.K_LEFT]:
                player.move(-1)
            if keys[pygame.K_RIGHT]:
                player.move(1)

            # Update aliens
            for alien in aliens[:]:  # Iterate over a copy for safe removal
                alien.move()
                # Alien shooting logic (random chance)
                if random.random() < 0.0025:  # Slightly increased chance for more action
                    if len(alien_bullets) < 5:  # Limit total alien bullets on screen
                        bullet_x = alien.x + alien.width // 2 - Bullet(0, 0, -1).width // 2
                        alien_bullet = Bullet(bullet_x, alien.y + alien.height, -1)
                        alien_bullets.append(alien_bullet)

            # Update player bullets
            for bullet in player_bullets[:]:
                bullet.move()
                if bullet.y + bullet.height < 0:  # Bullet off-screen (top)
                    player_bullets.remove(bullet)
                    continue

                # Check collision with aliens
                for alien in aliens[:]:
                    if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(
                        pygame.Rect(alien.x, alien.y, alien.width, alien.height)):
                        try:
                            aliens.remove(alien)
                            player_bullets.remove(bullet)
                        except ValueError:
                            pass
                        score += 10  # Award 10 points per alien
                        hit_sound.play()
                        if not aliens:  # All aliens defeated
                            game_won_flag = True
                        break

                # Check collision with barriers (player bullets damage own barriers too)
                for barrier in barriers[:]:
                    if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(barrier.rect):
                        try:
                            player_bullets.remove(bullet)
                        except ValueError:
                            pass
                        destroyed = barrier.hit()
                        if destroyed:
                            barriers.remove(barrier)
                        break

            # Update alien bullets
            for bullet in alien_bullets[:]:
                bullet.move()
                if bullet.y > LOGICAL_HEIGHT:  # Bullet off-screen (bottom)
                    alien_bullets.remove(bullet)
                    continue

                # Check collision with player
                if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(
                    pygame.Rect(player.x, player.y, player.width, player.height)):
                    try:
                        alien_bullets.remove(bullet)
                    except ValueError:
                        pass
                    lives -= 1
                    lose_life_sound.play()
                    if lives > 0:
                        player.reset()
                    else:
                        game_over_flag = True
                    continue

                # Check collision with barriers
                for barrier in barriers[:]:
                    if pygame.Rect(bullet.x, bullet.y, bullet.width, bullet.height).colliderect(barrier.rect):
                        try:
                            alien_bullets.remove(bullet)
                        except ValueError:
                            pass
                        destroyed = barrier.hit()
                        if destroyed:
                            barriers.remove(barrier)
                        break

            # Check if aliens reach player's level (invasion)
            alien_has_reached_player = any(alien.y + alien.height >= player.y for alien in aliens)

            if alien_has_reached_player:
                lives -= 1
                lose_life_sound.play()
                if lives > 0:
                    player.reset()
                    aliens = reset_aliens()  # Full reset of aliens
                    barriers = reset_barriers(player.y)
                    player_bullets = []
                    alien_bullets = []
                else:
                    game_over_flag = True

            last_update_time = current_time_ms  # Reset update timer

        # --- Drawing ---
        game_surface.fill(BLACK)  # Clear game surface

        if not game_over_flag and not game_won_flag:
            player.draw(game_surface)
            for alien in aliens:
                alien.draw(game_surface)
            for barrier in barriers:
                barrier.draw(game_surface)
            for bullet in player_bullets + alien_bullets:  # Draw all bullets
                bullet.draw(game_surface)

        # Draw score
        score_text_surface = font.render(f"SCORE: {score}", True, WHITE)
        game_surface.blit(score_text_surface, (5, 5))

        # Draw lives as small player ship icons
        life_icon_width, life_icon_height = 16, 8
        for i in range(lives):
            icon_x = LOGICAL_WIDTH - (i + 1) * (life_icon_width + 5)  # Position from right
            pygame.draw.rect(game_surface, WHITE, (icon_x, 5, life_icon_width, life_icon_height))
            pygame.draw.rect(game_surface, LIGHT_GRAY, (icon_x + life_icon_width // 2 - 2, 3, 4, 2))  # Cannon

        # Draw Game Over message
        if game_over_flag:
            game_over_surface = font.render("GAME OVER", True, WHITE)
            text_rect = game_over_surface.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 10))
            game_surface.blit(game_over_surface, text_rect)

            restart_surface = font.render("Press SPACE to Restart", True, LIGHT_GRAY)
            restart_rect = restart_surface.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 10))
            game_surface.blit(restart_surface, restart_rect)

        # Draw Game Won message
        if game_won_flag:
            game_won_surface = font.render("YOU WIN!", True, WHITE)
            text_rect = game_won_surface.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 - 10))
            game_surface.blit(game_won_surface, text_rect)

            final_score_surface = font.render(f"Final Score: {score}", True, WHITE)
            final_score_rect = final_score_surface.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 10))
            game_surface.blit(final_score_surface, final_score_rect)

            restart_surface = font.render("Press SPACE to Play Again", True, LIGHT_GRAY)
            restart_rect = restart_surface.get_rect(center=(LOGICAL_WIDTH // 2, LOGICAL_HEIGHT // 2 + 30))
            game_surface.blit(restart_surface, restart_rect)

        # Scale the low-resolution game surface to the window size
        scaled_surface = pygame.transform.scale(game_surface, (WINDOW_WIDTH, WINDOW_HEIGHT))
        screen.blit(scaled_surface, (0, 0))

        pygame.display.flip()  # Update the full display

        clock.tick(FPS)  # Maintain 60 FPS rendering rate

    pygame.quit()


if __name__ == "__main__":
    main()
