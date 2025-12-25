import os
import pygame


class Animation:
    """
    Tiny helper: loops through a list of surfaces at a fixed fps.
    """
    def __init__(self, frames, fps=8, loop=True):
        self.frames = frames
        self.loop = loop
        self.fps = fps
        self.index = 0
        self.time = 0.0
        self.frame_time = 1.0 / max(1, fps)
        self.done = False

    def reset(self):
        self.index = 0
        self.time = 0.0
        self.done = False

    def update(self, dt):
        if self.done or len(self.frames) == 0:
            return

        self.time += dt
        while self.time >= self.frame_time:
            self.time -= self.frame_time
            self.index += 1

            if self.index >= len(self.frames):
                if self.loop:
                    self.index = 0
                else:
                    self.index = len(self.frames) - 1
                    self.done = True

    def image(self):
        if len(self.frames) == 0:
            return None
        return self.frames[self.index]


def load_png(path):
    # Use convert_alpha for sprites with transparency
    return pygame.image.load(path).convert_alpha()


class BigBoy:
    """
    BigBoy = simple fighter controller:
      - Idle
      - Walk (2 frames)
      - Belly bump attack (requires 2 steps forward first)
    """
    IDLE = "idle"
    WALK = "walk"
    PRE_BUMP = "pre_bump"
    BUMP = "bump"
    RECOVER = "recover"

    def __init__(self, sprite_dir, pos=(200, 380), ground_y=420):
        self.sprite_dir = sprite_dir
        self.ground_y = ground_y

        # --- load frames ---
        self.frames_idle = [load_png(os.path.join(sprite_dir, "Idle.png"))]
        self.frames_walk = [
            load_png(os.path.join(sprite_dir, "Walk1.png")),
            load_png(os.path.join(sprite_dir, "Walk2.png")),
        ]
        self.frames_pre = [load_png(os.path.join(sprite_dir, "PreBellyBump.png"))]
        self.frames_bump = [load_png(os.path.join(sprite_dir, "BellyBumpV3.png"))]

        # --- animations ---
        self.anim_idle = Animation(self.frames_idle, fps=1, loop=True)
        self.anim_walk = Animation(self.frames_walk, fps=6, loop=True)
        self.anim_pre  = Animation(self.frames_pre, fps=10, loop=False)
        self.anim_bump = Animation(self.frames_bump, fps=10, loop=False)

        self.state = self.IDLE
        self.facing = -1  # 1 = right, -1 = left

        # Physics-ish
        self.speed = 220  # px/sec
        self.bump_speed = 520  # px/sec during belly bump lunge
        self.vel_x = 0

        # Step gating for belly bump:
        # require “2 steps forward” (we count walk-frame changes while moving forward)
        self.steps_forward = 0
        self._last_walk_frame = 0

        # Rects
        self.image = self.anim_idle.image()
        self.rect = self.image.get_rect(midbottom=pos)

        # Hurtbox slightly tighter than sprite (tweak later)
        self.hurtbox = self.rect.copy().inflate(-30, -10)

        # Belly hitbox appears only during BUMP
        self.belly_hitbox = pygame.Rect(0, 0, 1, 1)
        self.belly_active = False

        # Cooldowns
        self.recover_timer = 0.0

    def _set_state(self, new_state):
        if new_state == self.state:
            return
        self.state = new_state

        if new_state == self.IDLE:
            self.anim_idle.reset()
        elif new_state == self.WALK:
            self.anim_walk.reset()
            self._last_walk_frame = self.anim_walk.index
        elif new_state == self.PRE_BUMP:
            self.anim_pre.reset()
        elif new_state == self.BUMP:
            self.anim_bump.reset()
        elif new_state == self.RECOVER:
            self.recover_timer = 0.12  # tiny pause after bump

    def can_belly_bump(self):
        return self.steps_forward >= 2 and self.state in (self.IDLE, self.WALK)

    def start_belly_bump(self):
        if not self.can_belly_bump():
            return
        self._set_state(self.PRE_BUMP)

    def update(self, dt, keys, opponent_hurtbox=None, arena_rect=None):
        # --- input -> movement (only when not attacking) ---
        move = 0
        if self.state in (self.IDLE, self.WALK):
            if keys[pygame.K_a] or keys[pygame.K_LEFT]:
                move = -1
            elif keys[pygame.K_d] or keys[pygame.K_RIGHT]:
                move = 1

            # facing follows movement
            #if move != 0:
            #    self.facing = 1 if move > 0 else -1

        # belly bump trigger
        if self.state in (self.IDLE, self.WALK):
            if keys[pygame.K_SPACE]:
                self.start_belly_bump()

        # --- state machine ---
        self.vel_x = 0
        self.belly_active = False

        if self.state == self.IDLE:
            if move != 0:
                self._set_state(self.WALK)
            self.anim_idle.update(dt)
            self.image = self.anim_idle.image()

        elif self.state == self.WALK:
            if move == 0:
                self._set_state(self.IDLE)
            else:
                self.vel_x = move * self.speed

            self.anim_walk.update(dt)
            self.image = self.anim_walk.image()

            # count “steps forward” ONLY while moving in facing direction
            # (each time Walk frame changes -> +1, so 2 changes = "two steps")
            if move == self.facing and self.anim_walk.index != self._last_walk_frame:
                self.steps_forward += 1
                self._last_walk_frame = self.anim_walk.index

            # if they back up or stop, reset step gate
            if move == 0 or move != self.facing:
                self.steps_forward = 0
            #self.facing = 1 if move > 0 else -1

        elif self.state == self.PRE_BUMP:
            self.anim_pre.update(dt)
            self.image = self.anim_pre.image()

            # once pre anim finishes -> bump
            if self.anim_pre.done:
                self._set_state(self.BUMP)

        elif self.state == self.BUMP:
            self.anim_bump.update(dt)
            self.image = self.anim_bump.image()

            # lunge forward
            self.vel_x = self.facing * self.bump_speed

            # belly hitbox active during bump
            self.belly_active = True
            self._update_belly_hitbox()

            # collision with opponent -> (you can launch them here)
            if opponent_hurtbox is not None and self.belly_hitbox.colliderect(opponent_hurtbox):
                # placeholder: on hit, end bump quickly
                self.anim_bump.done = True

            if self.anim_bump.done:
                self.steps_forward = 0
                self._set_state(self.RECOVER)

        elif self.state == self.RECOVER:
            self.recover_timer -= dt
            if self.recover_timer <= 0:
                self._set_state(self.IDLE)
            self.image = self.anim_idle.image()

        # --- apply motion ---
        self.rect.x += int(self.vel_x * dt)

        # lock to ground
        self.rect.bottom = self.ground_y

        # clamp to arena (optional)
        if arena_rect is not None:
            self.rect.left = max(arena_rect.left, self.rect.left)
            self.rect.right = min(arena_rect.right, self.rect.right)

        # update hurtbox
        self.hurtbox = self.rect.copy().inflate(-30, -10)

    def _update_belly_hitbox(self):
        # Put a fat rectangle in front of BigBoy.
        # Tweak numbers until it feels right.
        w = int(self.rect.width * 0.65)
        h = int(self.rect.height * 0.45)
        y = self.rect.centery - h // 2

        if self.facing == 1:
            x = self.rect.centerx + int(self.rect.width * 0.15)
        else:
            x = self.rect.centerx - int(self.rect.width * 0.15) - w

        self.belly_hitbox = pygame.Rect(x, y, w, h)

    def draw(self, screen, debug=False):
        img = self.image
        if img is None:
            return

        # flip if facing left
        if self.facing == -1:
            img = pygame.transform.flip(img, True, False)

        # draw sprite
        screen.blit(img, self.rect.topleft)

        if debug:
            pygame.draw.rect(screen, (0, 255, 0), self.hurtbox, 2)
            if self.belly_active:
                pygame.draw.rect(screen, (255, 0, 0), self.belly_hitbox, 2)
