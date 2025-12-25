import pygame




class DUMMY:
    def __init__(self, pos):
        self.w = 60
        self.h = 110
        self.rect = pygame.Rect(0, 0, self.w, self.h)
        self.rect.midbottom = pos

        self.vx = 0
        self.vy = 0
        self.gravity = 1.2

        self.stun_ms = 0
        self.hit_flash_ms = 0

    def launch(self, facing_right: bool):
        # ridiculous arcade launch
        self.vx = -18 if facing_right else 18
        self.vy = -14
        self.stun_ms = 400
        self.hit_flash_ms = 120

    def update(self, arena_rect, ground_y):
        now = pygame.time.get_ticks()

        if self.stun_ms > 0:
            # still move, but "stunned"
            # (you can also reduce control here if you later add AI)
            pass


        # physics
        self.vy += self.gravity
        self.rect.x += int(self.vx)
        self.rect.y += int(self.vy)

        # ground
        if self.rect.bottom >= ground_y:
            self.rect.bottom = ground_y
            self.vy = 0
            # friction
            self.vx = int(self.vx * 0.85)

        # walls (bounce)

        if self.rect.left < arena_rect.left:
            self.rect.left = arena_rect.left
            self.vx = int(-self.vx * 0.75)  # bounce back
            self.vy = -10                   # pop up (funny)
            self.hit_flash_ms = 320

        if self.rect.right > arena_rect.right:
            self.rect.right = arena_rect.right
            self.vx = int(-self.vx * 0.75)
            self.vy = -10
            self.hit_flash_ms = 320


        # timers
        if self.stun_ms > 0:
            self.stun_ms -= 16  # approx per frame; good enough for now
            if self.stun_ms < 0:
                self.stun_ms = 0

        if self.hit_flash_ms > 0:
            self.hit_flash_ms -= 16
            if self.hit_flash_ms < 0:
                self.hit_flash_ms = 0

    def draw(self, screen):
        # flash white briefly on impact
        color = (255, 255, 255) if self.hit_flash_ms > 0 else (200, 60, 60)
        pygame.draw.rect(screen, color, self.rect)







class PLAYER(pygame.sprite.Sprite):
    def __init__(self,pos):
        self.flip = False
        self.walking = False
        self.enemy_hit_registered = False

        self.animation_list = []
        self.frame_index = 0
        self.action = 0
        self.update_time = pygame.time.get_ticks()
        scale = 1

        temp_list = []
        # Idle Update Action #0
        for i in range (1):
            img = pygame.image.load(f'assets/sprites/bigboy/Idle.png').convert_alpha()
            img = pygame.transform.scale(img,(int(img.get_width() * scale),int(img.get_height()*scale)))
            temp_list.append(img)
        self.animation_list.append(temp_list)

        temp_list = []
        # Walk Update Action #1
        for i in range (2):
            img = pygame.image.load(f'assets/sprites/bigboy/walk/{i}.png').convert_alpha()
            img = pygame.transform.scale(img,(int(img.get_width() * scale),int(img.get_height()*scale)))
            temp_list.append(img)
        self.animation_list.append(temp_list)

        temp_list = []
        # PreBump Update Action #2
        for i in range (1):
            img = pygame.image.load(f'assets/sprites/bigboy/PreBellyBump.png').convert_alpha()
            img = pygame.transform.scale(img,(int(img.get_width() * scale),int(img.get_height()*scale)))
            temp_list.append(img)
        self.animation_list.append(temp_list)

        temp_list = []
        # The REASON we're all here Update Action #3
        for i in range (1):
            img = pygame.image.load(f'assets/sprites/bigboy/BellyBumpV3.png').convert_alpha()
            img = pygame.transform.scale(img,(int(img.get_width() * scale),int(img.get_height()*scale)))
            temp_list.append(img)
        self.animation_list.append(temp_list)

        self.image = self.animation_list[self.action][self.frame_index]
        self.rect = self.image.get_rect(topleft=(pos))
        self.old_rect = self.rect.copy()
        # --- two-step gate ---
        self.step_count = 0
        self.last_walk_frame = 0

        # --- belly bump sequencing ---
        self.bumping = False
        self.bump_phase = None
        self.pre_time = 180      # ms: how long to show PreBellyBump
        self.bump_time = 120     # ms: how long to show BellyBumpV3
        self.bump_start = 0

        # --- input edge detection (so holding SPACE doesn't spam) ---
        self.space_was_down = False

    def update_animation(self):
        ANIMATION_COOLDOWN = 150

        # keep image synced to frame
        self.image = self.animation_list[self.action][self.frame_index]

        # advance frame timer
        if pygame.time.get_ticks() - self.update_time > ANIMATION_COOLDOWN:
            self.update_time = pygame.time.get_ticks()
            self.frame_index += 1

            # --- step counting (only while walking action #1) ---
            if self.action == 1:
                # count every frame change as a "step event"
                if self.frame_index != self.last_walk_frame:
                    self.step_count += 1
                    self.last_walk_frame = self.frame_index

        # loop animation frames
        if self.frame_index >= len(self.animation_list[self.action]):
            self.frame_index = 0

        # --- drive belly bump phases (time-based, no extra frames needed) ---
        if self.bumping:
            now = pygame.time.get_ticks()
            elapsed = now - self.bump_start

            if self.bump_phase == "pre" and elapsed >= self.pre_time:
                self.bump_phase = "hit"
                self.bump_start = now
                self.update_action(3)  # BellyBumpV3

            elif self.bump_phase == "hit" and elapsed >= self.bump_time:
                # end attack
                self.bumping = False
                self.bump_phase = None
                self.step_count = 0
                self.update_action(0)  # back to idle

    def update_action(self,new_action):
        #check if action is different from previous
        if new_action != self.action:
            self.action = new_action
        #update animation settings
            self.frame_index = 0
            self.update_time = pygame.time.get_ticks()
    def action_handler(self):
        if self.bumping:
            return

        if self.walking:
            self.update_action(1)
        else:
            self.update_action(0)
    def input(self):
        self.walking = False
        self.dx = 0
        self.dy = 0
        key = pygame.key.get_pressed()
        if self.bumping:
            self.walking = False
            self.dx = 0
            self.dy = 0
            return
        if key[pygame.K_LEFT] or key[pygame.K_a]:
            self.walking = True
            #self.update_action(1)
            self.dx -= 5
            self.flip = False
        elif key[pygame.K_RIGHT] or key[pygame.K_d]:
            self.walking = True
            #self.update_action(1)
            self.dx += 5
            self.flip = True
        else:
            self.walking = False
        # SPACE edge-detect (pressed this frame)
        space_down = key[pygame.K_SPACE]
        space_pressed = space_down and not self.space_was_down
        self.space_was_down = space_down

        if (not self.bumping) and space_pressed and self.step_count >= 2:
            # start pre-bump -> smash
            self.enemy_hit_registered = False

            self.bumping = True
            self.bump_phase = "pre"
            self.bump_start = pygame.time.get_ticks()
            self.update_action(2)  # PreBellyBump
            self.walking = False
            self.dx = 0
            self.dy = 0
        if self.bumping and self.bump_phase == "hit":
            self.dx = -6 if self.flip else 6

        self.action_handler()
        self.rect.x += self.dx
        self.rect.y += self.dy

        # If you stopped walking, reset the step gate
        if not self.walking and not self.bumping:
            self.step_count = 0
            self.last_walk_frame = self.frame_index
            self.enemy_hit_registered = False

    def get_belly_hitbox(self):
        # Only active during hit phase
        if not self.bumping or self.bump_phase != "hit":
            return None

        # Make a big rectangle in front of the player
        w = int(self.rect.width * 0.25)
        h = int(self.rect.height * 0.45)
        y = self.rect.centery - h // 2

        facing_right = (self.flip == True)  # in your system: flip False = facing right

        if facing_right:
            x = self.rect.centerx + int(self.rect.width * 0.10)
        else:
            x = self.rect.centerx - int(self.rect.width * 0.10) - w

        return pygame.Rect(x, y, w, h)

    def update(self):
        self.input()
    def draw(self,screen):
        self.update_animation()
        if self.flip:
            screen.blit(pygame.transform.flip(self.image,self.flip,False),self.rect)
        else:
            screen.blit(self.image,self.rect)
