import asyncio
import os
import platform
import sys
from pathlib import Path

import pygame
from pygame.locals import (
    K_LEFT,
    K_RIGHT,
    K_UP,
    K_SPACE,
    K_ESCAPE,
    QUIT,
)

"""A tiny Super Mario World‑style demo written in Python/Pygame.

Controls
--------
← / →    Walk
↑ or ␣   Jump
Esc      Quit
"""

# -------------------------------------------------------------
# Configuration
# -------------------------------------------------------------
WIDTH, HEIGHT = 640, 480          # Window size (pixels)
FPS = 60                          # Frames per second
TILE_SIZE = 30                    # Size of a tile (pixels)
GRAVITY = 0.6                     # Downward acceleration (px / frame²)
JUMP_VELOCITY = -12               # Up‑ward impulse (px / frame)
PLAYER_SPEED = 4                  # Horizontal speed (px / frame)

# Palette
SKY_BLUE = (135, 206, 235)
BROWN = (139, 69, 19)
GOLD = (218, 165, 32)
RED = (255, 0, 0)

# -------------------------------------------------------------
# World → Level → Tilemap definitions
# -------------------------------------------------------------
worlds = {
    1: {
        "name": "Yoshi's Island",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S..................S",
                "S......??..........S",
                "S.................PS",
                "SSSSSSSSSSSSSSSSSSSS",
            ],
            2: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S....??............S",
                "S........P.........S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ],
        },
    },
    2: {
        "name": "Donut Plains",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S.........?........S",
                "S.....P............S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    3: {
        "name": "Vanilla Dome",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S..................S",
                "S....??.....P......S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    4: {
        "name": "Twin Bridges",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S......?...........S",
                "S.............P....S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    5: {
        "name": "Forest of Illusion",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S....??............S",
                "S........P.........S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    6: {
        "name": "Chocolate Island",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S.........??.......S",
                "S.....P............S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    7: {
        "name": "Valley of Bowser",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S..................S",
                "S....??.....P......S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    8: {
        "name": "Special World",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S.....??...........S",
                "S.............P....S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
    9: {
        "name": "Star World",
        "levels": {
            1: [
                "SSSSSSSSSSSSSSSSSSSS",
                "S....??............S",
                "S........P.........S",
                "S..................S",
                "SSSSSSSSSSSSSSSSSSSS",
            ]
        },
    },
}

# -------------------------------------------------------------
# Helper classes
# -------------------------------------------------------------
class Level:
    """Stores the tilemap for a single level and provides helpers."""

    def __init__(self, tilemap):
        self.tilemap = tilemap
        self.rows = len(tilemap)
        self.cols = len(tilemap[0])
        self.width = self.cols * TILE_SIZE
        self.height = self.rows * TILE_SIZE

        # Pre‑compute solid tiles for fast collision checks
        self._solids = {
            (x, y)
            for y, row in enumerate(tilemap)
            for x, cell in enumerate(row)
            if cell == "S"
        }

    # ---------------- public API ----------------
    def draw(self, surface):
        """Render the tilemap onto *surface*."""
        for y, row in enumerate(self.tilemap):
            for x, cell in enumerate(row):
                screen_rect = pygame.Rect(
                    x * TILE_SIZE, y * TILE_SIZE, TILE_SIZE, TILE_SIZE
                )
                if cell == "S":
                    pygame.draw.rect(surface, BROWN, screen_rect)
                elif cell == "?":
                    pygame.draw.rect(surface, GOLD, screen_rect)

    def solid_at(self, grid_x: int, grid_y: int) -> bool:
        """Return *True* if the tile at (grid_x, grid_y) is solid."""
        return (grid_x, grid_y) in self._solids


class Player:
    """Simple physics‑based player controller."""

    def __init__(self, spawn_x: int, spawn_y: int, level: Level):
        self.rect = pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE)
        self.rect.topleft = (spawn_x * TILE_SIZE, spawn_y * TILE_SIZE)
        self.level = level
        self.vel_x = 0.0
        self.vel_y = 0.0

    # ---------------- helpers ----------------
    def _move_axis(self, dx: float, dy: float):
        """Move by (dx,dy) with tile collisions."""
        # Horizontal first ---------------------------------------------------
        self.rect.x += dx
        self._resolve_collisions(axis="x")
        # Vertical second ----------------------------------------------------
        self.rect.y += dy
        self._resolve_collisions(axis="y")

    def _resolve_collisions(self, *, axis: str):
        """Slide player out of solids when intersecting."""
        # Determine tiles overlapped by the player's rect
        left = self.rect.left // TILE_SIZE
        right = (self.rect.right - 1) // TILE_SIZE
        top = self.rect.top // TILE_SIZE
        bottom = (self.rect.bottom - 1) // TILE_SIZE

        for gy in range(top, bottom + 1):
            for gx in range(left, right + 1):
                if self.level.solid_at(gx, gy):
                    tile_rect = pygame.Rect(
                        gx * TILE_SIZE, gy * TILE_SIZE, TILE_SIZE, TILE_SIZE
                    )
                    if self.rect.colliderect(tile_rect):
                        if axis == "x":
                            if self.vel_x > 0:
                                self.rect.right = tile_rect.left
                            elif self.vel_x < 0:
                                self.rect.left = tile_rect.right
                            self.vel_x = 0
                        else:  # axis == 'y'
                            if self.vel_y > 0:
                                self.rect.bottom = tile_rect.top
                                self._on_ground = True
                            elif self.vel_y < 0:
                                self.rect.top = tile_rect.bottom
                            self.vel_y = 0

    # ---------------- public API ----------------
    def update(self, keys):
        # Horizontal movement ----------------------------------------------
        self.vel_x = 0
        if keys[K_LEFT]:
            self.vel_x = -PLAYER_SPEED
        if keys[K_RIGHT]:
            self.vel_x = PLAYER_SPEED

        # Jump --------------------------------------------------------------
        if (keys[K_UP] or keys[K_SPACE]) and self.on_ground:
            self.vel_y = JUMP_VELOCITY

        # Gravity -----------------------------------------------------------
        self.vel_y += GRAVITY
        if self.vel_y > TILE_SIZE:  # Terminal fall speed clamp
            self.vel_y = TILE_SIZE

        # Reset grounded flag before move
        self._on_ground = False

        # Apply movement ----------------------------------------------------
        self._move_axis(self.vel_x, self.vel_y)

    # ---------------------------------------------------------------------
    @property
    def on_ground(self) -> bool:
        return getattr(self, "_on_ground", False)

    def draw(self, surface):
        pygame.draw.rect(surface, RED, self.rect)


# -------------------------------------------------------------
# Game wrapper
# -------------------------------------------------------------
class Game:
    def __init__(self):
        pygame.init()
        pygame.display.set_caption("Super Mario World – Python edition")
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        self.clock = pygame.time.Clock()

        self.current_world = 1
        self.current_level = 1
        self._load_level()

    # ---------------- helpers ----------------
    def _find_player_spawn(self):
        for y, row in enumerate(self.level.tilemap):
            for x, cell in enumerate(row):
                if cell == "P":
                    return x, y
        # Fallback if no explicit spawn tile
        return 1, 1

    def _load_level(self):
        tilemap = worlds[self.current_world]["levels"][self.current_level]
        self.level = Level(tilemap)
        spawn_x, spawn_y = self._find_player_spawn()
        self.player = Player(spawn_x, spawn_y, self.level)
        # Center the camera at start
        self.cam_x = 0

    # ---------------- game loop parts ----------------
    def _handle_events(self):
        for event in pygame.event.get():
            if event.type == QUIT or (
                event.type == pygame.KEYDOWN and event.key == K_ESCAPE
            ):
                pygame.quit()
                sys.exit()

    def _update(self):
        keys = pygame.key.get_pressed()
        self.player.update(keys)

        # When player reaches right edge, advance to next level / world
        if self.player.rect.left >= self.level.width:
            if self.current_level < len(worlds[self.current_world]["levels"]):
                self.current_level += 1
            else:
                # next world, loop around if finished all
                self.current_world = (
                    self.current_world % len(worlds)
                ) + 1
                self.current_level = 1
            self._load_level()

        # Simple camera that follows player horizontally
        self.cam_x = max(0, min(self.player.rect.centerx - WIDTH // 2, self.level.width - WIDTH))

    def _draw(self):
        # Sky background
        self.screen.fill(SKY_BLUE)
        # Translate level + player by camera offset
        cam_surface = pygame.Surface((self.level.width, self.level.height), pygame.SRCALPHA)
        self.level.draw(cam_surface)
        self.player.draw(cam_surface)
        self.screen.blit(cam_surface, (-self.cam_x, 0))
        pygame.display.flip()

    # ---------------- public API ----------------
    async def run(self):
        while True:
            self._handle_events()
            self._update()
            self._draw()
            self.clock.tick(FPS)
            await asyncio.sleep(0)  # yield control to event loop


# -------------------------------------------------------------
# Bootstrapping for native CPython & Emscripten / Pyodide
# -------------------------------------------------------------
async def main():
    game = Game()
    await game.run()


if platform.system() == "Emscripten":
    # Pyodide / Brython: schedule without blocking
    asyncio.ensure_future(main())
else:
    if __name__ == "__main__":
        try:
            asyncio.run(main())
        except KeyboardInterrupt:
            pygame.quit()
