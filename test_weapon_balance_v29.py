"""Independent reserves, real headshot damage, baseline roles and audio gain."""
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import numpy as np
import pygame
from fps_game import Game
from rogue_content import WEAPONS


class WeaponBalanceTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls):pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.now=1000;g.unlocked_weapons=set(range(8))
        g.weapon_reserves.clear();g.weapon_ammo.clear();g.weapon_ready=False
        g.extras.clear();g.mag_bonus=0;g.damage_bonus=g.rate_bonus=g.reload_bonus=1
        g.evolutions.owned.clear();g.evolutions.clear();g.combat.throws.clear()
        g.terrain_cells.clear();g.lava_cells.clear();g.enemies=[];g.boss_rewards=0;g.xp=0
        g.player=[10.,14.];g.angle=g.pitch=g.z=0;g.evolutions.clear()
        g.combat.cooldown=0;g.combat.boss_pattern.clear();g.damage_popups.clear()
        g.pet['rage_until']=0;g.pierce=g.blast=0;g.switch_weapon(0,refill=True)
        g.reload_until=0;g.next_shot=0;g.last_gun_shot=-100000

    def test_baseline_stats_applied_to_all_eight(self):
        g=self.g
        for i,w in enumerate(WEAPONS):
            g.switch_weapon(i)
            self.assertEqual(g.damage,w['damage']);self.assertEqual(g.fire_delay,w['delay'])
            self.assertEqual(g.mag_size,w['mag']);self.assertEqual(g.reload_duration,w['reload'])
        self.assertGreater(WEAPONS[0]['delay'],35)
        self.assertLess(WEAPONS[0]['delay'],WEAPONS[2]['delay'])
        self.assertGreater(WEAPONS[3]['damage'],WEAPONS[2]['damage'])
        self.assertGreater(WEAPONS[2]['reload'],WEAPONS[0]['reload'])

    def test_guns_start_with_distinct_reserves_and_caps(self):
        for i in range(4):
            self.g.switch_weapon(i)
            self.assertEqual(self.g.reserve,WEAPONS[i]['reserve'])
            self.assertEqual(self.g.reserve_max,WEAPONS[i]['reserve_max'])

    def test_fresh_run_starts_with_full_first_magazine(self):
        g=self.g;g.reset()
        self.assertEqual((g.weapon_index,g.mag,g.mag_size,g.reserve),(0,30,30,150))
        self.assertEqual(g.weapon_reserves,{0:150})

    def test_switch_roundtrip_preserves_each_magazine_and_reserve(self):
        g=self.g
        for i in range(4):
            g.switch_weapon(i);g.mag=i+1;g.reserve=11+i
        for i in range(4):
            g.switch_weapon(i);self.assertEqual((g.mag,g.reserve),(i+1,11+i))

    def test_reload_debits_only_equipped_gun_once(self):
        g=self.g
        for i in range(4):g.switch_weapon(i);g.reserve=10
        for i in range(4):
            g.switch_weapon(i);g.mag=1;g.reload_until=0;g.reload(1000)
            end=g.reload_until;before=dict(g.weapon_reserves)
            g.update(.001,end+1)
            transfer=min(WEAPONS[i]['mag']-1,10)
            self.assertEqual(g.reserve,10-transfer);self.assertEqual(g.mag,1+transfer)
            self.assertTrue(all(g.weapon_reserves[j]==value for j,value in before.items() if j!=i))
            g.update(.001,end+2);self.assertEqual(g.reserve,10-transfer)

    def test_switch_cancels_reload_without_losing_other_ammo(self):
        g=self.g;g.mag=1;g.reserve=40;g.reload(1000);g.switch_weapon(1)
        self.assertEqual(g.reload_until,0);g.switch_weapon(0)
        self.assertEqual((g.mag,g.reserve),(1,40))

    def test_wave_preserves_all_four_reserves(self):
        g=self.g
        for i in range(4):g.switch_weapon(i);g.reserve=i+2
        before=dict(g.weapon_reserves);g.switch_weapon(7);g.spawn_wave()
        self.assertEqual(g.weapon_reserves,before)
        self.assertEqual((g.mag,g.mag_size,g.reserve,g.reserve_max),(0,0,0,0))

    def test_melee_has_no_ammo_even_with_magazine_upgrades(self):
        g=self.g;g.mag_bonus=15
        for i in range(4,8):
            g.switch_weapon(i);g.reserve=999;g.reload(1000)
            self.assertEqual((g.mag,g.mag_size,g.reserve,g.reserve_max,g.reload_until),(0,0,0,0,0))
            self.assertNotIn(i,g.weapon_reserves);self.assertNotIn(i,g.weapon_ammo)
            self.assertNotIn('备弹',g.ammo_text());self.assertNotIn('弹匣',g.ammo_text(True))
            g.state='playing';g.draw()
            g.state='character';g.draw()

    def test_ammo_station_refills_all_owned_guns_from_melee(self):
        g=self.g;g.unlocked_weapons={0,2,7};g.switch_weapon(0);g.reserve=0
        g.switch_weapon(2);g.reserve=0;g.switch_weapon(7);g.player=list(g.ammo_station)
        g.refill_reserve()
        self.assertEqual(g.weapon_reserves,{0:300,2:400});self.assertEqual(g.reserve,0)

    def test_supply_is_scaled_for_each_gun_and_capped(self):
        g=self.g
        for i in range(4):g.switch_weapon(i);g.reserve=0
        g.switch_weapon(7);g.grant_ammo_supply(8)
        self.assertEqual(g.weapon_reserves,{0:8,1:3,2:27,3:2})
        g.grant_ammo_supply(100000)
        self.assertEqual(g.weapon_reserves,{i:WEAPONS[i]['reserve_max'] for i in range(4)})

    def test_kill_supply_works_while_holding_melee(self):
        g=self.g
        for i in range(4):g.switch_weapon(i);g.reserve=0
        g.switch_weapon(4);g.extras['blue_supply']=8
        g.enemies=[[15.,14.,0,0,100.,'normal',99999],[16.,14.,100,0,100.,'normal',99999]]
        g.finish_kills(1000)
        self.assertEqual(g.weapon_reserves,{0:8,1:3,2:27,3:2})
        self.assertEqual(g.reserve,0)

    def shot_damage(self,weapon,head=False,crit=False):
        g=self.g;g.switch_weapon(weapon,refill=True);g.next_shot=0;g.reload_until=0
        g.last_gun_shot=-100000
        g.damage_popups.clear();g.extras['crit']=.8 if crit else 0
        enemy=[15.,14.,10000.,0,10000.,'normal',99999];g.enemies=[enemy]
        image=pygame.Surface((200,400),pygame.SRCALPHA);image.fill('white')
        rect=pygame.Rect(380,270 if head else 100,200,400)
        with patch.object(g,'enemy_visual',return_value=(image,rect)),patch.object(g,'finish_kills'),patch('fps_game.random.random',return_value=0 if crit else 1):
            g.shoot(1000)
        return 10000-enemy[2]

    def test_all_gun_body_and_head_damage_real_hits(self):
        for i in range(4):
            body=self.shot_damage(i);head=self.shot_damage(i,True)
            self.assertAlmostEqual(body,WEAPONS[i]['damage']*WEAPONS[i]['pellets'])
            self.assertAlmostEqual(head,body*WEAPONS[i]['headshot'])
            self.assertEqual(self.g.damage_popups[-1]['hit_z'],1.12)
            self.assertEqual(self.g.mag,WEAPONS[i]['mag']-1)

    def test_headshot_and_critical_stack_once(self):
        for i in range(4):
            amount=self.shot_damage(i,True,True)
            expected=WEAPONS[i]['damage']*WEAPONS[i]['pellets']*WEAPONS[i]['headshot']*2
            self.assertAlmostEqual(amount,expected)
            self.assertEqual(self.g.damage_popups[-1]['color'],'yellow')

    def test_footstep_runtime_normalized_centered_and_original_unchanged(self):
        import wave
        g=self.g;data=pygame.sndarray.array(g.sounds['footstep']).astype(np.int32)
        self.assertAlmostEqual(np.abs(data).max(),28000,delta=3)
        if data.ndim==2:self.assertTrue(np.array_equal(data[:,0],data[:,1]))
        self.assertAlmostEqual(g.sounds['footstep'].get_volume(),.85,delta=.008)
        with wave.open('Assets/audio/footstep.wav') as wav:
            original=np.frombuffer(wav.readframes(wav.getnframes()),dtype='<i2').astype(np.int32)
        self.assertLess(np.abs(original).max(),10000)

    def test_footstep_reserved_channel_and_mute(self):
        g=self.g
        with patch.object(g,'footstep_channel') as channel:
            g.muted=False;g.sound('footstep');channel.play.assert_called_once_with(g.sounds['footstep'])
            channel.reset_mock();g.muted=True;g.sound('footstep');channel.play.assert_not_called()


if __name__=='__main__':unittest.main()
