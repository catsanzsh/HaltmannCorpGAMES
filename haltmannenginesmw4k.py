import pygame
import sys

# --- Configuration ---
WIDTH, HEIGHT = 800, 600  # Increased screen size
FPS = 60
TILE_SIZE = 30
GRAVITY = 0.7
PLAYER_JUMP_VELOCITY = -15
PLAYER_SPEED = 5
ENEMY_SPEED = 1.5
MUSHROOM_SPEED = 2

# --- Palette ---
SKY_BLUE = (135, 206, 250)
BROWN = (139, 69, 19)      # Solid blocks
GOLD = (255, 215, 0)      # Question blocks
YELLOW = (255, 255, 0)    # Coins
RED = (220, 20, 60)       # Player
GREEN = (0, 128, 0)       # Enemies (Goombas)
BRIGHT_RED = (255, 0, 0)  # Mushrooms
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
LIGHT_BROWN = (205, 133, 63) # Hit Question Block / Empty Block
BRICK_COLOR = (170, 74, 68)  # Breakable bricks

# --- Game States ---
START_MENU = 0
PLAYING = 1
LEVEL_CLEAR = 2
GAME_OVER = 3
GAME_WON = 4

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
                "S         ???                          S",
                "S        SBBBS                         S",
                "S P     S.....S         C C C          S",
                "S       S.....S   B?B         E        S",
                "S      SS...SS   BB.BB               G S",
                "S     S.......S SSSSSSS    SSSS    SSSSS",
                "S    S.........S                     S S",
                "S   S...........S      E             S S",
                "S  S.............S SSSSSSSSSSSSSSSSSSS S",
                "S S...............S                   S S",
                "S SSSSSSSSSSSSSSSSS                   S S",
                "S                                     S S",
                "S              E                      S S",
                "S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
            ],
            2: [
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
                "S                                      S",
                "S  P         ?????                     S",
                "S SSSSS    SSSSSSSSS                   S",
                "S                                      S",
                "S      C C C                           S",
                "S     BBBBBBB                          S",
                "S    SSSSSSSSS                         S",
                "S                  E         E         S",
                "S SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS   S",
                "S                                      S",
                "S                                   G  S",
                "SSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSSS",
            ],
        },
    },
    2: {
        "name": "Donut Plains",
        "levels": {
            1: [ # A very short test level for world progression
                "SSSSSSSSSSSS",
                "S P      G S",
                "SSSSSSSSSSSS",
            ]
        }
    }
}

class FontManager:
    """Handles loading and rendering fonts."""
    def __init__(self):
        self.default_font_small = pygame.font.Font(None, 36)
        self.default_font_large = pygame.font.Font(None, 72)

    def render(self, surface, text, position, color, size="small", center=False):
        font = self.default_font_large if size == "large" else self.default_font_small
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
        self.cols = len(self.tilemap[0])
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
        return tile in ['S', 'Q', 'B'] # Solid, Hit Question, Brick (small player can't pass)

    def is_breakable_brick(self, grid_x: int, grid_y: int) -> bool:
        """Checks if a tile is a breakable brick."""
        return self.get_tile(grid_x, grid_y) == 'B'

    def hit_block(self, grid_x: int, grid_y: int, player_power_up: str, game_items_list: list):
        """Handles player hitting a block from below."""
        tile = self.get_tile(grid_x, grid_y)
        block_center_x = grid_x * TILE_SIZE + TILE_SIZE // 2
        spawn_y = (grid_y - 1) * TILE_SIZE # Item spawns above the block

        if tile == '?':
            self.tilemap[grid_y][grid_x] = 'Q' # Change to hit question block
            # Determine item to spawn
            if player_power_up == "small": # Prioritize mushroom if small
                item_type = "mushroom"
            else: # Otherwise, a coin
                item_type = "coin"
            
            # Spawn the item
            # Item position needs to be world coordinates
            new_item = Item(block_center_x - TILE_SIZE // 2, spawn_y, item_type, self)
            new_item.vel_y = -5 # Pop out effect
            game_items_list.append(new_item)
            return True # Block was hit and changed

        elif tile == 'B':
            if player_power_up == "big":
                self.tilemap[grid_y][grid_x] = '.' # Break the brick
                # TODO: Add particle effect or score for breaking bricks
                return True # Brick broken
            else:
                # Small player bonks head, no change to brick
                # TODO: Add bonk sound
                return False # Brick not broken, just bonked
        return False


    def draw(self, surface, cam_x):
        """Draws the visible part of the level."""
        start_col = cam_x // TILE_SIZE
        end_col = start_col + (WIDTH // TILE_SIZE) + 2 # Draw a bit extra for smooth scrolling

        for y, row_list in enumerate(self.tilemap):
            for x in range(max(0, start_col), min(self.cols, end_col)):
                cell = row_list[x]
                rect = pygame.Rect(x * TILE_SIZE - cam_x, y * TILE_SIZE, TILE_SIZE, TILE_SIZE)
                if cell == "S":
                    pygame.draw.rect(surface, BROWN, rect)
                elif cell == "?":
                    pygame.draw.rect(surface, GOLD, rect)
                elif cell == "Q":
                    pygame.draw.rect(surface, LIGHT_BROWN, rect)
                elif cell == "B":
                    pygame.draw.rect(surface, BRICK_COLOR, rect)
                elif cell == "C": # Directly placed coin
                    pygame.draw.circle(surface, YELLOW, rect.center, TILE_SIZE // 3)
                elif cell == "M": # Directly placed mushroom (for testing)
                     pygame.draw.rect(surface, BRIGHT_RED, rect.inflate(-TILE_SIZE//3, -TILE_SIZE//3))
                elif cell == "G":
                    pygame.draw.rect(surface, GREEN, rect) # Goal tile
                    pygame.draw.circle(surface, WHITE, rect.center, TILE_SIZE // 3)


class Entity(pygame.sprite.Sprite):
    """Base class for Player and Enemy."""
    def __init__(self, spawn_x: int, spawn_y: int, level: Level, color, width=TILE_SIZE, height=TILE_SIZE):
        super().__init__()
        self.rect = pygame.Rect(spawn_x * TILE_SIZE, spawn_y * TILE_SIZE, width, height)
        self.level = level
        self.vel_x = 0.0
        self.vel_y = 0.0
        self._on_ground = False
        self.color = color
        self.initial_spawn_x = spawn_x
        self.initial_spawn_y = spawn_y

    def _move_axis(self, dx: float, dy: float, game_items_list=None, player_power_up=None, game=None):
        """Move entity and resolve collisions along one axis at a time."""
        # Move X
        self.rect.x += dx
        self._resolve_collisions(axis="x")

        # Move Y
        self.rect.y += dy
        # Pass game_items_list and player_power_up for player hitting blocks
        if isinstance(self, Player):
             self._resolve_collisions(axis="y", game_items_list=game_items_list, player_power_up=player_power_up, game=game)
        else:
            self._resolve_collisions(axis="y")


    def _resolve_collisions(self, axis: str, game_items_list=None, player_power_up=None, game=None):
        """Resolves collisions with solid tiles after movement."""
        # Iterate over tiles the entity might be overlapping
        # Add a small margin for floating point inaccuracies if rect sizes are not multiples of TILE_SIZE
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
                            if self.vel_x > 0: # Moving right
                                self.rect.right = tile_rect.left
                            elif self.vel_x < 0: # Moving left
                                self.rect.left = tile_rect.right
                            if isinstance(self, Enemy): # Enemies turn on wall hit
                                self.vel_x *= -1
                            else:
                                self.vel_x = 0
                        elif axis == "y":
                            if self.vel_y > 0: # Moving down
                                self.rect.bottom = tile_rect.top
                                self._on_ground = True
                            elif self.vel_y < 0: # Moving up
                                self.rect.top = tile_rect.bottom
                                # Player specific: hit block from below
                                if isinstance(self, Player) and game_items_list is not None and player_power_up is not None and game is not None:
                                    if self.level.hit_block(gx, gy, player_power_up, game_items_list):
                                        game.play_sound("bonk_block") # Play sound if block was interactive
                                    else: # Bonked a solid non-interactive block or small player hit brick
                                        game.play_sound("bonk_solid")


                            self.vel_y = 0
    
    def respawn(self):
        self.rect.x = self.initial_spawn_x * TILE_SIZE
        self.rect.y = self.initial_spawn_y * TILE_SIZE
        self.vel_x = 0
        self.vel_y = 0
        self._on_ground = False
        if isinstance(self, Enemy): # Reset enemy direction
            self.vel_x = -ENEMY_SPEED


    def draw(self, surface, cam_x):
        """Draws the entity."""
        # Adjust rect for camera position
        # For player, adjust height based on power-up
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        pygame.draw.rect(surface, self.color, draw_rect)


class Player(Entity):
    """Represents the player character."""
    def __init__(self, spawn_x: int, spawn_y: int, level: Level):
        super().__init__(spawn_x, spawn_y, level, RED, TILE_SIZE, TILE_SIZE)
        self.power_up = "small"  # "small", "big"
        self.lives = 3
        self.score = 0
        self.invincible_timer = 0 # For invincibility after taking damage
        self.on_goal = False

    def update(self, keys, game): # Pass game for item spawning
        """Updates player state based on input and physics."""
        if self.invincible_timer > 0:
            self.invincible_timer -= 1

        # Horizontal movement
        self.vel_x = 0
        if keys[pygame.K_LEFT]:
            self.vel_x = -PLAYER_SPEED
        if keys[pygame.K_RIGHT]:
            self.vel_x = PLAYER_SPEED

        # Jumping
        if (keys[pygame.K_UP] or keys[pygame.K_SPACE]) and self._on_ground:
            self.vel_y = PLAYER_JUMP_VELOCITY
            self._on_ground = False # Prevent double jump in same frame
            game.play_sound("jump")


        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > TILE_SIZE: # Terminal velocity (max fall speed)
            self.vel_y = TILE_SIZE

        # Reset on_ground, it will be set by collision if true
        self._on_ground = False 
        
        # Move and resolve collisions
        # Pass game.items for block hitting logic to spawn items
        self._move_axis(self.vel_x, self.vel_y, game.items, self.power_up, game)

        # Check for falling out of map
        if self.rect.top > self.level.height + TILE_SIZE * 2 : # Give some leeway
             self.take_damage(game, fall_death=True)


        # Check for goal
        goal_gx_left = self.rect.left // TILE_SIZE
        goal_gx_right = self.rect.right // TILE_SIZE
        goal_gy_top = self.rect.top // TILE_SIZE
        goal_gy_bottom = self.rect.bottom // TILE_SIZE
        
        for gy in range(goal_gy_top, goal_gy_bottom + 1):
            for gx in range(goal_gx_left, goal_gx_right + 1):
                if self.level.get_tile(gx, gy) == 'G':
                    self.on_goal = True
                    break
            if self.on_goal:
                break


    def take_damage(self, game, fall_death=False): # Pass game for sfx and state change
        """Handles player taking damage."""
        if self.invincible_timer > 0 and not fall_death:
            return # Already invincible

        if self.power_up == "big":
            self.power_up = "small"
            self.rect.height = TILE_SIZE # Shrink
            self.rect.y += TILE_SIZE # Adjust y pos after shrinking
            self.invincible_timer = FPS * 2 # 2 seconds of invincibility
            game.play_sound("power_down")
        else:
            self.lives -= 1
            self.invincible_timer = FPS * 1 # Shorter invincibility on death animation/respawn
            if self.lives <= 0:
                game.game_state = GAME_OVER
                game.play_sound("game_over_player")
            else:
                # Respawn at level start (or checkpoint if implemented)
                self.respawn() # Entity base class handles respawn position
                # Player specific respawn logic:
                self.power_up = "small" 
                self.rect.height = TILE_SIZE
                game.play_sound("player_die")


    def collect_item(self, item, game): # Pass game for sfx
        """Handles collecting an item."""
        if item.type == "mushroom":
            if self.power_up == "small":
                self.power_up = "big"
                self.rect.height = TILE_SIZE * 2
                self.rect.y -= TILE_SIZE # Grow upwards
                game.play_sound("power_up")
            self.score += 1000 # Score for mushroom even if already big
        elif item.type == "coin":
            self.score += 200
            game.play_sound("coin")
        # Remove item from game list by having Game class handle it
        return True # Item collected

    def respawn(self):
        """Resets player state for respawn or new level."""
        super().respawn()
        self.power_up = "small"
        self.rect.width = TILE_SIZE
        self.rect.height = TILE_SIZE
        self.invincible_timer = 0
        self.on_goal = False


    def draw(self, surface, cam_x):
        """Draws the player, adjusting for power-up state and invincibility."""
        # Blinking effect when invincible
        if self.invincible_timer > 0:
            if (self.invincible_timer // (FPS // 10)) % 2 == 0: # Blink every few frames
                return # Skip drawing to make it blink

        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        
        current_color = RED
        if self.power_up == "big":
            # You could use a slightly different color for big Mario, or just rely on size
            # For now, keep color same, size is the indicator
            pass
        
        pygame.draw.rect(surface, current_color, draw_rect)

class Enemy(Entity):
    """Represents an enemy character."""
    def __init__(self, spawn_x: int, spawn_y: int, level: Level):
        super().__init__(spawn_x, spawn_y, level, GREEN)
        self.vel_x = -ENEMY_SPEED # Start moving left

    def update(self):
        """Updates enemy state and movement."""
        # Apply gravity
        self.vel_y += GRAVITY
        if self.vel_y > TILE_SIZE:
            self.vel_y = TILE_SIZE
        
        self._on_ground = False # Will be set by collision if true

        # Ledge and wall detection before moving
        if self._on_ground: # Only check for turns if on ground
            # Determine the grid cell for the ground just beyond the enemy's current facing edge
            # And the grid cell for a potential wall in front
            next_step_gx = -1
            wall_check_gx = -1

            if self.vel_x < 0:  # Moving left
                next_step_gx = (self.rect.left - 1) // TILE_SIZE 
                wall_check_gx = (self.rect.left -1) // TILE_SIZE
            elif self.vel_x > 0:  # Moving right
                next_step_gx = self.rect.right // TILE_SIZE
                wall_check_gx = self.rect.right // TILE_SIZE
            
            if next_step_gx != -1:
                # Y-coordinate of the ground tile the enemy is (or should be) standing on
                ground_level_gy = (self.rect.bottom -1) // TILE_SIZE
                
                # Check for wall at enemy's mid-height
                enemy_mid_gy = self.rect.centery // TILE_SIZE

                if self.level.is_solid(wall_check_gx, enemy_mid_gy): # Wall in front
                    pass # Collision resolution will handle turning
                elif not self.level.is_solid(next_step_gx, ground_level_gy): # Ledge in front
                    self.vel_x *= -1


        # Move and resolve collisions
        self._move_axis(self.vel_x, self.vel_y)

        # If enemy falls out of map (optional: remove it)
        if self.rect.top > self.level.height + TILE_SIZE * 2:
            # This enemy should be removed from the game's enemy list
            # For now, let it fall. Game class can handle removal.
            pass


class Item(pygame.sprite.Sprite):
    """Represents collectible items like mushrooms and coins."""
    def __init__(self, x: int, y: int, item_type: str, level: Level):
        super().__init__()
        self.type = item_type
        self.level = level
        self.vel_x = 0
        self.vel_y = 0
        self._on_ground = False

        if self.type == "mushroom":
            self.rect = pygame.Rect(x, y, TILE_SIZE, TILE_SIZE)
            self.color = BRIGHT_RED
            self.vel_x = MUSHROOM_SPEED # Mushrooms move
        elif self.type == "coin":
            self.rect = pygame.Rect(x, y, TILE_SIZE // 2, TILE_SIZE // 2)
            self.rect.centerx = x + TILE_SIZE // 2 # Center coin on its spawn tile
            self.rect.centery = y + TILE_SIZE // 2
            self.color = YELLOW
            self.lifetime = FPS * 0.5 # Coins might disappear quickly after appearing
        
        self.initial_y = y # For coin pop animation

    def update(self):
        """Updates item state (movement for mushrooms, lifetime for coins)."""
        if self.type == "mushroom":
            self.vel_y += GRAVITY
            if self.vel_y > TILE_SIZE:
                self.vel_y = TILE_SIZE
            
            self._on_ground = False
            
            # Mushroom X movement and collision
            self.rect.x += self.vel_x
            # Simplified X collision for mushroom (just turn on solid)
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
                            self.vel_x *= -1 # Turn around
                            break
                if self.vel_x == 0 and self.type == "mushroom": # If somehow stuck, try to unstick
                    self.vel_x = MUSHROOM_SPEED if pygame.time.get_ticks() % 2 == 0 else -MUSHROOM_SPEED


            # Mushroom Y movement and collision
            self.rect.y += self.vel_y
            # Recalculate tile checks for Y
            left_tile = self.rect.left // TILE_SIZE
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
            
            if self.rect.top > self.level.height + TILE_SIZE * 5: # Remove if falls way off
                self.kill() # Pygame sprite group removal

        elif self.type == "coin":
            # Coin might have a short upward pop animation then static or disappear
            if self.vel_y != 0 : # Initial pop
                self.rect.y += self.vel_y
                self.vel_y += GRAVITY * 0.5 # Slower gravity for pop
                if self.rect.y > self.initial_y : # Stop popping below original spawn
                    self.rect.y = self.initial_y
                    self.vel_y = 0

            if self.vel_y == 0: # After pop or if no pop
                self.lifetime -=1
                if self.lifetime <=0:
                    self.kill() # Remove from sprite groups

    def draw(self, surface, cam_x):
        draw_rect = self.rect.copy()
        draw_rect.x -= cam_x
        if self.type == "mushroom":
            pygame.draw.rect(surface, self.color, draw_rect)
            # Simple eyes for mushroom
            eye_radius = TILE_SIZE // 8
            pygame.draw.circle(surface, WHITE, (draw_rect.centerx - TILE_SIZE//4, draw_rect.centery - TILE_SIZE//5), eye_radius)
            pygame.draw.circle(surface, WHITE, (draw_rect.centerx + TILE_SIZE//4, draw_rect.centery - TILE_SIZE//5), eye_radius)
            pygame.draw.circle(surface, BLACK, (draw_rect.centerx - TILE_SIZE//4, draw_rect.centery - TILE_SIZE//5), eye_radius//2)
            pygame.draw.circle(surface, BLACK, (draw_rect.centerx + TILE_SIZE//4, draw_rect.centery - TILE_SIZE//5), eye_radius//2)
        elif self.type == "coin":
            pygame.draw.circle(surface, self.color, draw_rect.center, TILE_SIZE // 3)
            pygame.draw.circle(surface, GOLD, draw_rect.center, TILE_SIZE // 4, width=2) # Outline


class Game:
    """Main game class orchestrating everything."""
    def __init__(self):
        pygame.init()
        pygame.mixer.init(frequency=22050, size=-16, channels=2, buffer=512) # For sounds
        pygame.display.set_caption("Super Platformer Engine")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()
        self.font_manager = FontManager()
        self.running = True
        self.game_state = START_MENU

        self.current_world_idx = 1
        self.current_level_idx = 1
        
        self.level = None
        self.player = None
        self.enemies = pygame.sprite.Group() # Use sprite group for enemies
        self.items = pygame.sprite.Group()   # And for items

        self.cam_x = 0
        self._load_sounds()

    def _load_sounds(self):
        """Loads sound effects. Since no external files, we'd ideally generate tones.
           For now, this is a placeholder. Pygame.mixer.Sound can take a buffer.
           Actual sound generation is complex, so we'll just have silent stubs."""
        self.sounds = {
            "jump": None, "coin": None, "power_up": None, "power_down": None,
            "stomp": None, "bonk_block": None, "bonk_solid": None,
            "player_die": None, "game_over_player": None, "level_clear_sound": None
        }
        # Example of how a simple sound could be made (requires numpy typically for easy array manipulation)
        # arr = pygame.sndarray.make_sound(...)
        # self.sounds["jump"] = pygame.sndarray.make_sound(arr)
        # For now, sound calls will be silent.

    def play_sound(self, sound_name):
        if self.sounds.get(sound_name):
            self.sounds[sound_name].play()
        # else:
        #     print(f"Debug: Sound '{sound_name}' not found or not loaded.")


    def _find_spawn_points(self, char_to_find: str) -> list[tuple[int, int]]:
        """Finds all spawn points for a given character in the current level's tilemap."""
        spawns = []
        if not self.level: return spawns
        for y, row in enumerate(self.level.tilemap):
            for x, cell in enumerate(row):
                if cell == char_to_find:
                    spawns.append((x, y))
        return spawns

    def _load_level_data(self):
        """Loads the tilemap and initializes player, enemies, and items for the current level."""
        try:
            tilemap_str_list = worlds[self.current_world_idx]["levels"][self.current_level_idx]
        except KeyError:
            # Level or world not found, could mean game won or error
            if self.current_world_idx > max(worlds.keys()) or \
               (self.current_world_idx in worlds and self.current_level_idx > max(worlds[self.current_world_idx]["levels"].keys())):
                self.game_state = GAME_WON
            else: # Should not happen if worlds dict is correct
                print(f"Error: Level {self.current_world_idx}-{self.current_level_idx} not found!")
                self.running = False # Critical error
            return False

        self.level = Level(tilemap_str_list)
        
        # Player setup
        player_spawns = self._find_spawn_points("P")
        if not player_spawns: 
            player_spawn_x, player_spawn_y = 1, self.level.rows - 2 # Default if no P
        else:
            player_spawn_x, player_spawn_y = player_spawns[0]

        if self.player is None: # First time loading a player
            self.player = Player(player_spawn_x, player_spawn_y, self.level)
        else: # Subsequent levels, maintain score/lives
            self.player.level = self.level
            self.player.initial_spawn_x = player_spawn_x
            self.player.initial_spawn_y = player_spawn_y
            self.player.respawn() # Reset position, powerup for new level start

        # Enemy setup
        self.enemies.empty() # Clear previous enemies
        enemy_spawns = self._find_spawn_points("E")
        for ex, ey in enemy_spawns:
            self.enemies.add(Enemy(ex, ey, self.level))

        # Item setup (directly placed items like 'C' or 'M')
        self.items.empty() # Clear previous items
        coin_spawns = self._find_spawn_points("C")
        for cx, cy in coin_spawns:
            # Make these static coins, not animated like from blocks
            coin = Item(cx * TILE_SIZE, cy*TILE_SIZE, "coin", self.level)
            coin.vel_y = 0 # No pop
            coin.lifetime = float('inf') # Persist until collected
            self.items.add(coin)
            self.level.tilemap[cy][cx] = '.' # Remove 'C' from map once item is created
        
        mushroom_spawns = self._find_spawn_points("M") # For testing direct mushrooms
        for mx, my in mushroom_spawns:
            mushroom = Item(mx * TILE_SIZE, my*TILE_SIZE, "mushroom", self.level)
            self.items.add(mushroom)
            self.level.tilemap[my][mx] = '.'

        self.cam_x = 0
        self.player.on_goal = False # Reset goal flag
        return True


    def _handle_input(self):
        """Handles global input and game state specific input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.running = False
                
                if self.game_state == START_MENU:
                    if event.key == pygame.K_RETURN:
                        self.game_state = PLAYING
                        self._load_level_data() # Load first level
                elif self.game_state == GAME_OVER:
                    if event.key == pygame.K_r:
                        self.reset_game() # Reset score, lives, back to level 1-1
                        self.game_state = PLAYING
                        self._load_level_data()
                elif self.game_state == LEVEL_CLEAR or self.game_state == GAME_WON:
                     if event.key == pygame.K_RETURN:
                        if self.game_state == GAME_WON:
                            self.reset_game() # Restart from beginning
                            self.game_state = START_MENU
                        else: # LEVEL_CLEAR
                            self.current_level_idx += 1
                            # Check if this world has more levels
                            if self.current_level_idx not in worlds[self.current_world_idx]["levels"]:
                                self.current_level_idx = 1
                                self.current_world_idx +=1
                                # Check if next world exists
                                if self.current_world_idx not in worlds:
                                    self.game_state = GAME_WON
                                    self.play_sound("level_clear_sound") # Or game won sound
                                    return # Don't load new level yet, show GAME_WON screen

                            if self.game_state != GAME_WON: # If not game won, load next level
                                self.game_state = PLAYING
                                if not self._load_level_data():
                                     # This case handles if _load_level_data itself sets GAME_WON
                                     if self.game_state != GAME_WON: # Should not happen
                                        print("Failed to load next level, but not game won state.")
                                        self.running = False # Critical error
                                else:
                                    self.play_sound("level_clear_sound") # Sound for starting next level

        if self.game_state == PLAYING and self.player:
            keys = pygame.key.get_pressed()
            self.player.update(keys, self)


    def _update(self):
        """Updates game logic based on the current state."""
        if self.game_state != PLAYING or not self.player or not self.level:
            return

        # Update enemies
        self.enemies.update()
        # Update items
        self.items.update()

        # Player-Enemy collisions
        if self.player.invincible_timer == 0: # Only check if not invincible
            enemy_collided = pygame.sprite.spritecollideany(self.player, self.enemies)
            if enemy_collided:
                # Check if player stomped on enemy
                # Player's bottom must be close to enemy's top, and player moving down
                stomp_threshold = self.player.vel_y + GRAVITY + 5 # How close bottom of player needs to be to top of enemy
                
                # More precise stomp: player's feet were above enemy head last frame, now colliding from top.
                # Simpler: player moving down, bottom of player near top of enemy.
                is_stomp = (self.player.vel_y > 0 and 
                            self.player.rect.bottom < enemy_collided.rect.centery and # Player bottom is above enemy center
                            abs(self.player.rect.bottom - enemy_collided.rect.top) < stomp_threshold)


                if is_stomp:
                    enemy_collided.kill() # Remove stomped enemy
                    self.player.score += 100
                    self.player.vel_y = PLAYER_JUMP_VELOCITY * 0.6 # Bounce
                    self.play_sound("stomp")
                else:
                    self.player.take_damage(self) # Pass game for sfx

        # Player-Item collisions
        item_collected = pygame.sprite.spritecollideany(self.player, self.items)
        if item_collected:
            if self.player.collect_item(item_collected, self): # Pass game for sfx
                item_collected.kill() # Remove collected item

        # Remove enemies that fell off map
        for enemy in list(self.enemies): # Iterate over a copy
            if enemy.rect.top > self.level.height + TILE_SIZE * 5:
                enemy.kill()
        
        # Camera update
        # Target camera position: player center, but don't go out of level bounds
        target_cam_x = self.player.rect.centerx - WIDTH // 2
        self.cam_x = max(0, min(target_cam_x, self.level.width - WIDTH))
        if self.level.width <= WIDTH: # If level is smaller than screen, cam_x is 0
            self.cam_x = 0

        # Check for level completion
        if self.player.on_goal:
            self.game_state = LEVEL_CLEAR
            self.play_sound("level_clear_sound")


    def _draw_hud(self):
        """Draws Heads-Up Display (score, lives, etc.)."""
        if not self.player: return
        self.font_manager.render(self.screen, f"Score: {self.player.score}", (10, 10), WHITE)
        self.font_manager.render(self.screen, f"Lives: {self.player.lives}", (WIDTH - 150, 10), WHITE)
        self.font_manager.render(self.screen, f"World: {self.current_world_idx}-{self.current_level_idx}", (WIDTH // 2 - 50, 10), WHITE)
        # Debug player powerup state
        # self.font_manager.render(self.screen, f"Power: {self.player.power_up}", (10, 40), WHITE)
        # self.font_manager.render(self.screen, f"Inv: {self.player.invincible_timer}", (10, 70), WHITE)


    def _draw(self):
        """Draws everything based on the current game state."""
        self.screen.fill(SKY_BLUE) # Default background

        if self.game_state == START_MENU:
            self.font_manager.render(self.screen, "Super Platformer Engine", (WIDTH // 2, HEIGHT // 3), GOLD, "large", center=True)
            self.font_manager.render(self.screen, "Press ENTER to Start", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
        
        elif self.game_state == PLAYING:
            if self.level and self.player:
                self.level.draw(self.screen, self.cam_x)
                self.items.draw(self.screen) # Draw all items (they handle their own cam_x offset if needed)
                # Custom draw for items if they need cam_x
                for item in self.items:
                    item.draw(self.screen, self.cam_x)

                self.player.draw(self.screen, self.cam_x)
                for enemy in self.enemies: # Enemies draw themselves with cam_x
                    enemy.draw(self.screen, self.cam_x)
                self._draw_hud()

        elif self.game_state == LEVEL_CLEAR:
            self.font_manager.render(self.screen, "Level Clear!", (WIDTH // 2, HEIGHT // 3), GREEN, "large", center=True)
            if self.player:
                self.font_manager.render(self.screen, f"Score: {self.player.score}", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
            self.font_manager.render(self.screen, "Press ENTER to Continue", (WIDTH // 2, HEIGHT // 2 + 50), WHITE, "small", center=True)

        elif self.game_state == GAME_OVER:
            self.font_manager.render(self.screen, "GAME OVER", (WIDTH // 2, HEIGHT // 3), RED, "large", center=True)
            if self.player:
                 self.font_manager.render(self.screen, f"Final Score: {self.player.score}", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
            self.font_manager.render(self.screen, "Press R to Restart", (WIDTH // 2, HEIGHT // 2 + 50), WHITE, "small", center=True)
        
        elif self.game_state == GAME_WON:
            self.font_manager.render(self.screen, "YOU WON!", (WIDTH // 2, HEIGHT // 3), GOLD, "large", center=True)
            if self.player:
                self.font_manager.render(self.screen, f"Final Score: {self.player.score}", (WIDTH // 2, HEIGHT // 2), WHITE, "small", center=True)
            self.font_manager.render(self.screen, "Press ENTER to Play Again", (WIDTH // 2, HEIGHT // 2 + 50), WHITE, "small", center=True)


        pygame.display.flip()

    def reset_game(self):
        """Resets game to initial state for a new game."""
        self.current_world_idx = 1
        self.current_level_idx = 1
        if self.player: # Reset existing player's stats
            self.player.lives = 3
            self.player.score = 0
        # Player object itself will be re-initialized or reset by _load_level_data
        self.enemies.empty()
        self.items.empty()
        self.cam_x = 0


    def run(self):
        """Main game loop."""
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
