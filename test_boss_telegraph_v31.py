"""Colossus telegraph sample: graded windups, silent common moves, short callout."""
import math
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game


class BossTelegraphV31Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g = Game(muted=True)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        g = self.g
        g.state = 'playing'; g.wave = 5; g.player = [14., 14.]; g.z = 0
        g.hp = g.max_hp = 100; g.shield = 0
        g.terrain_cells = set(); g.projectiles = []
        c = g.combat
        c.boss_pattern.clear(); c.boss_cycles.clear(); c.boss_impacts.clear()
        g.boss_cue_text = ''; g.boss_cue_until = 0; g.message = ''
        self.boss = [10., 14., 1000., 0, 1000., 'boss', 999999]
        g.enemies = [self.boss]

    def attack(self, now):
        with patch.object(self.g, 'sound') as sound:
            ok = self.g.combat.boss_attack(self.boss, now)
        return ok, self.g.combat.boss_pattern.get(id(self.boss)), sound

    def test_signature_windup_is_1200_and_carries_colossus_palette(self):
        ok, pattern, sound = self.attack(1000)
        self.assertTrue(ok)
        self.assertEqual(pattern['skill'], 'hammer')
        self.assertEqual(pattern['windup'] - 1000, 1200)
        self.assertEqual(pattern['telegraph']['color'], (255, 120, 40))
        sound.assert_called_once_with('boss_hammer')

    def test_common_move_windup_is_900_with_colossus_cue(self):
        self.g.combat.boss_cycles[id(self.boss)] = 1
        ok, pattern, sound = self.attack(2000)
        self.assertEqual(pattern['skill'], 'slam')
        self.assertEqual(pattern['windup'] - 2000, 900)
        sound.assert_called_once_with('boss_cue_colossus')
        self.assertEqual(self.g.boss_cue_text, '')
        self.assertEqual(self.g.message, '')

    def test_enraged_windup_floor_is_800(self):
        self.boss[2] = 400
        ok, pattern, _ = self.attack(1000)
        self.assertEqual(pattern['windup'] - 1000, 800)

    def test_signature_callout_lives_two_seconds_without_message(self):
        self.attack(1000)
        self.assertEqual(self.g.boss_cue_text, '三连地锤 · 末击后反击')
        self.assertEqual(self.g.boss_cue_until, 3000)
        self.assertEqual(self.g.message, '')

    def test_unwired_boss_keeps_legacy_windup_and_message(self):
        g = self.g
        g.wave = 10; g.combat.boss_pattern.clear(); g.combat.boss_cycles.clear()
        boss = [10., 14., 1000., 0, 1000., 'boss', 999999]
        g.enemies = [boss]
        with patch.object(g, 'sound') as sound:
            g.combat.boss_attack(boss, 1000)
        pattern = g.combat.boss_pattern[id(boss)]
        self.assertIsNone(pattern.get('telegraph'))
        self.assertEqual(pattern['windup'] - 1000, 1250)
        sound.assert_called_once_with('boss_charge')
        self.assertEqual(g.boss_cue_text, '')
        self.assertIn('猎王', g.message)

    def test_hud_and_world_render_with_colossus_telegraph(self):
        g = self.g
        g.wave = 5; g.state = 'playing'; g.z = 0; g.angle = 0; g.pitch = 0
        g.player = [14., 14.]
        self.attack(1000)
        for now in (1200, 2200, 4000):
            g.now = now
            g.boss_cue_text = '三连地锤 · 末击后反击'; g.boss_cue_until = 3000
            g.draw()

    def test_hammer_draws_every_future_stage_radius(self):
        g = self.g; g.angle = 0; g.pitch = 0; g.z = 0; g.player = [14., 14.]
        self.attack(1000)
        g.now = 1500
        captured = []
        with patch.object(g.combat, '_draw_zone', side_effect=lambda surface, vertices, *a, **k: captured.append(vertices)):
            g.combat.draw(g.screen)
        pattern = g.combat.boss_pattern[id(self.boss)]
        radii = {round(math.dist(v, pattern['target']), 2) for vertices in captured for v in vertices}
        for stage in range(3):
            self.assertIn(round(g.combat.hammer_radius(stage), 2), radii)


if __name__ == '__main__':
    unittest.main()