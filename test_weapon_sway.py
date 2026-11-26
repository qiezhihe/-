import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import math
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game


class WeaponSwayTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.unlocked_weapons.add(2);g.switch_weapon(2)
        g.reload_until=0;g.muzzle_until=0;g.now=1000;g.cloud_art.cache.clear()

    def test_walking_uses_small_rotation_and_stationary_is_stable(self):
        g=self.g;g.walking=False;g.walk_phase=math.pi/2
        with patch.object(pygame.transform,'rotate',wraps=pygame.transform.rotate) as rotate:
            g.cloud_art.weapon(g)
            self.assertFalse(rotate.called)
            g.cloud_art.cache.clear();g.walking=True
            g.cloud_art.weapon(g)
            self.assertTrue(rotate.called)
            angle=rotate.call_args.args[1]
            self.assertLessEqual(abs(angle),.9)

    def test_weapon_anchor_is_lower_right(self):
        g=self.g;g.walking=False
        old=g.screen;target=pygame.Surface(old.get_size(),pygame.SRCALPHA);g.screen=target
        try:g.cloud_art.weapon(g);bounds=target.get_bounding_rect(min_alpha=128)
        finally:g.screen=old
        self.assertLessEqual(bounds.right,g.screen.get_width()-8)
        self.assertLessEqual(bounds.bottom,g.screen.get_height()-8)
        self.assertGreater(bounds.right,g.screen.get_width()-120)

    def test_reload_keeps_authored_frame_without_bob(self):
        g=self.g;g.reload_start=1000;g.reload_duration=1400;g.reload_until=2400;g.now=1700
        g.walking=True;g.walk_phase=math.pi/2
        with patch.object(pygame.transform,'rotate',wraps=pygame.transform.rotate) as rotate:
            g.cloud_art.weapon(g)
            self.assertFalse(rotate.called)
            self.assertTrue(any(k[0].startswith('low_mg_reload_v16_') for k in g.cloud_art.cache))


if __name__=='__main__': unittest.main()
