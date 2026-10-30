"""Focused regressions for weapon state inheritance and corner navigation."""
import os
os.environ['SDL_VIDEODRIVER']='dummy'
os.environ['SDL_AUDIODRIVER']='dummy'
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game

class MotionSwitchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g=Game()
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def test_new_weapon_clears_attack_and_guard(self):
        g=self.g
        g.now=1000
        g.weapon_action_start=990; g.muzzle_until=1070
        g.combat.cooldown=1600; g.combat.guard=True; g.guarding=True
        g.combat.active=[('slash',1200,0)]
        g.unlocked_weapons={0}; g.weapon_slots=[0]; g.weapon_index=0
        self.assertTrue(g.acquire_weapon(4))
        self.assertEqual(g.weapon_action_start,-100000)
        self.assertEqual(g.muzzle_until,0)
        self.assertEqual(g.combat.cooldown,0)
        self.assertFalse(g.guarding)
        self.assertFalse(g.combat.active)

    def test_stationary_enemy_is_idle(self):
        g=self.g; g.now=2000
        e=[10.,10.,100,0,100,'normal',0]
        self.assertEqual(g.enemy_art.state(g,e),'idle')
        with patch.object(g,'enemy_position_clear',return_value=True):
            g.move_enemy(e,.1,0)
        self.assertEqual(g.enemy_art.state(g,e),'walk_left')
        g.now+=101
        self.assertEqual(g.enemy_art.state(g,e),'idle')

    def test_blocked_motion_does_not_advance_stride(self):
        g=self.g; e=[10.,10.,100,0,100,'normal',0]
        g._enemy_motion={}
        with patch.object(g,'enemy_position_clear',return_value=False):
            g.move_enemy(e,1,0)
        self.assertNotIn(id(e),g._enemy_motion)

    def test_route_recenters_before_blocked_corner(self):
        g=self.g; g.terrain_cells={(11,10)}
        e=[10.78,10.5,100,0,100,'normal',0]
        point=g.enemy_waypoint(e,(12.5,10.5))
        self.assertTrue(g.enemy_position_clear(*point))
        self.assertLessEqual(point[0],10.5)

if __name__=='__main__': unittest.main()
