import os
import pygame

pygame.init()
pygame.display.set_mode((1, 1))  # <-- REQUIRED for convert()/convert_alpha()


RAW_DIR = "assets/raw"
OUT_DIR = "assets/processed"
TARGET_HEIGHT = 128
PAD = 14
WHITE = (255, 255, 255)

os.makedirs(OUT_DIR, exist_ok=True)

def autocrop(surface, pad=0):
    mask = pygame.mask.from_surface(surface)
    rects = mask.get_bounding_rects()
    if not rects:
        return surface

    r = rects[0].copy()
    for rr in rects[1:]:
        r.union_ip(rr)

    # apply padding
    r.x -= pad
    r.y -= pad
    r.w += pad * 2
    r.h += pad * 2

    # hard clip to surface bounds (safe for subsurface)
    bounds = surface.get_rect()
    x0 = max(bounds.left, r.left)
    y0 = max(bounds.top,  r.top)
    x1 = min(bounds.right, r.right)
    y1 = min(bounds.bottom, r.bottom)

    # if something went weird, just return original
    if x1 <= x0 or y1 <= y0:
        return surface

    return surface.subsurface((x0, y0, x1 - x0, y1 - y0)).copy()

def process_image(path):
    surf = pygame.image.load(path).convert_alpha()
    w, h = surf.get_size()
    px = pygame.PixelArray(surf)

    # tuned for projector screen + black outfit
    BRIGHT = 150      # lower = more aggressive background kill
    CHROMA = 45       # allows slight tint variation
    HARD_ALPHA = 180  # cutoff to eliminate halos

    for y in range(h):
        for x in range(w):
            r, g, b, a = surf.unmap_rgb(px[x, y])

            vmax = max(r, g, b)
            vmin = min(r, g, b)
            chroma = vmax - vmin

            if vmax >= BRIGHT and chroma <= CHROMA:
                # background → fully transparent
                px[x, y] = (r, g, b, 0)
            else:
                # force solid alpha (kills glow/halo)
                px[x, y] = (r, g, b, 255)

    del px  # unlock surface

    # --- crop using alpha ---
    surf = autocrop(surf, PAD)

    # --- scale (pixel art friendly) ---
    scale = TARGET_HEIGHT / surf.get_height()
    new_w = max(1, int(round(surf.get_width() * scale)))
    surf = pygame.transform.scale(surf, (new_w, TARGET_HEIGHT))

    return surf

for name in sorted(os.listdir(RAW_DIR)):
    if not name.lower().endswith((".png", ".jpg", ".jpeg")):
        continue

    src = os.path.join(RAW_DIR, name)
    out = process_image(src)

    out_name = os.path.splitext(name)[0] + ".png"
    out_path = os.path.join(OUT_DIR, out_name)

    pygame.image.save(out, out_path)
    print("saved", out_path)

pygame.quit()
