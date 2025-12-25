import pygame, sys
from assets.src.config import *
from assets.src.entities import BigBoy
from assets.src.classes import *

class GAME:
    def __init__(self):
        pygame.init()

        pygame.mixer.pre_init(44100, -16, 2, 128)
        pygame.mixer.init()

        # music (streamed)
        pygame.mixer.music.load("assets/audio/homedepot.mp3")
        pygame.mixer.music.set_volume(0.45)
        pygame.mixer.music.play(-1)   # -1 loops forever

        # hit sfx (small, loaded in memory)
        self.sfx_hit = pygame.mixer.Sound("assets/audio/hit.mp3")
        self.sfx_hit.set_volume(0.90)
        self.screen = pygame.display.set_mode(RES)
        self.clock = pygame.time.Clock()
        self.hit_pause =0
        self.shake = 0


        # arena bounds (simple stage walls)
        self.arena = pygame.Rect(40, 0, RES[0] - 80, RES[1])

        # BigBoy sprites live here:
        #self.bigboy = BigBoy(sprite_dir="assets/sprites", pos=(220, 420), ground_y=420)

        self.player = PLAYER((220, 300))
        self.arena = pygame.Rect(60, 0, RES[0] - 120, RES[1])
        self.ground_y = 420

        self.enemy = DUMMY((520, self.ground_y))

        self.debug = False

    def EventHandler(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_F1:
                self.debug = not self.debug

    def DisplayHandler(self):
        self.screen.fill(BG)

        # stage walls (visual)
        pygame.draw.rect(self.screen, (40, 40, 40), self.arena, 3)

        #self.bigboy.draw(self.screen, debug=self.debug)

        self.player.draw(self.screen)
        # arena walls
        pygame.draw.rect(self.screen, (50, 50, 50), self.arena, 3)

        # enemy
        self.enemy.draw(self.screen)

        # debug draw belly hitbox
        hitbox = self.player.get_belly_hitbox()
        #if hitbox:
            #pygame.draw.rect(self.screen, (0, 255, 0), hitbox, 2)
        offset_x = 0
        if self.hit_pause > 0:
            offset_x = (-2 if self.hit_pause % 2 == 0 else 2)

        self.screen.blit(self.screen, (offset_x, 0))

        pygame.display.flip()


    def UpdateHandler(self):
        #self.bigboy.update(dt, keys, opponent_hurtbox=None, arena_rect=self.arena)
        self.player.update()
                # update enemy physics
        self.enemy.update(self.arena, self.ground_y)
        hitbox = self.player.get_belly_hitbox()
        if hitbox and not self.player.enemy_hit_registered and hitbox.colliderect(self.enemy.rect):
            facing_right = (self.player.flip == False)
            self.enemy.launch(facing_right)
            self.player.enemy_hit_registered = True
            self.sfx_hit.play()
            self.hit_pause = 20  # frames of freeze


    def Loop(self):
        while True:
            if self.hit_pause > 0:
                self.hit_pause -= 1
                self.DisplayHandler()
                continue
            dt = self.clock.tick(FPS) / 1000.0


            self.EventHandler()
            self.UpdateHandler()

            self.DisplayHandler()
