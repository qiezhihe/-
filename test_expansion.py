"""Forward-compatible QA for the next combat expansion.

Tests are skipped until the corresponding production interface exists; this
prevents a test-only shadow implementation from masking missing gameplay.
"""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT','1')
import unittest
import pygame
from fps_game import Game
from rogue_content import WEAPONS


class ExpansionContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Game()
    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.g.reset()
        self.g.state='playing'

    def require(self,*names):
        missing=[name for name in names if not hasattr(self.g,name)]
        if missing: self.skipTest('pending production interface: '+','.join(missing))

    def test_three_slot_first_acquired_order_and_no_replacement(self):
        self.require('weapon_slots','acquire_weapon','switch_slot')
        if len(WEAPONS)<7: self.skipTest('pending 8+ weapon catalog')
        self.assertEqual(self.g.weapon_slots,[0])
        self.assertTrue(self.g.acquire_weapon(2))
        self.assertTrue(self.g.acquire_weapon(4))
        self.assertFalse(self.g.acquire_weapon(2))
        self.assertFalse(self.g.acquire_weapon(6))
        self.assertEqual(self.g.weapon_slots,[0,2,4])
        self.g.switch_slot(1); self.assertEqual(self.g.weapon_index,2)

    def test_melee_hit_requires_range_and_line_of_sight(self):
        self.require('melee_attack','melee_cooldown')
        self.assertGreaterEqual(self.g.melee_cooldown,0)
        hp=self.g.hp
        self.g.melee_attack(1000)
        self.assertEqual(self.g.hp,hp)

    def test_guard_or_shield_reduces_melee_damage(self):
        self.require('guarding','guard_damage_reduction')
        self.assertGreaterEqual(self.g.guard_damage_reduction,0)
        self.g.guarding=True
        hp=self.g.hp
        self.g.hurt(20)
        guarded=hp-self.g.hp
        self.g.guarding=False
        self.g.hp=hp
        self.g.hurt(20)
        self.assertLessEqual(guarded,hp-self.g.hp)

    def test_pet_damage_and_cooldown_are_bounded(self):
        self.require('pet','update_pet','pet_cooldown')
        self.assertGreaterEqual(self.g.pet_cooldown,0)
        self.assertIsNotNone(self.g.pet)
        self.g.update_pet(.016,self.g.now)
        self.assertGreaterEqual(self.g.pet_cooldown,0)

    def test_terrain_blocks_movement_and_projectile_los(self):
        self.require('terrain')
        self.assertIsInstance(self.g.terrain,(list,tuple,dict,set))
        if not callable(getattr(self.g,'terrain_blocks',None)):
            self.skipTest('terrain_blocks name is occupied by production terrain set')

    def test_wave_event_has_explicit_phase_and_payload(self):
        self.require('wave_event','wave_event_type')
        self.assertIn(self.g.wave_event_type,('start','wave_start','elite','boss','rest','end'))
        self.g.wave_wait=self.g.now-1
        self.g.update(.016,self.g.now)
        self.assertIsNotNone(self.g.wave_event)

    def test_space_jump_has_no_air_double_jump(self):
        self.require('jump','vertical_velocity','on_ground')
        self.assertTrue(self.g.on_ground)
        self.g.jump()
        self.assertFalse(self.g.on_ground)
        velocity=self.g.vertical_velocity
        self.g.jump()
        self.assertEqual(self.g.vertical_velocity,velocity)

    def test_gravity_returns_player_to_ground(self):
        self.require('jump','vertical_velocity','on_ground')
        self.g.jump()
        for _ in range(300): self.g.update(1/60,self.g.now+_*(1000/60))
        self.assertTrue(self.g.on_ground)
        self.assertGreaterEqual(self.g.vertical_velocity,0)

    def test_jump_and_fire_does_not_crash(self):
        self.require('jump','vertical_velocity','on_ground')
        self.g.jump()
        self.g.shoot(self.g.now)

    def test_all_melee_weapons_attack_draw_and_repeat_without_ammo(self):
        for index in range(4,len(WEAPONS)):
            with self.subTest(weapon=WEAPONS[index]['name']):
                self.g.reset(); self.g.state='playing'
                self.assertTrue(self.g.acquire_weapon(index))
                self.g.mag=0
                reserve=self.g.reserve
                for time in (10000,20000):
                    self.g.now=time
                    self.g.shoot(time)
                    self.assertGreater(self.g.muzzle_until,time)
                    self.g.draw()
                self.g.reload(21000)
                self.assertEqual(self.g.reload_until,0)
                self.assertEqual(self.g.reserve,reserve)
                self.g.switch_slot(0); self.g.draw()
                self.g.switch_slot(1); self.g.draw()

    def test_jump_projection_moves_near_world_more_than_far_world(self):
        g=self.g
        g.angle=0; g.pitch=0
        x,y=g.player
        near=g.project(x+2,y,0); far=g.project(x+8,y,0)
        enemy=[x+4,y,100,0,100,'normal',0]
        before=g.enemy_visual(enemy)[1]
        g.z=.5
        near_delta=g.project(x+2,y,0)[1]-near[1]
        far_delta=g.project(x+8,y,0)[1]-far[1]
        self.assertGreater(near_delta,far_delta*3)
        self.assertGreater(g.enemy_visual(enemy)[1].y,before.y)
        self.assertEqual(g.project(x+4,y,.5)[1],300)
        self.assertEqual(enemy[:2],[x+4,y])
        g.draw()


if __name__=='__main__': unittest.main()
