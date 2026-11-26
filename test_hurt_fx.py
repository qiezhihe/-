"""Player hit-feedback regressions: red damage language, blue/white protection."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy');os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import math
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game


class HurtFeedbackTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def setUp(self):
        g=self.g
        g.state='playing'; g.now=1000; g.enemies=[]; g.hp=100; g.max_hp=100; g.shield=0
        g.guarding=False; g.guard_damage_reduction=0.0; g.extras={}
        g.player=[10.,10.]; g.angle=0.0
        g.hurt_vignette_until=0; g.hurt_vignette_peak=0.0; g.hurt_arcs=[]
        g.shake_until=0; g.hitstop_until=0; g.shield_fx_until=0; g.block_fx_until=0
        g.dodge_until=0; g.hurt_beat_until=0; g.low_hp_alpha=0.0

    def test_source_creates_directional_arc(self):
        self.g.hurt(10,source=(10.,9.))
        self.assertEqual(len(self.g.hurt_arcs),1)
        self.assertAlmostEqual(self.g.hurt_arcs[0]['angle'],-math.pi/2,places=3)
        self.assertEqual(self.g.hurt_arcs[0]['end'],1600)

    def test_arc_angle_maps_right_side_to_positive(self):
        self.g.hurt(10,source=(11.,10.))
        self.assertAlmostEqual(self.g.hurt_arcs[0]['angle'],0.0,places=3)

    def test_arcs_are_capped_at_four(self):
        for _ in range(8): self.g.hurt(5,source=(12.,10.))
        self.assertLessEqual(len(self.g.hurt_arcs),4)

    def test_no_source_means_no_arc(self):
        self.g.hurt(10)
        self.assertEqual(self.g.hurt_arcs,[])

    def test_vignette_peak_accumulates_and_caps(self):
        self.g.hurt(5); first=self.g.hurt_vignette_peak
        self.g.hurt(5); self.assertGreater(self.g.hurt_vignette_peak,first)
        for _ in range(20): self.g.hurt(20)
        self.assertLessEqual(self.g.hurt_vignette_peak,1.6)

    def test_zero_amount_is_silent(self):
        self.g.hurt(0)
        self.assertEqual(self.g.hurt_vignette_until,0)
        self.assertEqual(self.g.shake_until,0)
        self.assertEqual(self.g.hitstop_until,0)

    def test_small_damage_shakes_without_hitstop(self):
        self.g.hurt(5)
        self.assertEqual(self.g.shake_until,1140)
        self.assertEqual(self.g.hitstop_until,0)

    def test_heavy_damage_triggers_hitstop_only_at_15(self):
        self.g.hurt(14); self.assertEqual(self.g.hitstop_until,0)
        self.g.hurt(15); self.assertEqual(self.g.hitstop_until,1050)

    def test_hitstop_is_not_refreshed_while_active(self):
        self.g.hurt(15); deadline=self.g.hitstop_until
        self.g.hurt(15)
        self.assertEqual(self.g.hitstop_until,deadline)

    def test_hitstop_expires_in_real_time_and_clock_resumes(self):
        g=self.g; g.hurt(15)
        frozen=g.now
        for _ in range(3): g.advance_clock(1/60)
        self.assertEqual(g.now,frozen)
        g.advance_clock(1/60)
        self.assertGreater(g.now,frozen)

    def test_shield_absorb_creates_blue_ring_not_red_vignette(self):
        self.g.shield=40
        self.g.hurt(10)
        self.assertEqual(self.g.hp,100); self.assertEqual(self.g.shield,30)
        self.assertEqual(self.g.shield_fx_until,1350)
        self.assertEqual(self.g.shake_until,1140)
        self.assertEqual(self.g.hurt_vignette_until,0)

    def test_dodge_creates_ghost_not_damage(self):
        self.g.extras={'dodge':1.0}
        with patch('fps_game.random.random',return_value=0.0):
            self.g.hurt(10)
        self.assertEqual(self.g.hp,100)
        self.assertEqual(self.g.dodge_until,1120)
        self.assertEqual(self.g.hurt_vignette_until,0)

    def test_guard_creates_block_flash(self):
        self.g.guarding=True; self.g.guard_damage_reduction=.5
        self.g.hurt(10)
        self.assertEqual(self.g.hp,95)
        self.assertEqual(self.g.block_fx_until,1250)

    def test_low_hp_pulse_rises_and_falls(self):
        g=self.g; g.hp=10
        g.draw_hurt_fx(g.screen); deep=g.low_hp_alpha
        for _ in range(20): g.draw_hurt_fx(g.screen)
        self.assertGreater(g.low_hp_alpha,deep)
        g.hp=100
        for _ in range(40): g.draw_hurt_fx(g.screen)
        self.assertLess(g.low_hp_alpha,.05)

    def test_shake_offset_stays_within_two_pixels(self):
        self.g.shake_until=1400
        for _ in range(12):
            ox,oy=self.g.shake_offset()
            self.assertLessEqual(abs(ox),2); self.assertLessEqual(abs(oy),2)

    def test_draw_with_every_layer_does_not_crash(self):
        g=self.g; g.hp=20; g.shield=10
        g.hurt(5,source=(12.,10.)); g.dodge_until=g.now+120
        g.draw()


if __name__=='__main__': unittest.main()