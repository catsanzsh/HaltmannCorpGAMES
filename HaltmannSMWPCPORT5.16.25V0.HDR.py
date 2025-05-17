import pygame
import sys
import math # For potential future use, e.g., animations

# --- Configuration ---
WIDTH, HEIGHT = 800, 600
FPS = 60
TILE_SIZE = 30
GRAVITY = 0.7
PLAYER_JUMP_VELOCITY = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 1.5
MUSHROOM_SPEED = 2

# --- Palette ---
SKY_BLUE = (135, 206, 250)
GRASS_GREEN = (34, 139, 34) # For overworld map
PATH_YELLOW = (255, 223, 186) # For paths on overworld
BROWN = (139, 69, 19)      # Solid blocks
GOLD = (255, 215, 0)       # Question blocks
YELLOW = (255, 255, 0)     # Coins
RED = (220, 20, 60)        # Player
GREEN = (0, 128, 0)        # Enemies (Goombas)
BRIGHT_RED = (255, 0, 0)   # Mushrooms
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (205, 133, 63) # Hit Question Block / Empty Block
BRICK_COLOR = (170, 74, 68)  # Breakable bricks
LEVEL_NODE_COLOR = (70, 130, 180) # Steel Blue for level nodes
LEVEL_NODE_CLEARED_COLOR = (60, 179, 113) # Medium Sea Green
LEVEL_NODE_HIGHLIGHT_COLOR = (255, 165, 0) # Orange

# --- Game States ---
START_MENU = 0
PLAYING = 1
LEVEL_CLEAR = 2
GAME_OVER = 3
GAME_WON = 4
OVERWORLD = 5 # New state for level selection

# --- World and Level Definitions ---
# 'S': Solid, 'P': Player, 'E': Enemy, '?': Question (Coin/Mushroom),
# 'B': Breakable Brick, 'C': Coin (direct), 'G': Goal
# 'M': Mushroom (direct - for testing, usually from '?')
worlds = {
    1: {
        "name": "Yoshi's Island",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
                "S                                      S",
                "S                                      S",
                "S        ???                           S",
                "S       SBBBS                          S",
                "S P   S.....S         C C C            S",
                "S     S.....S   B?B         E          S",
                "S    SS...SS   BB.BB                 G S",
                "S   S.......S SSSSSSS   SSSS      SSSSS",
                "S  S.........S                       S S",
                "S S...........S       E              S S",
                "S S.............S SSSSSSSSSSSSSSSSSSS S",
                "S S...............S                   S S",
                "S SSSSSSSSSSSSSSSSS                   S S",
                "S                                     S S",
                "S                  E                  S S",
                "S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
            ],
            2: [
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
                "S                                      S",
                "S  P      ?????                      S",
                "S SSSSS  SSSSSSSSS                     S",
                "S                                      S",
                "S      C C C                           S",
                "S     BBBBBBB                          S",
                "S    SSSSSSSSS                         S",
                "S                 E         E          S",
                "S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS   S",
                "S                                      S",
                "S                                  G   S",
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
            ],
            3: [ # New Level 1-3
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
                "S G                                    S",
                "S SSSSSS                               S",
                "S      S                               S",
                "S  P   S   E   E   E                 S",
                "S SSSSSSSSSSSSSSSSSSSSSSSSSSSS         S",
                "S S                          S         S",
                "S S   ????                   S         S",
                "S S   SBBBS                  S         S",
                "S S   S...S  SSSSSSSSSSSSSSSSS         S",
                "S S   S...S  S                         S",
                "S SSSSS...SSSS                         S",
                "S     S...S                            S",
                "S     S...S      C M C                 S",
                "S     SSSSS    BBBBBBBBB               S",
                "S              SSSSSSSSS               S",
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    2: {
        "name": "Donut Plains",
        "levels": {
            1: [ # New Level 2-1 (was World 2, Level 1)
                "SSSSSSSSSSSSSSSSSSSS",
                "S P                S",
                "S SSS    BBBB    S S",
                "S   S    ????    S S",
                "S   S    S..S    S S",
                "S E S    S..S  E S S",
                "S SSSSSS S..SSSSSS S",
                "S        S..S      S",
                "S C      S..S    C S",
                "S SSSSSSSSSSSSSSSG S",
                "SSSSSSSSSSSSSSSSSSSS",
            ],
            2: [ # New Level 2-2
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
                "S P                          S",
                "S SSS                        S",
                "S      E                     S",
                "S SSSSSSSSSS ??? SSSSSSSSSSSSS",
                "S            S.B.S           S",
                "S            S.B.S  E        S",
                "S C          S...S           S",
                "S SSSSSSSSSSSS...SSSSSSSSSSSSS",
                "S            S...S           S",
                "S M          S...S         G S",
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
            ]
        }
    }
}

# Overworld level node positions and connections
# (world_id, level_id): (x, y, "Name", next_level_tuple or None)
# next_level_tuple is (next_world_id, next_level_id)
overworld_nodes = {
    (1, 1): {"pos": (150, 200), "name": "1-1", "next": (1, 2)},
    (1, 2): {"pos": (250, 200), "name": "1-2", "next": (1, 3)},
    (1, 3): {"pos": (350, 200), "name": "1-3", "next": (2, 1)},
    (2, 1): {"pos": (200, 350), "name": "2-1", "next": (2, 2)},
    (2, 2): {"pos": (300, 350), "name": "2-2", "next": None}, # Last level in this demo
}


class FontManager:
    """Handles loading and rendering fonts."""
    def __init__(self):
        self.default_font_small = pygame.font.Font(None, 36)
        self.default_font_medium = pygame.font.Font(None, 48)
        self.default_font_large = pygame.font.Font(None, 72)

    def render(self, surface, text, position, color, size="small", center=False):
        font = self.default_font_small
        if size == "large":
            font = self.default_font_large
        elif size == "medium":
            font = self.default_font_medium
        
        text_surface = font.render(text, True, color)
        text_rect = text_surface.get_rect()
        if center:
            text_rect.center = position
        else:
            text_rect.topleft = position
        surface.blit(text_surface, text_rect)

class Level:
    """Represents the game level, including tilemap and drawing."""
    def __init__(self, tilemap_str_list):
        self.tilemap = [list(row) for row in tilemap_str_list] # Mutable list of lists
        self.rows = len(self.tilemap)
        self.cols = len(self.tilemap[0]) if self.rows > 0 else 0
        self.width = self.cols * TILE_SIZE
        self.height = self.rows * TILE_SIZE

    def get_tile(self, grid_x: int, grid_y: int) -> str:
        """Gets the tile character at a grid position."""
        if 0 <= grid_y < self.rows and 0 <= grid_x < self.cols:
            return self.tilemap[grid_y][grid_x]
        return " " # Return empty space for out-of-bounds

    def is_solid(self, grid_x: int, grid_y: int) -> bool:
        """Checks if a tile is solid for collision."""
        tile = self.get_tile(grid_x, grid_y)
        # 'Q' is a hit question block, still solid.
        return tile in ['S', 'Q', 'B']

    def is_breakable_brick(self, grid_x: int, grid_y: int) -> bool:
        """Checks if a tile is a breakable brick."""
        return self.get_tile(grid_x, grid_y) == 'B'

    def hit_block(self, grid_x: int, grid_y: int, player_power_up: str, game_items_group: pygame.sprite.Group, game):
        """Handles player hitting a block from below. Items are added to game_items_group."""
        tile = self.get_tile(grid_x, grid_y)
        block_center_x = grid_x * TILE_SIZE + TILE_SIZE // 2
        spawn_y = (grid_y - 1) * TILE_SIZE # Item spawns above the block

        if tile == '?':
            self.tilemap[grid_y][grid_x] = 'Q' # Change to hit question block
            item_type = "mushroom" if player_power_up == "small" else "coin"
            
            new_item = Item(block_center_x - TILE_SIZE // 2, spawn_y, item_type, self)
            new_item.vel_y = -5 # Pop out effect
            game_items_group.add(new_item) # Add to the sprite group
            game.play_sound("bonk_block") # Sound for hitting a question block
            return True 

        elif tile == 'B':
            if player_power_up == "big":
                self.tilemap[grid_y][grid_x] = '.' # Break the brick
                game.play_sound("break_brick") # Sound for breaking brick
                # TODO: Add particle effect or score for breaking bricks
                return True 
            else:
                game.play_sound("bonk_solid") # Small player bonks head
                return False 
        return False


    def draw(self, surface, cam_x):
        """Draws the visible part of the level."""
        start_col = cam_x // TILE_SIZE
        end_col = start_col + (WIDTH // TILE_SIZE) + 2 

        for y, row_list in enumerate(self.tilemap):
            for x in range(max(0, start_col), min(self.cols, end_col)):
                cell = row_list[x]
                rect = pygame.Rect(x * TILE_SIZE - cam_x, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if cell == "S":
                    pygame.draw.rect(surface, BROWN, rect)
                elif cell == "?":
                    pygame.draw.rect(surface, GOLD, rect)
                elif cell == "Q": # Hit question block
                    pygame.draw.rect(surface, LIGHT_BROWN, rect)
                elif cell == "B":
                    pygame.draw.rect(surface, BRICK_COLOR, rect)
                elif cell == "C": 
                    pygame.draw.circle(surface, YELLOW, rect.center, TILE_SIZE // 3)
                elif cell == "M": 
                     pygame.draw.rect(surface, BRIGHT_RED, rect.inflate(-TILE_SIZE//3, -TILE_SIZE//3))
                elif cell == "G":
                    pygame.draw.rect(surface, GREEN, rect) 
                    pygame.draw.circle(surface, WHITE, rect.center, TILE_SIZE // 3)


class Entity(pygame.sprite.Sprite):
    """Base class for Player and Enemy."""
    def __init__(self, spawn_x: int, spawn_y: int, level: Level, color, width=TILE_SIZE, height=TILE_SIZE):
        super().__init__()
        self.image = pygame.Surface([width, height]) # Base image
        self.image.fill(color) # Fill with color
        self.rect = self.image.get_rect()
        self.rect.topleft = (spawn_x * TILE_SIZE, spawn_y * TILE_SIZE)
        
        self.level = level
        self.vel_x = 0.0
        self.vel_y = 0.0
        self._on_ground = False
        self.color = color # Store color for potential changes (e.g. powerups)
        self.initial_spawn_x_tile = spawn_x # Store tile coordinates
        self.initial_spawn_y_tile = spawn_y

    def _move_axis(self, dx: float, dy: float, game=None): # Pass game for player block hitting
        """Move entity and resolve collisions along one axis at a time."""
        self.rect.x += dx
        self._resolve_collisions(axis="x", game=game)

        self.rect.y += dy
        self._resolve_collisions(axis="y", game=game)


    def _resolve_collisions(self, axis: str, game=None): # Pass game for player block hitting
        """Resolves collisions with solid tiles after movement."""
        margin = 1 
        left_tile = self.rect.left // TILE_SIZE
        right_tile = (self.rect.right - margin) // TILE_SIZE
        top_tile = self.rect.top // TILE_SIZE
        bottom_tile = (self.rect.bottom - margin) // TILE_SIZE

        for gy in range(top_tile, bottom_tile + 1):
            for gx in range(left_tile, right_tile + 1):
                if self.level.is_solid(gx, gy):
                    tile_rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                    if self.rect.colliderect(tile_rect):
                        if axis == "x":
                            if self.vel_x > 0: self.rect.right = tile_rect.left
                            elif self.vel_x < 0: self.rect.left = tile_rect.right
                            if isinstance(self, Enemy): self.vel_x *= -1
                            else: self.vel_x = 0
                        elif axis == "y":
                            if self.vel_y > 0: 
                                self.rect.bottom = tile_rect.top
                                self._on_ground = True
                            elif self.vel_y < 0: 
                                self.rect.top = tile_rect.bottom
                                if isinstance(self, Player) and game: # Player hitting block
                                    # Pass game.items (the sprite group) to hit_block
                                    self.level.hit_block(gx, gy, self.power_up, game.items, game)
                            self.vel_y = 0
    
    def respawn(self):
        self.rect.x = self.initial_spawn_x_tile * TILE_SIZE
        self.rect.y = self.initial_spawn_y_tile * TILE_SIZE
        self.vel_x = 0
        self.vel_y = 0
        self._on_ground = False
        if isinstance(self, Enemy): 
            self.vel_x = -ENEMY_SPEED # Reset enemy direction
        if isinstance(self, Player): # Player specific respawn
            self.power_up = "small"
            self.rect.height = TILE_SIZE
            self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
            self.image.fill(self.color)


    def draw(self, surface, cam_x):
        """Draws the entity."""
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        surface.blit(self.image, draw_rect)


class Player(Entity):
    """Represents the player character."""
    def __init__(self, spawn_x: int, spawn_y: int, level: Level):
        super().__init__(spawn_x, spawn_y, level, RED, TILE_SIZE, TILE_SIZE)
        self.power_up = "small"  # "small", "big"
        self.lives = 3
        self.score = 0
        self.invincible_timer = 0 
        self.on_goal = False

    def update(self, keys, game): # Pass game for item spawning and sounds
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        self.vel_x = 0
        if keys[pygame.K_LEFT]: self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]: self.vel_x = PLAYER_SPEED

        if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self._on_ground:
            self.vel_y = PLAYER_JUMP_VELOCITY
            self._on_ground = False 
            game.play_sound("jump")

        self.vel_y += GRAVITY
        if self.vel_y > TILE_SIZE: self.vel_y = TILE_SIZE # Terminal velocity

        self._on_ground = False 
        self._move_axis(self.vel_x, self.vel_y, game) # Pass game for block hitting

        if self.rect.top > self.level.height + TILE_SIZE * 2 : 
            self.take_damage(game, fall_death=True)

        # Check for goal
        # Simpler goal check: if player center is within a goal tile
        player_center_gx = self.rect.centerx // TILE_SIZE
        player_center_gy = self.rect.centery // TILE_SIZE
        if self.level.get_tile(player_center_gx, player_center_gy) == 'G':
             # Check if any part of the player overlaps a goal tile
            left_tile = self.rect.left // TILE_SIZE
            right_tile = (self.rect.right -1) // TILE_SIZE
            top_tile = self.rect.top // TILE_SIZE
            bottom_tile = (self.rect.bottom -1) // TILE_SIZE
            for gy_g in range(top_tile, bottom_tile + 1):
                for gx_g in range(left_tile, right_tile + 1):
                    if self.level.get_tile(gx_g, gy_g) == 'G':
                        self.on_goal = True
                        break
                if self.on_goal: break


    def take_damage(self, game, fall_death=False): 
        if self.invincible_timer > 0 and not fall_death: return

        if self.power_up == "big":
            self.power_up = "small"
            self.rect.height = TILE_SIZE 
            self.rect.y += TILE_SIZE 
            self.image = pygame.Surface([TILE_SIZE, TILE_SIZE]) # Resize surface
            self.image.fill(self.color)
            self.invincible_timer = FPS * 2 
            game.play_sound("power_down")
        else:
            self.lives -= 1
            self.invincible_timer = FPS * 1 
            if self.lives <= 0:
                game.game_state = GAME_OVER
                game.play_sound("game_over_player")
            else:
                self.respawn() 
                game.play_sound("player_die")


    def collect_item(self, item, game): 
        if item.type == "mushroom":
            if self.power_up == "small":
                self.power_up = "big"
                self.rect.height = TILE_SIZE * 2
                self.rect.y -= TILE_SIZE 
                self.image = pygame.Surface([TILE_SIZE, TILE_SIZE * 2]) # Resize surface
                self.image.fill(self.color)
                game.play_sound("power_up")
            self.score += 1000 
        elif item.type == "coin":
            self.score += 200
            game.play_sound("coin")
        return True 

    # Respawn is handled by Entity, player specific parts are in Entity.respawn()

    def draw(self, surface, cam_x):
        if self.invincible_timer > 0 and (self.invincible_timer // (FPS // 10)) % 2 == 0:
            return # Skip drawing for blink effect

        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        
        # Color doesn't change for big player in this version, size is the indicator
        surface.blit(self.image, draw_rect)

class Enemy(Entity):
    """Represents an enemy character."""
    def __init__(self, spawn_x: int, spawn_y: int, level: Level):
        super().__init__(spawn_x, spawn_y, level, GREEN)
        self.vel_x = -ENEMY_SPEED 

    def update(self):
        self.vel_y += GRAVITY
        if self.vel_y > TILE_SIZE: self.vel_y = TILE_SIZE
        
        self._on_ground = False 

        # Ledge and wall detection
        if self._on_ground: 
            next_step_gx = -1
            wall_check_gx = -1
            if self.vel_x < 0: 
                next_step_gx = (self.rect.left - 1) // TILE_SIZE 
                wall_check_gx = (self.rect.left -1) // TILE_SIZE
            elif self.vel_x > 0: 
                next_step_gx = self.rect.right // TILE_SIZE
                wall_check_gx = self.rect.right // TILE_SIZE
            
            if next_step_gx != -1:
                ground_level_gy = (self.rect.bottom) // TILE_SIZE # Check tile below next step
                enemy_mid_gy = self.rect.centery // TILE_SIZE

                # Check for solid tile for ledge detection slightly below enemy's current bottom
                # to ensure it's actually a ledge and not a 1-tile high step down.
                # For simplicity, we check the tile directly at ground_level_gy.
                # A more robust check would be self.level.is_solid(next_step_gx, ground_level_gy +1)
                # but that might make them fall off 1-tile high platforms.
                
                # If there's a wall in front (at enemy's height) OR no ground ahead
                if self.level.is_solid(wall_check_gx, enemy_mid_gy) or \
                   not self.level.is_solid(next_step_gx, ground_level_gy):
                    # Collision resolution will handle wall turning.
                    # For ledges, explicitly turn here.
                    if not self.level.is_solid(next_step_gx, ground_level_gy) and not self.level.is_solid(wall_check_gx, enemy_mid_gy):
                         self.vel_x *= -1
        
        self._move_axis(self.vel_x, self.vel_y)

        if self.rect.top > self.level.height + TILE_SIZE * 3: # Increased leeway
            self.kill()


class Item(pygame.sprite.Sprite):
    """Represents collectible items like mushrooms and coins."""
    def __init__(self, x: int, y: int, item_type: str, level: Level): # x, y are world coords
        super().__init__()
        self.type = item_type
        self.level = level
        self.vel_x = 0
        self.vel_y = 0
        self._on_ground = False

        if self.type == "mushroom":
            self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
            self.image.fill(BRIGHT_RED)
            # Simple eyes for mushroom
            eye_radius = TILE_SIZE // 8
            pygame.draw.circle(self.image, WHITE, (TILE_SIZE//2 - TILE_SIZE//4, TILE_SIZE//2 - TILE_SIZE//5), eye_radius)
            pygame.draw.circle(self.image, WHITE, (TILE_SIZE//2 + TILE_SIZE//4, TILE_SIZE//2 - TILE_SIZE//5), eye_radius)
            pygame.draw.circle(self.image, BLACK, (TILE_SIZE//2 - TILE_SIZE//4, TILE_SIZE//2 - TILE_SIZE//5), eye_radius//2)
            pygame.draw.circle(self.image, BLACK, (TILE_SIZE//2 + TILE_SIZE//4, TILE_SIZE//2 - TILE_SIZE//5), eye_radius//2)

            self.rect = self.image.get_rect(topleft=(x,y))
            self.vel_x = MUSHROOM_SPEED 
        elif self.type == "coin":
            self.image = pygame.Surface([TILE_SIZE // 2, TILE_SIZE // 2])
            self.image.set_colorkey(BLACK) # Make background transparent if needed
            self.image.fill(BLACK) # Fill with colorkey color first
            pygame.draw.circle(self.image, YELLOW, (TILE_SIZE // 4, TILE_SIZE // 4), TILE_SIZE // 4)
            pygame.draw.circle(self.image, GOLD, (TILE_SIZE // 4, TILE_SIZE // 4), TILE_SIZE // 5, width=1) # Outline
            
            self.rect = self.image.get_rect(topleft=(x,y))
            self.rect.centerx = x + TILE_SIZE // 2 
            self.rect.centery = y + TILE_SIZE // 2
            self.lifetime = FPS * 0.7 # Coin disappears after a bit
        
        self.initial_y = y 

    def update(self):
        if self.type == "mushroom":
            self.vel_y += GRAVITY
            if self.vel_y > TILE_SIZE: self.vel_y = TILE_SIZE
            
            self._on_ground = False
            
            # Mushroom X movement and collision (simplified from Entity)
            self.rect.x += self.vel_x
            left_tile = self.rect.left // TILE_SIZE
            right_tile = (self.rect.right - 1) // TILE_SIZE
            top_tile = self.rect.top // TILE_SIZE
            bottom_tile = (self.rect.bottom - 1) // TILE_SIZE

            for gy in range(top_tile, bottom_tile + 1):
                for gx in range(left_tile, right_tile + 1):
                    if self.level.is_solid(gx, gy):
                        tile_rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if self.rect.colliderect(tile_rect):
                            if self.vel_x > 0: self.rect.right = tile_rect.left
                            elif self.vel_x < 0: self.rect.left = tile_rect.right
                            self.vel_x *= -1 
                            break 
                if self.vel_x == 0 and self.type == "mushroom": # Unstick
                     self.vel_x = MUSHROOM_SPEED if pygame.time.get_ticks() % 2 == 0 else -MUSHROOM_SPEED

            # Mushroom Y movement and collision
            self.rect.y += self.vel_y
            left_tile = self.rect.left // TILE_SIZE # Recheck after x-move
            right_tile = (self.rect.right - 1) // TILE_SIZE
            top_tile = self.rect.top // TILE_SIZE
            bottom_tile = (self.rect.bottom - 1) // TILE_SIZE
            for gy in range(top_tile, bottom_tile + 1):
                for gx in range(left_tile, right_tile + 1):
                    if self.level.is_solid(gx, gy):
                        tile_rect = pygame.Rect(gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                        if self.rect.colliderect(tile_rect):
                            if self.vel_y > 0: 
                                self.rect.bottom = tile_rect.top
                                self._on_ground = True
                            elif self.vel_y < 0: self.rect.top = tile_rect.bottom
                            self.vel_y = 0
                            break
            
            if self.rect.top > self.level.height + TILE_SIZE * 5: 
                self.kill() 

        elif self.type == "coin":
            if self.vel_y != 0 : # Initial pop
                self.rect.y += self.vel_y
                self.vel_y += GRAVITY * 0.5 
                if self.rect.y > self.initial_y : 
                    self.rect.y = self.initial_y
                    self.vel_y = 0

            if self.vel_y == 0: 
                self.lifetime -=1
                if self.lifetime <=0:
                    self.kill() 

    def draw(self, surface, cam_x): # Items need cam_x for drawing
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        surface.blit(self.image, draw_rect)


class Game:
    """Main game class orchestrating everything."""
    def __init__(self):
        pygame.init()
        try:
            pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512)
            self.sounds_enabled = True
        except pygame.error:
            self.sounds_enabled = False
            print("Warning: Pygame mixer could not be initialized. Sounds will be disabled.")

        pygame.display.set_caption("Super Platformer Engine")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_manager = FontManager()
        self.running = True
        self.game_state = START_MENU

        self.current_world_idx = 1
        self.current_level_idx = 1
        
        self.level = None
        self.player = None # Will be initialized in _load_level_data or reset_game
        self.enemies = pygame.sprite.Group() 
        self.items = pygame.sprite.Group()   

        self.cam_x = 0
        self._load_sounds()

        # Overworld state
        self.overworld_cursor_node_key = (1,1) # Start at level 1-1
        self.unlocked_levels = set([(1,1)]) # Initially only 1-1 is unlocked
        self.cleared_levels = set() # Track cleared levels e.g. (world_idx, level_idx)


    def _load_sounds(self):
        self.sounds = {
            "jump": None, "coin": None, "power_up": None, "power_down": None,
            "stomp": None, "bonk_block": None, "bonk_solid": None, "break_brick": None,
            "player_die": None, "game_over_player": None, "level_clear_sound": None,
            "overworld_move": None, "overworld_select": None
        }
        if not self.sounds_enabled: return

        # Placeholder for actual sound generation (e.g., using sfxr or similar)
        # For now, these will be silent if no sound files are loaded.
        # Example: self.sounds["jump"] = pygame.mixer.Sound("path/to/jump.wav")
        # Since "no png" was a constraint, I'm assuming no external assets for sounds either.
        # If you have simple sound generation functions (e.g. creating square waves),
        # they could be used here with pygame.sndarray.make_sound().

    def play_sound(self, sound_name):
        if self.sounds_enabled and self.sounds.get(sound_name):
            try:
                self.sounds[sound_name].play()
            except AttributeError: # If sound is None
                pass # print(f"Debug: Sound '{sound_name}' is None.")
        # else:
        #     print(f"Debug: Sound '{sound_name}' not found or not loaded, or sounds disabled.")


    def _find_spawn_points(self, char_to_find: str) -> list[tuple[int, int]]:
        spawns = []
        if not self.level: return spawns
        for y, row in enumerate(self.level.tilemap):
            for x, cell in enumerate(row):
                if cell == char_to_find:
                    spawns.append((x, y))
        return spawns

    def _load_level_data(self, world_idx, level_idx):
        """Loads the tilemap and initializes player, enemies, items for the chosen level."""
        try:
            tilemap_str_list = worlds[world_idx]["levels"][level_idx]
            self.current_world_idx = world_idx
            self.current_level_idx = level_idx
        except KeyError:
            print(f"Error: Level {world_idx}-{level_idx} not found in worlds data!")
            # This could happen if overworld_nodes points to a non-existent level
            # Or if trying to load next level that doesn't exist (should be caught by GAME_WON)
            self.game_state = OVERWORLD # Go back to overworld to prevent crash
            return False

        self.level = Level(tilemap_str_list)
        
        player_spawns = self._find_spawn_points("P")
        player_spawn_x, player_spawn_y = (1, self.level.rows - 3) if not player_spawns else player_spawns[0]
        
        # If player exists (from previous level), update its state, else create new
        if self.player is None:
            self.player = Player(player_spawn_x, player_spawn_y, self.level)
            # Lives and score are preserved across levels if player object persists.
            # If starting a new game entirely, these are reset in reset_game().
        else:
            self.player.level = self.level
            self.player.initial_spawn_x_tile = player_spawn_x
            self.player.initial_spawn_y_tile = player_spawn_y
            self.player.respawn() # Resets position, powerup, image to small

        self.enemies.empty() 
        enemy_spawns = self._find_spawn_points("E")
        for ex, ey in enemy_spawns:
            self.enemies.add(Enemy(ex, ey, self.level))

        self.items.empty() 
        # Directly placed coins
        coin_spawns = self._find_spawn_points("C")
        for cx, cy in coin_spawns:
            coin = Item(cx * TILE_SIZE, cy*TILE_SIZE, "coin", self.level)
            coin.vel_y = 0 
            coin.lifetime = float('inf') 
            self.items.add(coin)
            if 0 <= cy < self.level.rows and 0 <= cx < self.level.cols:
                 self.level.tilemap[cy][cx] = '.' 
        
        # Directly placed mushrooms (for testing)
        mushroom_spawns = self._find_spawn_points("M")
        for mx, my in mushroom_spawns:
            mushroom = Item(mx * TILE_SIZE, my*TILE_SIZE, "mushroom", self.level)
            self.items.add(mushroom)
            if 0 <= my < self.level.rows and 0 <= mx < self.level.cols:
                self.level.tilemap[my][mx] = '.'

        self.cam_x = 0
        if self.player: self.player.on_goal = False
        self.game_state = PLAYING
        return True


    def _handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == PLAYING:
                        self.game_state = OVERWORLD # Go back to overworld from game
                    else:
                        self.running = False
                
                if self.game_state == START_MENU:
                    if event.key == pygame.K_RETURN:
                        self.game_state = OVERWORLD 
                        self.reset_game_stats() # Reset score/lives for a new game start
                elif self.game_state == OVERWORLD:
                    self._handle_input_overworld(event)
                elif self.game_state == GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game_stats() 
                        self.game_state = OVERWORLD # Restart from overworld
                    elif event.key == pygame.K_RETURN:
                        self.reset_game_stats()
                        self.game_state = START_MENU # Back to title
                elif self.game_state == LEVEL_CLEAR:
                     if event.key == pygame.K_RETURN:
                        self.game_state = OVERWORLD # Back to overworld to select next
                elif self.game_state == GAME_WON:
                    if event.key == pygame.K_RETURN:
                        self.reset_game_stats()
                        self.game_state = START_MENU

        if self.game_state == PLAYING and self.player:
            keys = pygame.key.get_pressed()
            self.player.update(keys, self)

    def _handle_input_overworld(self, event):
        """Handles input for the overworld map."""
        current_node_data = overworld_nodes.get(self.overworld_cursor_node_key)
        if not current_node_data: return # Should not happen

        # For simplicity, allow cycling through all defined nodes with left/right
        # A more complex system would use the "connections"
        node_keys = list(overworld_nodes.keys()) # Get an ordered list of node keys
        current_index = -1
        try:
            current_index = node_keys.index(self.overworld_cursor_node_key)
        except ValueError: # Should not happen if cursor_node_key is always valid
            self.overworld_cursor_node_key = node_keys[0] if node_keys else (1,1)
            current_index = 0


        if event.key == pygame.K_RIGHT:
            next_index = (current_index + 1) % len(node_keys)
            # Only move to next if it's unlocked
            if node_keys[next_index] in self.unlocked_levels:
                self.overworld_cursor_node_key = node_keys[next_index]
                self.play_sound("overworld_move")
        elif event.key == pygame.K_LEFT:
            prev_index = (current_index - 1 + len(node_keys)) % len(node_keys)
             # Only move to prev if it's unlocked
            if node_keys[prev_index] in self.unlocked_levels:
                self.overworld_cursor_node_key = node_keys[prev_index]
                self.play_sound("overworld_move")
        elif event.key == pygame.K_RETURN:
            if self.overworld_cursor_node_key in self.unlocked_levels:
                world_to_load, level_to_load = self.overworld_cursor_node_key
                if self._load_level_data(world_to_load, level_to_load):
                    self.play_sound("overworld_select")
                # game_state is set to PLAYING by _load_level_data on success


    def _update(self):
        if self.game_state != PLAYING or not self.player or not self.level:
            return

        # self.player.update is called in _handle_input based on keys
        self.enemies.update()
        self.items.update()

        # Player-Enemy collisions
        if self.player.invincible_timer == 0:
            # Pass self.enemies (the group) to spritecollideany
            enemy_collided = pygame.sprite.spritecollideany(self.player, self.enemies)
            if enemy_collided:
                stomp_threshold = self.player.vel_y + GRAVITY + 5 
                is_stomp = (self.player.vel_y > 0 and 
                            self.player.rect.bottom < enemy_collided.rect.centery + TILE_SIZE * 0.5 and # Allow slightly deeper stomp
                            abs(self.player.rect.bottom - enemy_collided.rect.top) < stomp_threshold)

                if is_stomp:
                    enemy_collided.kill() 
                    self.player.score += 100
                    self.player.vel_y = PLAYER_JUMP_VELOCITY * 0.6 # Bounce
                    self.play_sound("stomp")
                else:
                    self.player.take_damage(self) 

        # Player-Item collisions
        # Pass self.items (the group) to spritecollide
        items_collected_list = pygame.sprite.spritecollide(self.player, self.items, True) # True to dokill
        for item_collected in items_collected_list:
            self.player.collect_item(item_collected, self)
            # Item is already removed from self.items group by spritecollide

        # Remove enemies that fell off map (already handled in Enemy.update with self.kill())
        
        # Camera update
        target_cam_x = self.player.rect.centerx - WIDTH // 2
        self.cam_x = max(0, min(target_cam_x, self.level.width - WIDTH))
        if self.level.width <= WIDTH: self.cam_x = 0

        if self.player.on_goal:
            self.game_state = LEVEL_CLEAR
            self.play_sound("level_clear_sound")
            self.cleared_levels.add((self.current_world_idx, self.current_level_idx))
            
            # Unlock next level
            current_node_data = overworld_nodes.get((self.current_world_idx, self.current_level_idx))
            if current_node_data and current_node_data["next"]:
                next_level_key = current_node_data["next"]
                self.unlocked_levels.add(next_level_key)
                # Check if all levels are cleared for GAME_WON
                if len(self.cleared_levels) == len(overworld_nodes):
                    # Check if the "next" of the last cleared level is None (or points to a non-existent one)
                    is_last_level_in_demo = True # Assume true initially
                    for node_key, node_info in overworld_nodes.items():
                        if node_info["next"] is not None and node_info["next"] in overworld_nodes:
                            if node_info["next"] not in self.cleared_levels:
                                is_last_level_in_demo = False # Found a defined next level that isn't cleared
                                break
                    if is_last_level_in_demo and current_node_data["next"] is None: # Explicitly the end
                         self.game_state = GAME_WON

            elif not current_node_data or not current_node_data["next"]: # No next level defined, this is the end
                 self.game_state = GAME_WON


    def _draw_hud(self):
        if not self.player: return
        self.font_manager.render(self.screen, f"Score: {self.player.score}", (10, 10), WHITE)
        self.font_manager.render(self.screen, f"Lives: {self.player.lives}", (WIDTH - 150, 10), WHITE)
        self.font_manager.render(self.screen, f"World: {self.current_world_idx}-{self.current_level_idx}", (WIDTH // 2 - 70, 10), WHITE, center=False)

    def _draw_overworld(self):
        """Draws the overworld map screen."""
        self.screen.fill(GRASS_GREEN) # A green background for the map
        self.font_manager.render(self.screen, "Select Level", (WIDTH // 2, 50), WHITE, "medium", center=True)
        
        # Draw paths (simple lines between connected nodes for now)
        # This could be more sophisticated with actual path graphics
        for node_key, node_data in overworld_nodes.items():
            if node_data["next"] and node_data["next"] in overworld_nodes:
                start_pos = node_data["pos"]
                end_pos = overworld_nodes[node_data["next"]]["pos"]
                # Draw path only if both current and next are unlocked
                if node_key in self.unlocked_levels and node_data["next"] in self.unlocked_levels:
                     pygame.draw.line(self.screen, PATH_YELLOW, start_pos, end_pos, 5)

        # Draw level nodes
        for node_key, node_data in overworld_nodes.items():
            pos = node_data["pos"]
            name = node_data["name"]
            node_radius = 20
            
            color = LEVEL_NODE_COLOR
            if node_key not in self.unlocked_levels:
                color = (100,100,100) # Grey out locked levels
            elif node_key in self.cleared_levels:
                color = LEVEL_NODE_CLEARED_COLOR
            
            if node_key == self.overworld_cursor_node_key and node_key in self.unlocked_levels:
                pygame.draw.circle(self.screen, LEVEL_NODE_HIGHLIGHT_COLOR, pos, node_radius + 5) # Highlight

            pygame.draw.circle(self.screen, color, pos, node_radius)
            self.font_manager.render(self.screen, name, (pos[0], pos[1] + node_radius + 5), WHITE, "small", center=True)

        self.font_manager.render(self.screen, "Use Arrow Keys to Move, ENTER to Select", (WIDTH // 2, HEIGHT - 50), WHITE, "small", center=True)
        self.font_manager.render(self.screen, "ESC to Title (from game) or Quit", (WIDTH // 2, HEIGHT - 25), WHITE, "small", center=True)


    def _draw(self):
        self.screen.fill(SKY_BLUE) 

        if self.game_state == START_MENU:
            self.font_manager.render(self.screen, "Super Platformer Engine", (WIDTH // 2, HEIGHT // 3), GOLD, "large", center=True)
            self.font_manager.render(self.screen, "Press ENTER to Start", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
        
        elif self.game_state == OVERWORLD:
            self._draw_overworld()

        elif self.game_state == PLAYING:
            if self.level and self.player:
                self.level.draw(self.screen, self.cam_x)
                # Items and enemies are sprite groups, they handle their own draw if added to a group
                # But they need cam_x passed to their draw method.
                for item in self.items: item.draw(self.screen, self.cam_x)
                for enemy in self.enemies: enemy.draw(self.screen, self.cam_x)
                self.player.draw(self.screen, self.cam_x) # Player draw handles invincibility blink
                self._draw_hud()

        elif self.game_state == LEVEL_CLEAR:
            self.font_manager.render(self.screen, "Level Clear!", (WIDTH // 2, HEIGHT // 3), GREEN, "large", center=True)
            if self.player:
                self.font_manager.render(self.screen, f"Score: {self.player.score}", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
            self.font_manager.render(self.screen, "Press ENTER for Overworld", (WIDTH // 2, HEIGHT // 2 + 50), WHITE, "small", center=True)

        elif self.game_state == GAME_OVER:
            self.font_manager.render(self.screen, "GAME OVER", (WIDTH // 2, HEIGHT // 3), RED, "large", center=True)
            if self.player:
                 self.font_manager.render(self.screen, f"Final Score: {self.player.score}", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
            self.font_manager.render(self.screen, "R for Overworld | ENTER for Title", (WIDTH // 2, HEIGHT // 2 + 50), WHITE, "small", center=True)
        
        elif self.game_state == GAME_WON:
            self.font_manager.render(self.screen, "YOU WON THE DEMO!", (WIDTH // 2, HEIGHT // 3), GOLD, "large", center=True)
            if self.player:
                self.font_manager.render(self.screen, f"Final Score: {self.player.score}", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
            self.font_manager.render(self.screen, "Press ENTER for Title Screen", (WIDTH // 2, HEIGHT // 2 + 50), WHITE, "small", center=True)

        pygame.display.flip()

    def reset_game_stats(self):
        """Resets player score and lives, typically for a new game from start menu."""
        if self.player: # If player object exists
            self.player.lives = 3
            self.player.score = 0
        else: # If player is None (e.g. first time starting)
            # Player will be created with default lives/score when _load_level_data is called
            pass 
        
        # Reset progression for a completely new game
        self.unlocked_levels = set([(1,1)]) 
        self.cleared_levels = set()
        self.overworld_cursor_node_key = (1,1)
        self.current_world_idx = 1
        self.current_level_idx = 1


    def run(self):
        while self.running:
            self._handle_input()
            self._update() 
            self._draw()
            self.clock.tick(FPS)
        
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()
