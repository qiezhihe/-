"""Render the colossus telegraph sample for visual QA."""
import os
import sys
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, root)
import pygame
from fps_game import Game


def main():
    g = Game(muted=True)
    g.state = 'playing'; g.wave = 5; g.z = 0; g.pitch = 0; g.angle = 0.
    boss = [20., 14., 1000., 0, 1000., 'boss', 999999]
    g.enemies = [boss]; g.player = [16., 14.]
    g.combat.boss_cycles.clear(); g.combat.boss_pattern.clear()
    g.combat.boss_attack(boss, 1000)
    target = g.combat.boss_pattern[id(boss)]['target']
    g.player = [target[0] - 4., target[1]]
    g.now = 1500
    g.boss_cue_text = '三连地锤 · 末击后反击'; g.boss_cue_until = 3000
    g.draw()
    folder = os.path.join(root, 'qa_screenshots')
    os.makedirs(folder, exist_ok=True)
    out = os.path.join(folder, 'boss_telegraph_v31.png')
    pygame.image.save(g.screen, out)
    lava = hud = 0
    width, height = g.screen.get_size()
    for x in range(0, width, 2):
        for y in range(0, height, 2):
            r, gr, b, _ = g.screen.get_at((x, y))
            if r > 200 and 70 <= gr <= 195 and b < 115: lava += 1
    for x in range(width // 2 - 200, width // 2 + 200):
        for y in range(92, 124):
            r, gr, b, _ = g.screen.get_at((x, y))
            if r > 180 and gr > 120 and b < 180: hud += 1
    print(out, 'lava_pixels', lava, 'hud_cue_pixels', hud)


if __name__ == '__main__':
    main()