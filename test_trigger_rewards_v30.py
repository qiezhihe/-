import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game
from rogue_content import WEAPONS
from weapon_evolutions import EVOLUTIONS


class TriggerRewardTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Game(muted=True)
    @classmethod
    def tearDownClass(cls):pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.now=1000;g.enemies=[];g.xp=0;g.xp_needed=10000
        g.boss_rewards=0;g.unlocked_weapons=set(range(8));g.weapon_slots=[0,1,3]
        g.extras.clear();g.evolutions.owned.clear();g.evolutions.clear()
        g.player=[10.,14.];g.angle=g.pitch=g.z=0;g.terrain_cells.clear()
        g.next_shot=0;g.last_gun_shot=-100000;g.reload_until=0
        g.weapon_ready=False;g.weapon_ammo.clear();g.switch_weapon(0,refill=True)
        g.upgrade_stacks.clear();g.focused=True;g.reward_is_boss=True

    def equip(self,index):
        g=self.g;g.switch_weapon(index,refill=True)
        g.next_shot=0;g.last_gun_shot=-100000;g.reload_until=0

    def test_single_action_guns_click_once_hold_never_fires_again(self):
        g=self.g
        for weapon in (1,3):
            self.equip(weapon);start=g.mag;reserve=g.reserve
            g.primary_attack(1000)
            for now in (1000,1001,2000,5000):g.primary_attack(now,held=True)
            self.assertEqual(g.mag,start-1);self.assertEqual(g.reserve,reserve)
            g.primary_attack(6000);self.assertEqual(g.mag,start-2)

    def test_kill_reset_reproduces_double_input_but_debits_one_round(self):
        g=self.g
        image=pygame.Surface((100,200),pygame.SRCALPHA);image.fill('white')
        for weapon in range(4):
            self.equip(weapon);g.state='playing';g.xp=0;g.extras['orange_reset']=.08
            g.enemies=[[15.,14.,1,0,1.,'normal',99999]]
            start=g.mag
            with patch.object(g,'enemy_visual',return_value=(image,pygame.Rect(430,200,100,200))):
                g.primary_attack(1000)
                self.assertEqual(g.next_shot,1000)  # Actual kill-reset path.
                g.primary_attack(1000,held=True)
                g.shoot(1000)  # Repeated mouse-down in the same event batch.
            self.assertEqual(g.mag,start-1)

    def test_automatic_guns_still_fire_when_held_after_cooldown(self):
        for weapon in (0,2):
            self.equip(weapon);start=self.g.mag;delay=self.g.fire_delay
            self.g.primary_attack(1000);self.g.primary_attack(1000,held=True)
            self.assertEqual(self.g.mag,start-1)
            self.g.primary_attack(1000+delay,held=True)
            self.assertEqual(self.g.mag,start-2)

    def test_stat_refresh_does_not_reopen_firing_cooldown(self):
        g=self.g;self.equip(3);g.shoot(1000);deadline=g.next_shot
        g.switch_weapon(3);self.assertEqual(g.next_shot,deadline)
        g.state='upgrade';g.choices=[('power','伤害','',0,1)];g.choose_upgrade(0)
        self.assertEqual(g.next_shot,deadline)

    def test_boss_evolutions_require_slot_not_just_unlock(self):
        g=self.g;g.weapon_slots=[3]
        with patch('weapon_evolutions.random.random',return_value=0):
            for _ in range(25):
                g.offer_upgrade(True);self.assertEqual(g.choices[2],EVOLUTIONS[3])
        g.weapon_slots=[0];g.state='upgrade';g.choices=[EVOLUTIONS[3]]
        g.choose_upgrade(0);self.assertFalse(g.evolutions.has(3))

    def test_normal_boss_specials_also_require_matching_held_weapon(self):
        g=self.g;g.weapon_slots=[0]
        forbidden={'pellets','shot_tight','shot_power','mg_power','mg_reload','sniper_power','sniper_haste',
                   'sword_arc','boomerang_return','spear_pierce','dagger_dash','melee_power','melee_guard'}
        for _ in range(100):
            g.offer_upgrade(True)
            self.assertFalse(forbidden & {card[0] for card in g.choices})

    def test_all_evolution_titles_explicitly_name_their_owner(self):
        for weapon,card in enumerate(EVOLUTIONS):
            self.assertIn(WEAPONS[weapon]['name'],card[1])
            self.assertIn('质变强化',card[1])
            self.g.choices=[card];self.g.state='upgrade';self.g.draw()

    def test_real_event_loop_click_plus_hold_is_one_sniper_shot(self):
        g=self.g;self.equip(3);before=g.mag
        events=[pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=1,pos=(480,300))]
        with patch('pygame.event.get',side_effect=[events,[pygame.event.Event(pygame.QUIT)]]),patch('pygame.mouse.get_pressed',return_value=(True,False,False)),patch.object(g,'update'),patch.object(g,'draw'):
            g._run_loop()
        self.assertEqual(g.mag,before-1)


if __name__=='__main__':unittest.main()
