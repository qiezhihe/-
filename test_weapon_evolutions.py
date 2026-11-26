import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game
from rogue_content import UPGRADES
from weapon_evolutions import EVOLUTIONS, BOSS_EVOLUTION_CHANCE


class EvolutionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Game(muted=True)

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.now=1000;g.player=[10.,14.];g.angle=g.pitch=g.z=0
        g.terrain_cells.clear();g.lava_cells.clear();g.enemies=[]
        g.evolutions.owned.clear();g.evolutions.clear();g.combat.throws.clear();g.combat.active.clear()
        g.combat.cooldown=0;g.combat.boss_pattern.clear();g.effects.clear()
        g.damage_popups.clear();g.kill_methods.clear();g.melee_staggers.clear()
        g.unlocked_weapons=set(range(8));g.weapon_slots=list(range(8));g.weapon_usage=[0.]*8
        g.extras.clear();g.upgrade_stacks.clear();g.damage_bonus=g.rate_bonus=1
        g.stamina=100;g.blink_stamina_cost=28;g.boss_rewards=0;g.xp=0;g.focused=True
        g.switch_weapon(0,refill=True);g.reload_until=0;g.next_shot=0;g.pierce=g.blast=0;g.last_gun_shot=-100000
        g.pet['rage_until']=0;g.reward_is_boss=True

    def enemy(self,x,y=14,hp=10000,kind='normal'):
        e=[float(x),float(y),float(hp),0,float(hp),kind,99999]
        self.g.enemies.append(e)
        return e

    def equip(self,weapon):
        self.g.evolutions.owned.add(weapon)
        self.g.switch_weapon(weapon,refill=True)

    def test_no_evolutions_in_normal_pool_or_nonboss_rewards(self):
        self.assertFalse({c[0] for c in EVOLUTIONS}&{c[0] for c in UPGRADES})
        with patch('weapon_evolutions.random.random',return_value=0):
            self.g.offer_upgrade(False)
        self.assertFalse(any(c[0].startswith('evo_') for c in self.g.choices))

    def test_boss_probability_boundary_and_one_offer(self):
        g=self.g
        with patch.object(g,'offer_pet_upgrade'),patch('weapon_evolutions.random.random',return_value=BOSS_EVOLUTION_CHANCE-.00001):
            g.offer_upgrade(True)
        self.assertEqual(sum(c[0].startswith('evo_') for c in g.choices),1)
        with patch.object(g,'offer_pet_upgrade'),patch('weapon_evolutions.random.random',return_value=BOSS_EVOLUTION_CHANCE):
            g.offer_upgrade(True)
        self.assertFalse(any(c[0].startswith('evo_') for c in g.choices))

    def test_pet_cannot_overwrite_rare_card_and_only_owned_weapons(self):
        g=self.g;g.unlocked_weapons={4};g.weapon_slots=[4]
        with patch('weapon_evolutions.random.random',return_value=0):
            g.offer_upgrade(True)
        self.assertEqual(g.choices[2],EVOLUTIONS[4])
        g.evolutions.owned.add(4)
        with patch('weapon_evolutions.random.random',return_value=0):
            self.assertIsNone(g.evolutions.offer(True))

    def test_acquire_once_and_block_forged_nonboss_or_locked_choice(self):
        g=self.g;g.state='upgrade';g.choices=[EVOLUTIONS[0]];g.choose_upgrade(0)
        self.assertTrue(g.evolutions.has(0));self.assertEqual(g.upgrade_stacks['evo_smg'],1)
        g.state='upgrade';g.choose_upgrade(0)
        self.assertEqual(g.upgrade_stacks['evo_smg'],1)
        g.reward_is_boss=False;g.choices=[EVOLUTIONS[1]];g.choose_upgrade(0)
        self.assertFalse(g.evolutions.has(1))
        g.reward_is_boss=True;g.unlocked_weapons={0};g.choices=[EVOLUTIONS[7]];g.choose_upgrade(0)
        self.assertFalse(g.evolutions.has(7))

    def test_smg_chains_exactly_three_unique_targets_and_los(self):
        self.equip(0);g=self.g
        primary=self.enemy(15);others=[self.enemy(16+i*.5,14.5) for i in range(4)]
        g.evolutions.gun_shot(0,[(5,primary,False)],g.damage,1000)
        self.assertEqual(sum(e[2]<10000 for e in others),3)
        self.assertEqual(primary[2],10000)
        self.assertEqual(len(g.evolutions.fx),3)
        for e in others:e[2]=10000
        with patch.object(g,'world_los',return_value=False):
            g.evolutions.gun_shot(0,[(5,primary,False)],g.damage,1000)
        self.assertTrue(all(e[2]==10000 for e in others))

    def test_shotgun_explosion_only_once_per_trigger_and_radius(self):
        self.equip(1);g=self.g;p=self.enemy(15);near=self.enemy(17.7);far=self.enemy(17.9)
        g.evolutions.gun_shot(1,[(5,p,False)]*9,g.damage,1000)
        self.assertEqual(p[2],10000-g.damage*3);self.assertEqual(near[2],p[2])
        self.assertEqual(far[2],10000);self.assertEqual(len(g.evolutions.fx),1)
        self.assertEqual(len(g.damage_popups),2)

    def test_machinegun_eighth_shot_launches_real_piercing_plasma(self):
        self.equip(2);g=self.g
        first=self.enemy(13);second=self.enemy(15)
        for _ in range(7):g.evolutions.gun_shot(2,[],g.damage,1000)
        self.assertEqual(len(g.evolutions.waves),0)
        g.evolutions.gun_shot(2,[],g.damage,1000)
        self.assertEqual(len(g.evolutions.waves),3)
        for i in range(5):g.evolutions.update(.1,1100+i*100)
        self.assertLess(first[2],10000);self.assertLess(second[2],10000)

    def test_machinegun_heat_resets_on_stop_switch_and_reload(self):
        self.equip(2);g=self.g
        for _ in range(6):g.evolutions.gun_shot(2,[],g.damage,1000)
        g.evolutions.update(.41,1410);self.assertEqual(g.evolutions.heat,0)
        g.evolutions.gun_shot(2,[],g.damage,1410);g.switch_weapon(0)
        self.assertEqual(g.evolutions.heat,0)
        g.switch_weapon(2);g.evolutions.heat=7;g.mag=1;g.reload(1500)
        self.assertEqual(g.evolutions.heat,0)

    def test_real_gun_trigger_dispatches_each_evolution_once(self):
        g=self.g
        image=pygame.Surface((100,200),pygame.SRCALPHA);image.fill('white')
        for weapon in range(4):
            self.equip(weapon);g.enemies=[];self.enemy(15);g.next_shot=0;g.reload_until=0;g.last_gun_shot=-100000
            with patch.object(g,'enemy_visual',return_value=(image,pygame.Rect(430,200,100,200))),patch.object(g,'finish_kills'),patch.object(g.evolutions,'gun_shot',wraps=g.evolutions.gun_shot) as hook:
                g.shoot(1000)
                hook.assert_called_once()
                self.assertEqual(hook.call_args.args[0],weapon)
                self.assertTrue(hook.call_args.args[1])

    def test_delayed_evolution_kill_uses_normal_kill_and_boss_reward_pipeline(self):
        self.equip(4);g=self.g;e=self.enemy(16,hp=40,kind='boss')
        g.combat.attack(1000)
        g.evolutions.update(.4,1400)
        self.assertEqual(e[2],0)
        old_kills=g.kills
        with patch.object(g,'offer_upgrade') as offer:
            g.finish_kills(1400)
            offer.assert_called_once_with(True)
        self.assertEqual(g.kills,old_kills+1)
        self.assertNotIn(e,g.enemies)

    def test_sniper_shoot_actually_penetrates_all_and_explodes(self):
        self.equip(3);g=self.g
        front=self.enemy(15);back=self.enemy(18)
        image=pygame.Surface((100,200),pygame.SRCALPHA);image.fill('white')
        with patch.object(g,'enemy_visual',return_value=(image,pygame.Rect(430,200,100,200))),patch.object(g,'finish_kills'):
            g.shoot(1000)
        self.assertEqual(front[2],10000-g.damage*1.8)
        self.assertEqual(back[2],10000-g.damage)
        self.assertEqual(g.mag,g.mag_size-1)
        self.assertTrue(any(f['kind']=='line' for f in g.evolutions.fx))

    def test_sword_wave_hits_outside_melee_range_once(self):
        self.equip(4);g=self.g;e=self.enemy(16)
        g.combat.attack(1000);self.assertEqual(e[2],10000)
        for i in range(6):g.evolutions.update(.1,1100+i*100)
        self.assertEqual(e[2],10000-g.damage*.9)

    def test_sword_wave_cannot_tunnel_through_wall(self):
        self.equip(4);g=self.g;g.terrain_cells={(12,14)};e=self.enemy(14)
        g.combat.attack(1000);g.evolutions.update(1,2000)
        self.assertEqual(e[2],10000);self.assertEqual(g.evolutions.waves,[])

    def test_boomerang_triples_no_duplicates_and_returns(self):
        self.equip(5);g=self.g
        g.combat.attack(1000);self.assertEqual(len(g.combat.throws),3)
        self.assertEqual(sorted(s['damage'] for s in g.combat.throws),[g.damage*.7,g.damage*.7,g.damage])
        shot=g.combat.throws[0];angle=shot['angle'];import math
        # First tick's side blade position, swept collision must damage it.
        from rogue_content import WEAPONS
        reach=WEAPONS[5]['range']*math.sin(math.pi*.1/1.2);curve=2*math.sin(2*math.pi*.1/1.2)
        e=self.enemy(10+math.cos(angle)*reach-math.sin(angle)*curve,
                     14+math.sin(angle)*reach+math.cos(angle)*curve)
        g.combat.update(.1,1100);self.assertLess(e[2],10000)
        g.combat.attack(1600);self.assertEqual(len(g.combat.throws),3)
        g.combat.update(.1,2300);self.assertEqual(g.combat.throws,[])

    def test_spear_contact_creates_one_persistent_damage_field(self):
        self.equip(6);g=self.g;e=self.enemy(12.2);near=self.enemy(12.2,15.8)
        g.combat.attack(1000);g.combat.update(.2,1200)
        self.assertEqual(len(g.evolutions.fields),1)
        self.assertAlmostEqual(g.evolutions.fields[0]['pos'][0],12.2)
        g.evolutions.update(.01,1210);hp=near[2];self.assertLess(hp,10000)
        g.evolutions.update(.25,1460);self.assertEqual(near[2],hp)
        g.evolutions.update(.26,1720);self.assertLess(near[2],hp)
        for i in range(40):g.evolutions.update(.1,1800+i*100)
        self.assertEqual(g.evolutions.fields,[])

    def test_spear_max_range_still_creates_field_on_miss(self):
        self.equip(6);g=self.g;g.combat.attack(1000)
        for i in range(1,12):g.combat.update(.1,1000+i*100)
        self.assertEqual(len(g.evolutions.fields),1)

    def test_dagger_echo_delayed_damage_kill_refund_and_reset(self):
        self.equip(7);g=self.g;e=self.enemy(12,hp=300)
        g.combat.attack(1000);hp=e[2];self.assertEqual(hp,300-g.damage)
        self.assertEqual(g.stamina,72)
        g.evolutions.update(.29,1290);self.assertEqual(e[2],hp)
        g.evolutions.update(.02,1310);self.assertEqual(e[2],0)
        self.assertEqual(g.stamina,86);self.assertEqual(g.combat.cooldown,1310)
        g.evolutions.update(.5,1810);self.assertEqual(g.stamina,86)

    def test_dagger_no_stamina_no_sound_no_cooldown_no_echo(self):
        self.equip(7);g=self.g;g.stamina=0;origin=g.player.copy()
        with patch.object(g,'sound') as sound:
            g.combat.attack(1000);sound.assert_not_called()
        self.assertEqual(g.player,origin);self.assertEqual(g.combat.cooldown,0)
        self.assertFalse(g.evolutions.echoes)

    def test_pause_does_not_advance_evolution_events(self):
        self.equip(4);g=self.g;g.combat.attack(1000)
        clock=g.evolutions.clock;waves=len(g.evolutions.waves)
        g.state='paused';g.update(20,21000)
        self.assertEqual(g.evolutions.clock,clock);self.assertEqual(len(g.evolutions.waves),waves)

    def test_new_wave_clears_events_but_keeps_ownership(self):
        self.equip(4);g=self.g;g.combat.attack(1000)
        g.spawn_wave();self.assertTrue(g.evolutions.has(4));self.assertEqual(g.evolutions.waves,[])

    def test_all_generated_cards_and_reward_rendering(self):
        g=self.g
        for card in EVOLUTIONS:
            self.assertIn('icon_'+card[0],g.cloud_art.images)
            g.state='upgrade';g.choices=[card,UPGRADES[0],UPGRADES[1]];g.draw()
            self.assertEqual(g.upgrade_card_rect(0).height,290)
        for i in range(8):
            self.equip(i);g.state='playing';g.evolutions.draw(g.screen)


if __name__=='__main__':unittest.main()
