"""Persistent player profile: run snapshot, achievements, stats and settings.

Machine-readable JSON lives next to the game (or next to the exe when frozen)
so a run survives closing the window. Corrupt files fall back to defaults.
"""
import json
import os
import sys
from pathlib import Path

import pygame

SAVE_VERSION = 1


def _application_dir():
    """Frozen builds store the profile next to the exe, not in the temp bundle."""
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


SAVE_PATH = _application_dir() / 'profile.json'

ACHIEVEMENTS = (
    ('first_kill', '初试锋芒', '击杀第一个敌人'),
    ('first_upgrade', '强化开始', '完成第一次强化选择'),
    ('first_boss', '首领终结者', '击败第一个 Boss'),
    ('wave_10', '深潜十层', '单局到达第 10 波'),
    ('kills_50', '杀戮机器', '单局击杀 50 个敌人'),
    ('headshots_25', '神枪手', '累计爆头 25 次'),
    ('melee_15', '近身大师', '累计近战击杀 15 次'),
    ('flawless_3', '毫发无伤', '连续 3 波没有受到伤害'),
    ('arsenal', '军火库', '同时解锁 3 把武器'),
    ('max_level', '极限强化', '单局等级达到 20'),
)
ACHIEVEMENT_KEYS = tuple(item[0] for item in ACHIEVEMENTS)
ACHIEVEMENT_BY_KEY = {item[0]: item for item in ACHIEVEMENTS}

DEFAULT_KEYS = {
    'forward': pygame.K_w, 'back': pygame.K_s, 'left': pygame.K_a, 'right': pygame.K_d,
    'jump': pygame.K_SPACE, 'sprint': pygame.K_LSHIFT,
    'reload': pygame.K_r, 'refill': pygame.K_f, 'pause': pygame.K_ESCAPE,
}
KEY_LABELS = {
    'forward': '前进', 'back': '后退', 'left': '左移', 'right': '右移',
    'jump': '跳跃', 'sprint': '冲刺', 'reload': '换弹', 'refill': '补给',
    'pause': '暂停',
}


def default_profile():
    return {
        'version': SAVE_VERSION,
        'save': None,
        'achievements': {},
        'stats': {
            'best_wave': 0, 'total_kills': 0, 'total_headshots': 0,
            'total_melee': 0, 'total_bosses': 0, 'runs': 0,
        },
        'settings': {
            'music_volume': .3, 'sfx_volume': .7, 'fullscreen': False,
            'horizontal_sensitivity': 1.0, 'vertical_sensitivity': 1.0,
            'ads_sensitivity': .6, 'fps_cap': 0,
            'keys': dict(DEFAULT_KEYS),
        },
    }


def default_path():
    """Tests run headless; they must never overwrite a real player profile."""
    if os.environ.get('SDL_VIDEODRIVER') == 'dummy':
        return False
    return SAVE_PATH


def load_profile(path=None):
    if path is False:
        return default_profile()
    path = SAVE_PATH if path is None else Path(path)
    profile = default_profile()
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except (OSError, ValueError):
        return profile
    if not isinstance(data, dict):
        return profile
    if isinstance(data.get('save'), dict):
        profile['save'] = data['save']
    unlocked = data.get('achievements')
    if isinstance(unlocked, dict):
        profile['achievements'] = {k: True for k in ACHIEVEMENT_KEYS if unlocked.get(k)}
    stats = data.get('stats')
    if isinstance(stats, dict):
        for key in profile['stats']:
            value = stats.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                profile['stats'][key] = value
    settings = data.get('settings')
    if isinstance(settings, dict):
        for key in ('music_volume', 'sfx_volume'):
            value = settings.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                profile['settings'][key] = max(0.0, min(1.0, float(value)))
        if isinstance(settings.get('fullscreen'), bool):
            profile['settings']['fullscreen'] = settings['fullscreen']
        for key, low, high in (('horizontal_sensitivity', .1, 2.0),
                               ('vertical_sensitivity', .1, 2.0),
                               ('ads_sensitivity', .1, 1.0)):
            value = settings.get(key)
            if isinstance(value, (int, float)) and not isinstance(value, bool):
                profile['settings'][key] = max(low, min(high, float(value)))
        fps_cap = settings.get('fps_cap')
        if isinstance(fps_cap, int) and not isinstance(fps_cap, bool) and \
                fps_cap in (0, 60, 90, 120, 144, 165, 240):
            profile['settings']['fps_cap'] = fps_cap
        keys = settings.get('keys')
        if isinstance(keys, dict):
            for action in DEFAULT_KEYS:
                value = keys.get(action)
                if isinstance(value, int) and 0 <= value < 512:
                    profile['settings']['keys'][action] = value
    return profile


def save_profile(profile, path=None):
    if path is False:
        return False
    path = SAVE_PATH if path is None else Path(path)
    try:
        path.write_text(json.dumps(profile, ensure_ascii=False, indent=2), encoding='utf-8')
        return True
    except OSError:
        return False