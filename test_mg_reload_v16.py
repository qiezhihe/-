import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import hashlib
import pygame
from fps_game import Game


class MachinegunReloadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls):pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.now=1000
        g.unlocked_weapons.add(2);g.switch_weapon(2)
        g.reload_until=0;g.weapon_action_start=-100000;g.muzzle_until=0

    def selected(self):
        g=self.g;g.cloud_art.cache.clear();g.cloud_art.weapon(g)
        return [key[0] for key in g.cloud_art.cache if key[0].startswith('low_mg')]

    def test_eight_distinct_alpha_frames(self):
        frames=[self.g.cloud_art.low_frames[f'low_mg_reload_v16_{i}'] for i in range(8)]
        self.assertEqual(len({hashlib.sha256(pygame.image.tobytes(f,'RGBA')).digest() for f in frames}),8)
        for frame in frames:
            self.assertEqual(frame.get_size(),(256,256))
            self.assertEqual(frame.get_at((0,0)).a,0)
            self.assertGreater(frame.get_bounding_rect().height,220)

    def test_all_reload_poses_follow_actual_duration_and_override_firing(self):
        g=self.g
        for duration in (250,750,2400,4800):
            g.reload_start=1000;g.reload_duration=duration;g.reload_until=1000+duration
            for i in range(8):
                g.now=1000+duration*(i+.5)/8;g.muzzle_until=g.now+70
                self.assertEqual(self.selected(),[f'low_mg_reload_v16_{i}'])

    def test_r_starts_animation_and_switch_cancels_it(self):
        g=self.g;g.mag=0;g.reserve=200;g.reload(g.now)
        self.assertGreater(g.reload_until,g.now)
        self.assertEqual(self.selected(),['low_mg_reload_v16_0'])
        g.switch_weapon(0);g.switch_weapon(2)
        self.assertEqual(g.reload_until,0)
        self.assertEqual(self.selected(),['low_mg_v9_0'])

    def test_idle_and_fire_unchanged_after_reload(self):
        g=self.g;self.assertEqual(self.selected(),['low_mg_v9_0'])
        g.muzzle_until=g.now+70
        self.assertEqual(self.selected(),['low_mg_v9_1'])

    def test_missing_new_sheet_falls_back_to_legacy_reload_not_idle(self):
        g=self.g
        saved={key:g.cloud_art.low_frames.pop(key) for key in list(g.cloud_art.low_frames) if key.startswith('low_mg_reload_v16_')}
        try:
            g.reload_start=1000;g.reload_duration=2400;g.reload_until=3400;g.now=1100
            self.assertEqual(self.selected(),['low_mg_anim_8'])
        finally:g.cloud_art.low_frames.update(saved)


if __name__=='__main__':unittest.main()
