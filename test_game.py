"""Release regressions. Run: py -m unittest -v test_game (no window/audio needed)."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
os.environ.setdefault('PYGAME_HIDE_SUPPORT_PROMPT', '1')
import random
import math
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game, bullet_hits_player, ray_wall_distance, make_sounds, load_font, W, H, FOV
from rogue_content import UPGRADES, WEAPONS


class GameRegressionTests(unittest.TestCase):
    def test_draw_near_weapon_crate(self):
        self.g.player=[18.5,20.5]
        self.g.angle=0
        self.g.draw()

    @classmethod
    def setUpClass(cls):
        random.seed(123)
        cls.game = Game()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def setUp(self):
        self.g = self.game
        self.g.reset()
        self.g.state = 'playing'
        self.g.enemies = []

    def enemy(self, x=18., y=14., hp=1000, kind='normal'):
        return [x, y, hp, 0, hp, kind, 100000]

    def test_swept_bullet_direct_hit_and_near_miss(self):
        self.assertTrue(bullet_hits_player((0, 0), (2, 0), (1, 0), (1, 0)))
        self.assertFalse(bullet_hits_player((0, .3), (2, .3), (1, 0), (1, 0)))
        self.assertTrue(bullet_hits_player((0, 0), (2, 0), (1, 1), (1, -1)))

    def test_dda_matches_analytic_arena_intersection(self):
        rng = random.Random(881)
        for _ in range(300):
            x,y=rng.uniform(1.2,26.8),rng.uniform(1.2,26.8)
            angle=rng.uniform(-math.pi,math.pi)
            dx,dy=math.cos(angle),math.sin(angle)
            distances=[(27-x)/dx if dx>0 else (1-x)/dx,
                       (27-y)/dy if dy>0 else (1-y)/dy]
            self.assertAlmostEqual(ray_wall_distance(x,y,dx,dy)[0], min(distances), places=9)
        self.assertEqual(ray_wall_distance(14,14,1,0)[0],13)
        self.assertEqual(ray_wall_distance(14,14,0,-1)[0],13)

    def test_zoom_projection_agrees_with_view_fov_edge(self):
        self.g.unlocked_weapons.add(3)
        self.g.switch_weapon(3)
        for ads,zoom in ((False,1),(True,2.5)):
            self.g.ads=ads
            edge=math.atan(math.tan(FOV/2)/zoom)
            point=self.g.project(14+5*math.cos(edge),14+5*math.sin(edge))
            self.assertLessEqual(abs(point[0]-W),1)

    def test_tracer_pitch_remains_aligned_to_crosshair(self):
        for pitch in (-.35,0,.35):
            self.g.pitch=pitch
            point=self.g.project(19,14,pitch*5*(.72/.55))
            self.assertLessEqual(abs(point[1]-H//2),1)

    def test_movement_and_boundary_do_not_tunnel(self):
        self.g.move(1, 0)
        self.assertAlmostEqual(self.g.player[0], 15)
        self.g.move(-100, 0)
        self.assertGreaterEqual(self.g.player[0], 1.18)

    def test_new_wave_clears_bullets_traces_and_attack_effects(self):
        self.g.projectiles = [[14,14,1,0,5,9999]]
        self.g.tracers = [[1]]
        self.g.effects = {1:(100, 4)}
        self.g.attack_animations = {1:('fire',100)}
        self.g.spawn_wave()
        for values in (self.g.projectiles, self.g.tracers, self.g.effects, self.g.attack_animations):
            self.assertFalse(values)

    def test_boss_and_ranged_population(self):
        for wave in (1, 5, 10, 20, 100):
            self.g.enemies = []
            self.g.wave = wave
            self.g.spawn_wave()
            kinds = [e[5] for e in self.g.enemies]
            self.assertEqual(kinds.count('boss'), int(wave % 5 == 0))
            self.assertLessEqual(kinds.count('shooter'), 4)
            self.assertGreater(sum(k in ('normal','runner','elite') for k in kinds), len(kinds)/2)

    def test_ammo_station_distance_and_cap(self):
        self.g.reserve = 0
        self.g.refill_reserve()
        self.assertEqual(self.g.reserve, 0)
        self.g.player = list(self.g.ammo_station)
        self.g.refill_reserve()
        self.assertEqual(self.g.reserve, self.g.reserve_max)
        self.g.extras['blue_supply'] = 8
        self.g.enemies = [self.enemy(hp=0), self.enemy()]
        self.g.finish_kills(0)
        self.assertEqual(self.g.reserve, self.g.reserve_max)

    def test_shot_miss_and_opaque_hit(self):
        e = self.enemy()
        self.g.enemies = [e]
        self.g.angle = 1.3
        self.g.shoot(1000)
        self.assertEqual(e[2], 1000)
        self.g.angle = 0
        self.g.next_shot = 0
        self.g.shoot(2000)
        self.assertLess(e[2], 1000)

    def test_contact_enemy_does_not_block_distant_aim(self):
        close, distant = self.enemy(x=14.5), self.enemy(x=18)
        self.g.enemies = [close, distant]
        self.g.shoot(1000)
        self.assertLess(distant[2], 1000)

    def test_locked_weapon_cannot_equip_and_unlock_names_specific_weapon(self):
        self.g.switch_weapon(3)
        self.assertEqual(self.g.weapon_index, 0)
        self.g.state = 'upgrade'
        self.g.choices = [('unlock3', '解锁·狙击枪', '', 1, 1)]
        self.g.choose_upgrade(0)
        self.assertIn(3, self.g.unlocked_weapons)
        self.assertEqual(self.g.weapon_index, 3)
        self.assertEqual(self.g.damage, WEAPONS[3]['damage'])

    def test_upgrade_pool_does_not_offer_locked_weapon_specials(self):
        forbidden = {'pellets','shot_power','shot_tight','mg_power','mg_reload','sniper_power','sniper_haste'}
        for _ in range(100):
            self.g.offer_upgrade()
            self.assertFalse(forbidden.intersection(u[0] for u in self.g.choices))
            self.assertEqual(len({u[0] for u in self.g.choices}),3)

    def test_reload_transfers_ammo_once(self):
        self.g.enemies = [self.enemy()]
        self.g.mag = 2
        self.g.reserve = 10
        self.g.reload(0)
        self.g.update(.01, self.g.reload_duration+1)
        self.assertEqual((self.g.mag, self.g.reserve), (12,0))
        self.g.update(.01, self.g.reload_duration+2)
        self.assertEqual((self.g.mag, self.g.reserve), (12,0))

    def test_selecting_current_weapon_preserves_reload(self):
        self.g.mag = 2
        self.g.reload(100)
        deadline = self.g.reload_until
        self.g.switch_weapon(0)
        self.assertEqual(self.g.reload_until, deadline)

    def test_stat_upgrade_preserves_reload(self):
        self.g.mag = 2
        self.g.reload(100)
        self.g.state = 'upgrade'
        self.g.choices = [('power','伤害','','0',1)]
        self.g.choose_upgrade(0)
        self.assertGreater(self.g.reload_until, 0)

    def test_boss_reward_does_not_get_downgraded_by_unlock(self):
        counts = [0,0,0,0]
        random.seed(615)
        for _ in range(600):
            self.g.offer_upgrade(True)
            for choice in self.g.choices:
                counts[choice[3]] += 1
        self.assertGreaterEqual((counts[2]+counts[3])/sum(counts), .93)

    def test_dead_dot_enemy_cannot_fire(self):
        corpse = self.enemy(x=14.4, hp=1, kind='shooter')
        corpse[6] = 0
        self.g.enemies = [corpse, self.enemy()]
        self.g.effects[id(corpse)] = (5000, 1000)
        self.g.update(.05, 100)
        self.assertFalse(self.g.projectiles)
        self.assertEqual(self.g.hp, 100)

    def test_empty_shot_does_not_postpone_wave_transition(self):
        self.g.wave_wait = 1100
        self.g.shoot(1050)
        self.assertEqual(self.g.wave_wait, 1100)

    def test_killed_enemy_effect_state_is_removed(self):
        e = self.enemy(hp=0)
        self.g.enemies = [e, self.enemy()]
        self.g.effects[id(e)] = (9999, 5)
        self.g.attack_animations[id(e)] = ('melee', 9999)
        self.g.finish_kills(100)
        self.assertNotIn(id(e), self.g.effects)
        self.assertNotIn(id(e), self.g.attack_animations)

    def test_extreme_shotgun_stacks_are_bounded(self):
        self.g.unlocked_weapons.add(1)
        self.g.extras['pellets']=10000
        self.g.mag_bonus=10000
        self.g.rate_bonus=10000
        self.g.reload_bonus=10000
        self.g.switch_weapon(1)
        self.assertLessEqual(self.g.mag_size,500)
        self.assertGreaterEqual(self.g.fire_delay,35)
        self.assertGreaterEqual(self.g.reload_duration,250)
        self.g.enemies=[self.enemy()]
        with patch.object(self.g,'enemy_visual', wraps=self.g.enemy_visual) as visual:
            self.g.shoot(1000)
        self.assertLessEqual(visual.call_count,64)

    def test_attack_decoration_is_visible_but_not_hittable(self):
        e=self.enemy()
        self.g.enemies=[e]
        for shot_index,animation in enumerate(('melee','swing','fire')):
            self.g.attack_animations[id(e)]=(animation,5000)
            image,rect=self.g.enemy_visual(e)
            hit_image,hit_rect=self.g.enemy_visual(e,hit_test=True)
            self.assertEqual(rect,hit_rect)
            visible=pygame.mask.from_surface(image)
            body=pygame.mask.from_surface(hit_image)
            decorations=visible.copy()
            decorations.erase(body,(0,0))
            self.assertGreater(decorations.count(),0)
            # Aim at a decoration-only pixel and check shoot() uses the body mask.
            points=decorations.outline()
            px,py=points[len(points)//2]
            fake_rect=rect.copy()
            fake_rect.x=W//2-px
            fake_rect.y=H//2-py
            e[2]=1000
            self.g.next_shot=0
            with patch.object(self.g,'enemy_visual',return_value=(hit_image,fake_rect)) as visual:
                self.g.shoot(1000+shot_index*100)
            self.assertEqual(e[2],1000)
            self.assertTrue(visual.call_args.kwargs.get('hit_test'))

    def test_wave_pause_freezes_countdown_and_ads_clears(self):
        self.g.begin_wave()
        self.g.ads = True
        with patch('pygame.time.get_ticks', return_value=100):
            self.g.wave_deadline = 3100
            self.g.pause()
        self.assertEqual(self.g.state, 'paused')
        self.assertFalse(self.g.ads)
        with patch('pygame.time.get_ticks', return_value=5000):
            self.g.resume()
        self.assertEqual(self.g.state, 'wave')
        self.assertEqual(self.g.wave_deadline, 8000)

    def test_reset_preserves_mute_and_clears_run_progress(self):
        self.g.muted = True
        self.g.unlocked_weapons.add(3)
        self.g.upgrade_stacks['power'] = 7
        self.g.wave = 15
        self.g.reset()
        self.assertTrue(self.g.muted)
        self.assertEqual(self.g.wave, 1)
        self.assertEqual(self.g.unlocked_weapons, {0})
        self.assertFalse(self.g.upgrade_stacks)

    def test_unfocused_upgrade_choice_stays_paused(self):
        self.g.state = 'upgrade'
        self.g.focused = False
        self.g.choices = [('power','伤害','',0,1)]
        self.g.choose_upgrade(0)
        self.assertEqual(self.g.state, 'paused')
        self.assertFalse(pygame.event.get_grab())

    def test_all_upgrades_apply_and_draw_without_crash(self):
        self.g.unlocked_weapons = set(range(4))
        for upgrade in UPGRADES:
            self.g.state = 'upgrade'
            self.g.choices = [upgrade]
            self.g.choose_upgrade(0)
        self.g.draw()
        self.assertGreater(self.g.max_hp, 100)

    def test_draw_all_states_weapons_and_close_projectile(self):
        self.g.unlocked_weapons = set(range(4))
        self.g.enemies = [self.enemy(kind=k, x=17+i) for i,k in enumerate(('normal','runner','shooter','elite','boss'))]
        self.g.projectiles = [[14.2,14,1,0,5,9999]]
        self.g.offer_upgrade(True)
        for weapon in range(4):
            self.g.switch_weapon(weapon)
            for state in ('wave','playing','paused','upgrade','lost'):
                self.g.state = state
                self.g.draw()

    def test_quit_event_exits_run(self):
        pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
        self.g.run()
        self.assertFalse(pygame.get_init())
        pygame.init()

    def run_events(self, *events):
        pygame.event.clear()
        for event in events:
            pygame.event.post(event)
        pygame.event.post(pygame.event.Event(pygame.QUIT))
        self.g.run()
        pygame.init()

    def test_menu_enter_starts_countdown(self):
        self.g.state = 'menu'
        self.run_events(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(self.g.state, 'wave')

    def test_focus_loss_and_escape_cannot_resume_background(self):
        self.run_events(pygame.event.Event(pygame.WINDOWFOCUSLOST),
                        pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(self.g.state, 'paused')
        self.assertFalse(self.g.focused)

    def test_paused_r_restarts(self):
        self.g.state = 'paused'
        self.g.wave = 7
        self.run_events(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_r))
        self.assertEqual(self.g.state, 'wave')
        self.assertEqual(self.g.wave, 1)

    def test_actual_keyboard_weapon_switch(self):
        self.g.acquire_weapon(2)
        self.g.switch_slot(0)
        self.run_events(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2))
        self.assertEqual(self.g.weapon_index, 2)

    def test_weapon_slots_follow_acquisition_order_and_cap(self):
        self.assertEqual(self.g.weapon_slots,[0])
        self.assertTrue(self.g.acquire_weapon(3))
        self.assertTrue(self.g.acquire_weapon(1))
        self.assertEqual(self.g.weapon_slots,[0,3,1])
        self.assertFalse(self.g.acquire_weapon(2))
        self.assertFalse(self.g.acquire_weapon(1))
        self.assertEqual(self.g.weapon_slots,[0,3,1])
        self.g.switch_slot(1)
        self.assertEqual(self.g.weapon_index,3)
        self.g.switch_slot(2)
        self.assertEqual(self.g.weapon_index,1)
        self.g.switch_slot(8)
        self.assertEqual(self.g.weapon_index,1)

    def test_full_slots_do_not_offer_unlock_cards(self):
        self.g.acquire_weapon(3)
        self.g.acquire_weapon(1)
        for _ in range(100):
            self.g.offer_upgrade()
            self.assertFalse(any(u[0].startswith('unlock') for u in self.g.choices))

    def test_four_key_no_longer_switches_gun(self):
        self.g.acquire_weapon(3)
        self.g.switch_slot(0)
        self.run_events(pygame.event.Event(pygame.KEYDOWN,key=pygame.K_4))
        self.assertEqual(self.g.weapon_index,0)

    def test_run_exception_releases_pygame(self):
        pygame.event.clear()
        with patch.object(self.g,'draw',side_effect=RuntimeError('injected render failure')):
            with self.assertRaisesRegex(RuntimeError,'injected'):
                self.g.run()
        self.assertFalse(pygame.get_init())
        pygame.init()

    def test_missing_audio_device_is_supported(self):
        with patch('pygame.mixer.get_init',return_value=None), patch('pygame.mixer.init',side_effect=pygame.error('no device')):
            self.assertEqual(make_sounds(), {})

    def test_font_file_failure_falls_back_to_builtin(self):
        real_font=pygame.font.Font
        def fake_font(path,size):
            if path is not None:
                raise pygame.error('bad font')
            return real_font(path,size)
        with patch('pathlib.Path.is_file',return_value=True), patch('pygame.font.Font',side_effect=fake_font):
            font=load_font(20)
        self.assertGreater(font.size('Release')[0],0)

    def test_weapon_sounds_have_distinct_samples(self):
        sounds=make_sounds()
        weapon_sounds=[sounds[f'shot{i}'] for i in range(4)]
        self.assertEqual(len({sound.get_raw() for sound in weapon_sounds}),4)
        self.assertEqual(len({round(sound.get_length(),3) for sound in weapon_sounds}),4)

    def test_reload_completion_and_pause_do_not_advance_world(self):
        self.g.enemies=[self.enemy()]
        self.g.mag=0
        self.g.reload(100)
        reserve=self.g.reserve
        self.g.pause()
        self.g.update(10,100000)
        self.assertEqual(self.g.mag,0)
        self.assertEqual(self.g.reserve,reserve)

    def test_dead_player_cannot_regenerate_or_advance_wave(self):
        self.g.hp=0
        self.g.regen=100
        self.g.wave_wait=50
        self.g.update(1,100)
        self.assertEqual(self.g.state,'lost')
        self.assertEqual(self.g.wave,1)
        self.assertEqual(self.g.hp,0)

    def test_dot_kill_and_fatal_bullet_same_frame_keeps_death_screen(self):
        e=self.enemy(hp=1)
        self.g.enemies=[e]
        self.g.effects[id(e)]=(5000,1000)
        self.g.hp=1
        self.g.projectiles=[[13.95,14,5,0,10,5000]]
        self.g.update(.02,100)
        self.assertEqual(self.g.state,'lost')
        self.assertEqual(self.g.hp,0)

    def test_paused_right_click_cannot_enable_ads(self):
        self.g.state='paused'
        self.run_events(pygame.event.Event(pygame.MOUSEBUTTONDOWN,button=3,pos=(480,300)))
        self.assertFalse(self.g.ads)


if __name__ == '__main__':
    unittest.main()
