import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
import pygame
from fps_game import Game

class MeleeTests(unittest.TestCase):
    def setUp(self):
        self.g=Game(); self.g.state='playing'; self.g.angle=0
        self.g.terrain_cells=set()

    def tearDown(self):
        pygame.quit()

    def equip(self,index):
        self.g.unlocked_weapons.add(index); self.g.switch_weapon(index)

    def test_ground_enemy_feet_match_ground_during_player_jump(self):
        g=self.g; g.wave=5
        for z in (0,.35,.65):
            g.z=z
            for kind in ('normal','runner','shooter','elite'):
                e=[18.,14.,100,0,100,kind,0]
                image,rect=g.enemy_visual(e,hit_test=True)
                feet=rect.y+image.get_bounding_rect(min_alpha=128).bottom
                ground=g.project(18,14,-.5)[1]
                self.assertLessEqual(abs(feet-ground),1)

    def test_enemy_knockback_cannot_tunnel_into_platform(self):
        g=self.g; g.terrain_cells={(15,14)}
        e=[14.,14.5,100,0,100,'normal',0]
        g.move_enemy(e,4,0)
        self.assertLess(e[0],15)
        self.assertTrue(g.enemy_position_clear(*e[:2]))

    def test_enemy_inside_raised_platform_is_recovered(self):
        g=self.g; g.terrain_cells={(15,14)}
        e=[15.5,14.5,100,0,100,'normal',0]
        g.unstuck_enemy(e)
        self.assertTrue(g.enemy_position_clear(*e[:2]))

    def test_spear_returns_after_exact_range(self):
        self.equip(6); g=self.g; g.enemies=[]; g.player=[5.,5.]
        g.combat.attack(1000)
        for i in range(1,200): g.combat.update(.016,1000+i*16)
        self.assertEqual(g.combat.throws,[])

    def test_dead_boss_cannot_fire_and_pattern_is_removed(self):
        g=self.g; g.wave=5; g.enemies=[]
        e=self.enemy(10,14); c=g.combat; c.boss_attack(e,1000)
        e[2]=0; c.update(.016,1800)
        self.assertEqual(g.projectiles,[])
        self.assertNotIn(id(e),c.boss_pattern)
        self.assertFalse(c.boss_attack(e,2000))

    def test_charge_hits_exact_locked_endpoint_once(self):
        g=self.g; g.wave=10; g.enemies=[]
        e=self.enemy(10,14); c=g.combat; c.boss_attack(e,1000)
        g.player=[18,14]
        pattern=c.boss_pattern[id(e)]
        for now in range(pattern['windup'],pattern['windup']+651,50): c.update(.05,now)
        self.assertAlmostEqual(e[0],14)
        self.assertAlmostEqual(e[1],14)
        self.assertEqual(g.hp,g.max_hp)

    def test_charge_does_not_cross_wall(self):
        g=self.g; g.wave=10; g.enemies=[]; g.terrain_cells={(12,14)}
        e=self.enemy(10,14); c=g.combat; c.boss_attack(e,1000)
        for now in range(1900,2501,50): c.update(.05,now)
        self.assertLess(e[0],12)

    def test_expired_skill_does_not_fire_late(self):
        g=self.g; g.wave=5; g.enemies=[]
        e=self.enemy(10,14); c=g.combat; c.boss_attack(e,1000)
        c.update(.05,10000)
        self.assertEqual(g.projectiles,[])
        self.assertNotIn(id(e),c.boss_pattern)

    def test_new_wave_clears_boss_skills(self):
        g=self.g; g.enemies=[]; e=self.enemy(10,14)
        g.combat.boss_attack(e,1000); g.spawn_wave()
        self.assertEqual(g.combat.boss_pattern,{})

    def test_laser_jump_and_windup_are_safe(self):
        g=self.g; g.wave=15; g.enemies=[]
        e=self.enemy(10,14); c=g.combat
        c.boss_cycles[id(e)]=1; c.boss_attack(e,1000)
        hp=g.hp
        c.update(.016,1500)
        self.assertEqual(g.hp,hp)
        g.z=.6; c.update(.016,2100)
        self.assertEqual(g.hp,hp)
        g.z=0; c.update(.016,2100)
        self.assertLess(g.hp,hp)

    def test_navigation_routes_around_wall(self):
        g=self.g; g.terrain_cells={(15,14)}
        e=[14.5,14.5]
        point=g.enemy_waypoint(e,(17.5,14.5))
        self.assertTrue(g.enemy_position_clear(*point))
        self.assertNotEqual(point,(17.5,14.5))

    def test_boomerang_cannot_duplicate_before_return(self):
        self.equip(5)
        c=self.g.combat
        c.attack(1000)
        c.attack(1000+self.g.fire_delay+1)
        self.assertEqual(len(c.throws),1)
        c.update(.016,2200)
        self.assertEqual(c.throws,[])
        c.attack(max(2300,c.cooldown))
        self.assertEqual(len(c.throws),1)

    def enemy(self,x,y):
        e=[x,y,1000,0,1000,'normal',0]; self.g.enemies.append(e); return e

    def test_dash_hits_start_middle_end_not_side(self):
        self.equip(7); self.g.enemies=[]
        targets=[self.enemy(x,14) for x in (14.1,15.4,16.7)]
        side=self.enemy(15.4,15)
        self.g.combat.attack(1000)
        for e in targets: self.assertEqual(e[2],1000-self.g.damage)
        self.assertEqual(side[2],1000)

    def test_dash_wall_blocks_target(self):
        self.equip(7); self.g.terrain_cells={(15,14)}; self.g.enemies=[]
        e=self.enemy(16,14); self.g.combat.attack(1000)
        self.assertEqual(e[2],1000); self.assertLess(self.g.player[0],15)

    def test_sword_arc_and_wall(self):
        self.equip(4); self.g.enemies=[]
        front=self.enemy(15,14); rear=self.enemy(13,14)
        self.g.combat.attack(1000)
        self.assertLess(front[2],1000); self.assertEqual(rear[2],1000)

    def test_spear_sweeps_multiple_targets_once(self):
        self.equip(6); self.g.enemies=[]
        targets=[self.enemy(x,14) for x in (14.5,15,15.8)]
        self.g.combat.attack(1000); self.g.combat.update(.2,1200)
        for e in targets: self.assertEqual(e[2],1000-self.g.damage)
        self.g.combat.update(.01,1210)
        for e in targets: self.assertEqual(e[2],1000-self.g.damage)

    def test_melee_audio_and_render(self):
        for name in ('sword_swing','boomerang_throw','spear_throw','dagger_dash','melee_hit'):
            self.assertIn(name,self.g.sounds)
        for index in range(4,8):
            self.equip(index); self.g.draw()

    def test_usage_bias_and_shared_melee_eligibility(self):
        self.equip(6); self.g.weapon_usage[6]=100
        self.assertEqual(self.g.upgrade_weight('spear_pierce'),7)
        self.assertEqual(self.g.upgrade_weight('melee_armor'),7)
        self.assertEqual(self.g.upgrade_weight('smg_haste'),1)
        self.g.state='paused'; before=self.g.weapon_usage.copy()
        self.g.update(1,1000); self.assertEqual(before,self.g.weapon_usage)

    def test_melee_sustain_cooldown_and_armor(self):
        self.equip(4); self.g.hp=50
        self.g.extras.update(melee_sustain=3,melee_armor=.2)
        e=self.enemy(15,14)
        self.g.combat._hit(e,1,1000); self.g.combat._hit(e,1,1100)
        self.assertEqual(self.g.hp,53)
        self.g.hurt(10); self.assertEqual(self.g.hp,45)
        self.g.combat._hit(e,1,1400); self.assertEqual(self.g.hp,48)

if __name__=='__main__': unittest.main()
