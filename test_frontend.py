"""Front-end regressions: continue/new game, achievements, settings, keys, fullscreen."""
import os
os.environ.setdefault('SDL_VIDEODRIVER', 'dummy')
os.environ.setdefault('SDL_AUDIODRIVER', 'dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game


class FrontendTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): cls.g = Game(muted=True)
    @classmethod
    def tearDownClass(cls): pygame.quit()

    def setUp(self):
        g = self.g
        g.state = 'menu'; g.now = 1000; g.menu_focus = 0; g.waiting_key = None
        g.quit_requested = False; g.frontend_message = ''
        g.profile['save'] = None; g.profile['achievements'] = {}
        g.kills = 0; g.level = 1; g.wave = 1; g.flawless_waves = 0; g.damage_this_wave = False
        g.horizontal_sensitivity = 1.0; g.vertical_sensitivity = 1.0
        g.ads_sensitivity = .6; g.ads = False; g.settings['fps_cap'] = 0

    # --- menu / continue ---------------------------------------------
    def test_menu_without_save_only_offers_new_game(self):
        actions = [action for action, _, _ in self.g.menu_buttons()]
        self.assertNotIn('continue', actions)
        self.assertEqual(actions[0], 'new')

    def test_menu_with_save_offers_continue_first(self):
        self.g.profile['save'] = {'wave': 4, 'level': 7, 'kills': 30}
        actions = [action for action, _, _ in self.g.menu_buttons()]
        self.assertEqual(actions[:2], ['continue', 'new'])

    def test_run_snapshot_round_trip(self):
        g = self.g; g.wave = 7; g.level = 9; g.hp = 66; g.shield = 12
        g.unlocked_weapons = {0, 2}; g.weapon_slots = [0, 2]; g.weapon_index = 2
        g.upgrade_stacks = {'power': 3}; g.flawless_waves = 2
        snap = g.snapshot_run()
        g.wave = 1; g.level = 1; g.hp = 100; g.shield = 0
        g.unlocked_weapons = {0}; g.weapon_slots = [0]; g.weapon_index = 0
        g.upgrade_stacks = {}; g.flawless_waves = 0
        g.load_run_snapshot(snap)
        self.assertEqual(g.wave, 7); self.assertEqual(g.level, 9)
        self.assertEqual(g.hp, 66); self.assertEqual(g.shield, 12)
        self.assertEqual(g.unlocked_weapons, {0, 2}); self.assertEqual(g.weapon_slots, [0, 2])
        self.assertEqual(g.weapon_index, 2); self.assertEqual(g.upgrade_stacks, {'power': 3})
        self.assertEqual(g.flawless_waves, 2)

    def test_continue_restores_wave_and_starts_countdown(self):
        g = self.g
        g.profile['save'] = {'wave': 6, 'level': 11, 'hp': 55, 'max_hp': 100,
                             'unlocked_weapons': [0, 2], 'weapon_slots': [0, 2],
                             'weapon_index': 2, 'upgrade_stacks': {'power': 2}}
        g.continue_game()
        self.assertEqual(g.wave, 6)
        self.assertEqual(g.level, 11)
        self.assertEqual(g.hp, 55)
        self.assertEqual(g.state, 'wave')
        self.assertTrue(g.has_run_save())

    def test_start_new_game_clears_old_save(self):
        g = self.g
        g.profile['save'] = {'wave': 9}
        g.start_new_game()
        self.assertEqual(g.wave, 1)
        self.assertEqual(g.state, 'wave')
        self.assertIsNotNone(g.profile['save'])
        self.assertEqual(g.profile['save']['wave'], 1)

    def test_death_clears_continue_save(self):
        g = self.g; g.profile['save'] = {'wave': 3}
        g.clear_run_save()
        self.assertIsNone(g.profile['save'])

    # --- achievements -------------------------------------------------
    def test_achievement_unlocks_once_and_sets_toast(self):
        g = self.g
        self.assertTrue(g.unlock_achievement('first_kill'))
        self.assertIn('first_kill', g.profile['achievements'])
        self.assertEqual(g.achievement_toast[0], 'first_kill')
        self.assertFalse(g.unlock_achievement('first_kill'))

    def test_kill_stats_and_achievements_accumulate(self):
        g = self.g
        enemy = [18., 14., 0, 0, 100., 'normal', 0]
        g.enemies = [enemy]; g.kill_methods[id(enemy)] = 'headshot'
        g.finish_kills(1000)
        stats = g.profile['stats']
        self.assertEqual(stats['total_kills'], 1)
        self.assertEqual(stats['total_headshots'], 1)
        self.assertIn('first_kill', g.profile['achievements'])

    def test_flawless_waves_increment_and_reset(self):
        g = self.g; g.wave = 2
        g.damage_this_wave = False; g.flawless_waves = 0
        g.begin_wave(persist=False); self.assertEqual(g.flawless_waves, 1)
        g.begin_wave(persist=False); self.assertEqual(g.flawless_waves, 2)
        g.damage_this_wave = True
        g.begin_wave(persist=False); self.assertEqual(g.flawless_waves, 0)

    def test_flawless_achievement_at_three_waves(self):
        g = self.g; g.flawless_waves = 3
        g.check_achievements()
        self.assertIn('flawless_3', g.profile['achievements'])

    # --- settings / volume / keys -------------------------------------
    def test_volume_is_clamped_and_stored(self):
        g = self.g
        g.set_music_volume(1.7); self.assertEqual(g.music_volume, 1.0)
        g.set_sfx_volume(-.4); self.assertEqual(g.sfx_volume, 0.0)
        self.assertEqual(g.settings['music_volume'], 1.0)
        self.assertEqual(g.settings['sfx_volume'], 0.0)

    def test_key_rebind_swaps_conflicting_action(self):
        g = self.g
        g.keys = dict(g.keys)
        g.keys['forward'] = pygame.K_w; g.keys['jump'] = pygame.K_SPACE
        g.bind_key('jump', pygame.K_w)
        self.assertEqual(g.keys['jump'], pygame.K_w)
        self.assertEqual(g.keys['forward'], pygame.K_SPACE)

    def test_key_rebind_rejects_unusable_code(self):
        g = self.g; before = g.keys['jump']
        g.bind_key('jump', 900000)
        self.assertEqual(g.keys['jump'], before)
        self.assertIn('不支持', g.frontend_message)

    def test_reset_settings_restores_defaults(self):
        g = self.g
        g.keys['jump'] = pygame.K_t; g.set_music_volume(1.0); g.set_sfx_volume(0.0)
        g.reset_settings()
        self.assertEqual(g.keys['jump'], pygame.K_SPACE)
        self.assertAlmostEqual(g.music_volume, .3)
        self.assertAlmostEqual(g.sfx_volume, .7)

    def test_sensitivity_is_clamped_and_stored(self):
        g = self.g
        g.set_sensitivity('horizontal_sensitivity', 9)
        self.assertEqual(g.horizontal_sensitivity, 2.0)
        g.set_sensitivity('vertical_sensitivity', 0)
        self.assertEqual(g.vertical_sensitivity, .1)
        g.set_sensitivity('ads_sensitivity', .55)
        self.assertAlmostEqual(g.ads_sensitivity, .55)
        self.assertEqual(g.settings['ads_sensitivity'], .55)
        g.set_sensitivity('missing_key', 1)  # unknown keys are ignored safely

    def test_mouse_look_uses_horizontal_vertical_and_ads(self):
        g = self.g; g.angle = 0.0; g.pitch = 0.0; g.ads = False
        g.horizontal_sensitivity = 2.0; g.vertical_sensitivity = .5; g.ads_sensitivity = .4
        g.apply_mouse_look(10, 10)
        self.assertAlmostEqual(g.angle, 10 * .0025 * 2.0)
        self.assertAlmostEqual(g.pitch, -10 * .002 * .5)
        base = g.angle; g.ads = True
        g.apply_mouse_look(10, 0)
        self.assertAlmostEqual(g.angle - base, 10 * .0025 * 2.0 * .4)

    def test_fps_cap_cycle_and_auto_floor(self):
        g = self.g; g.settings['fps_cap'] = 0
        self.assertGreaterEqual(g._resolve_fps_cap(0), 120)
        for _ in range(7): g.cycle_fps_cap()
        self.assertEqual(g.settings['fps_cap'], 0)
        self.assertEqual(g._resolve_fps_cap(144), 144)
        self.assertEqual(g._resolve_fps_cap(240), 240)

    def test_reset_settings_restores_sensitivity_and_fps(self):
        g = self.g
        g.set_sensitivity('horizontal_sensitivity', 2)
        g.ads_sensitivity = .2
        g.settings['fps_cap'] = 240; g.fps_cap = 240
        g.reset_settings()
        self.assertEqual(g.horizontal_sensitivity, 1.0)
        self.assertAlmostEqual(g.ads_sensitivity, .6)
        self.assertEqual(g.settings['fps_cap'], 0)
        self.assertGreaterEqual(g.fps_cap, 120)

    def test_settings_click_sets_horizontal_sensitivity(self):
        g = self.g; g.state = 'settings'
        rect = g.settings_hitboxes()['horizontal']
        g.click_settings((rect.right - 1, rect.centery))
        self.assertAlmostEqual(g.horizontal_sensitivity, 2.0, delta=.02)

    def test_fullscreen_toggle_updates_state(self):
        g = self.g
        start = g.fullscreen
        # The dummy SDL driver cannot open a real fullscreen window, so the
        # mode switch itself is stubbed while the state/persistence path is tested.
        with patch.object(g, '_apply_display_mode', return_value=g.screen):
            g.toggle_fullscreen()
            self.assertNotEqual(g.fullscreen, start)
            self.assertEqual(g.settings['fullscreen'], g.fullscreen)
            g.toggle_fullscreen(start)
            self.assertEqual(g.fullscreen, start)

    def test_present_letterboxes_with_black_bars(self):
        g = self.g
        fake = pygame.Surface((1280, 720)); fake.fill((255, 255, 255))
        with patch.object(g, 'window', fake):
            g.screen.fill((20, 40, 60))
            g.present()
        self.assertEqual(fake.get_at((1, 1))[:3], (0, 0, 0))
        self.assertNotEqual(fake.get_at((640, 360))[:3], (0, 0, 0))

    def test_to_logical_maps_scaled_pointer(self):
        g = self.g
        fake = pygame.Surface((1920, 1080))
        with patch.object(g, 'window', fake):
            self.assertEqual(g.to_logical((96, 0)), (0, 0))
            self.assertEqual(g.to_logical((96 + 864, 540)), (480, 300))

    # --- interaction ---------------------------------------------------
    def test_menu_enter_starts_a_run(self):
        g = self.g
        g.handle_frontend_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_RETURN))
        self.assertEqual(g.state, 'wave')
        self.assertTrue(g.has_run_save())

    def test_escape_returns_settings_to_menu(self):
        g = self.g; g.state = 'settings'
        g.handle_frontend_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertEqual(g.state, 'menu')

    def test_settings_click_selects_key_binding(self):
        g = self.g; g.state = 'settings'
        rect = g.settings_hitboxes()['key_jump']
        g.handle_frontend_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=rect.center))
        self.assertEqual(g.waiting_key, 'jump')

    def test_achievements_back_button_returns(self):
        g = self.g; g.state = 'achievements'
        g.handle_frontend_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1,
                                                   pos=g.achievements_back_rect().center))
        self.assertEqual(g.state, 'menu')

    def test_all_frontend_pages_draw(self):
        for state in ('menu', 'settings', 'achievements'):
            self.g.state = state
            self.g.draw()


if __name__ == '__main__': unittest.main()