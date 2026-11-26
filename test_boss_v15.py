"""Readable hunter identity and move-dodgeable judge laser arena."""
import math
import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game


class BossV15Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.g=Game(muted=True)

    @classmethod
    def tearDownClass(cls):pygame.quit()

    def setUp(self):
        g=self.g;g.state='playing';g.wave=15;g.player=[14.,14.];g.z=0
        g.hp=g.max_hp=100;g.shield=0;g.terrain_cells=set();g.projectiles=[]
        g.combat.boss_pattern.clear();g.combat.boss_cycles.clear();g.combat.boss_impacts=[]
        self.boss=[10.,14.,1000.,0,1000.,'boss',999999];g.enemies=[self.boss]

    def laser(self,enraged=False):
        if enraged:self.boss[2]=400
        self.g.combat.boss_attack(self.boss,1000)
        return self.g.combat.boss_pattern[id(self.boss)]

    def test_judge_opens_with_laser_and_repeats_often(self):
        c=self.g.combat;skills=[]
        for _ in range(4):
            c.boss_attack(self.boss,1000);skills.append(c.boss_pattern.pop(id(self.boss))['skill'])
        self.assertEqual(skills,['laser','snipe','laser','split'])

    def test_three_or_four_wide_slow_beams_and_long_duration(self):
        for enraged,count,duration in ((False,3,9000),(True,4,11000)):
            self.g.combat.boss_cycles.clear();self.g.combat.boss_pattern.clear()
            p=self.laser(enraged)
            self.assertEqual(p['beam_count'],count)
            self.assertEqual(p['impact']-p['windup'],duration)
            self.assertGreater(p['beam_half_width'],.45)
            self.assertLess(p['rotation_speed']*18,3.2)

    def test_reverse_is_continuous_paused_and_warned(self):
        c=self.g.combat;p=self.laser();start=p['windup'];turn=4000
        a,d,w=c.laser_state(p,start+turn-1);self.assertEqual(d,1);self.assertTrue(w)
        b,d,w=c.laser_state(p,start+turn+500);self.assertEqual(d,0);self.assertTrue(w)
        self.assertLess(abs(b-a),.001)
        b2,_,_=c.laser_state(p,start+turn+900);self.assertEqual(b,b2)
        end,d,_=c.laser_state(p,start+turn+1100);self.assertEqual(d,-1);self.assertLess(end,b)
        self.assertIn('反转',c.laser_status(p,start+turn-500))

    def test_windup_safe_and_visual_width_matches_hit_boundary(self):
        g=self.g;c=g.combat;p=self.laser();start=p['windup']
        c.update(.016,start-1);self.assertEqual(g.hp,100)
        for offset,hit in ((-.01,True),(.01,False)):
            g.player=[14.,14.+p['beam_half_width']+offset];g.hp=100;p.pop('damage_at',None)
            c.update(.016,start);self.assertEqual(g.hp<100,hit)
        with patch.object(c,'_draw_zone') as draw:
            c._draw_corridor(g.screen,p['origin'],0,18,p['beam_half_width'],True)
            ys={round(v[1]-14.,2) for v in draw.call_args_list[0].args[1]}
            self.assertEqual(ys,{-.6,.6})

    def test_all_beams_damage_but_only_once_per_tick(self):
        g=self.g;c=g.combat;p=self.laser();start=p['windup']
        for a in c.laser_rays(p,start):
            g.player=[10+math.cos(a)*4,14+math.sin(a)*4];p.pop('damage_at',None)
            with patch.object(g,'hurt') as hurt:
                c.update(.016,start);hurt.assert_called_once_with(12,source=p['origin'])

    def test_cover_jump_and_recovery_are_safe(self):
        g=self.g;c=g.combat;p=self.laser();start=p['windup']
        g.z=.6;c.update(.016,start);self.assertEqual(g.hp,100)
        g.z=0;g.terrain_cells={(12,14)};c.update(.016,start);self.assertEqual(g.hp,100)
        g.terrain_cells=set();c.update(.016,p['impact']);self.assertEqual(g.hp,100)
        c.update(.016,p['recover']);self.assertNotIn(id(self.boss),c.boss_pattern)

    def test_area_throw_locks_position_full_warning_and_exact_radius(self):
        g=self.g;c=g.combat;p=self.laser();now=p['windup']+600
        # Isolate the area attack from the beam while testing its boundary.
        with patch.object(c,'laser_rays',return_value=[]):
            c.update(.016,now);zone=p['zones'][0];target=zone['target']
            self.assertEqual(zone['land']-zone['start'],1250)
            g.player=[20.,20.];c.update(.016,zone['land']-1)
            self.assertEqual(zone['target'],target);self.assertEqual(g.hp,100)
            for offset,hit in ((-.01,True),(.01,False)):
                zone['hit']=False;g.hp=100
                g.player=[target[0]+c.LASER_AREA_RADIUS+offset,target[1]]
                c.update(.016,zone['land']);self.assertEqual(g.hp<100,hit)
            g.hp=100;c.update(.016,zone['land']+1);self.assertEqual(g.hp,100)

    def test_lag_death_and_wave_clear_do_not_leave_damaging_zones(self):
        g=self.g;c=g.combat;p=self.laser();now=p['windup']+6000
        c.update(.016,now);self.assertEqual(p['zones'][0]['land'],now+1250)
        self.assertEqual(len(p['zones']),1)
        self.boss[2]=0;g.hp=100;c.update(.016,now+1300)
        self.assertEqual(g.hp,100);self.assertFalse(c.boss_pattern)
        self.boss[2]=1000;c.boss_cycles.clear();c.boss_attack(self.boss,1000)
        g.spawn_wave();self.assertFalse(c.boss_pattern)

    def test_normal_walking_can_evade_entire_laser_and_area_phase(self):
        g=self.g;c=g.combat;p=self.laser();radius=6.
        g.player=[10+radius*math.cos(.85),14+radius*math.sin(.85)]
        # Walk with the safe sector and alternate radial sidesteps away from
        # each locked throw. Total speed stays below base 3.2, no jumping.
        for now in range(p['windup'],p['impact'],20):
            angle,_,_=c.laser_state(p,now)
            age=now-p['windup']-600
            if age>=0:
                radius=max(4,min(10,radius+(1 if int(age//1800)%2==0 else -1)*2.7*.02))
            target=(10+radius*math.cos(angle+.85),14+radius*math.sin(angle+.85))
            dx,dy=target[0]-g.player[0],target[1]-g.player[1];dist=math.hypot(dx,dy)
            step=min(dist,3.2*.02)
            if dist:g.move(dx/dist*step,dy/dist*step)
            c.update(.02,now)
        self.assertEqual(g.hp,100)

    def test_hunter_no_longer_uses_colossus_slam(self):
        g=self.g;c=g.combat;g.wave=10;c.boss_attack(self.boss,1000)
        p=c.boss_pattern[id(self.boss)];c.update(.05,p['windup']+550)
        self.assertEqual(c.boss_impacts[-1][2],'hunt')
        calls=[]
        with patch.object(c,'_draw_circle',side_effect=lambda *a,**k:calls.append((a,k))):
            g.now=p['windup']+551;c.draw(g.screen)
        self.assertTrue(any('fx_signature_hunt' in a for a,_ in calls))
        self.assertFalse(any('fx_boss_slam' in a for a,_ in calls))

    def test_fifth_boss_keeps_single_beam_without_area_barrage(self):
        g=self.g;c=g.combat;g.wave=25;c.boss_cycles[id(self.boss)]=1
        c.boss_attack(self.boss,1000);p=c.boss_pattern[id(self.boss)]
        self.assertEqual(p['skill'],'laser');self.assertNotIn('array',p)
        self.assertEqual(len(c.laser_rays(p,p['windup'])),1)
        c.update(.016,p['windup']+600);self.assertNotIn('zones',p)

    def test_hunter_charge_also_uses_claw_not_slam(self):
        g=self.g;c=g.combat;g.wave=10;c.boss_cycles[id(self.boss)]=1
        c.boss_attack(self.boss,1000);p=c.boss_pattern[id(self.boss)]
        c.update(.05,p['impact'])
        self.assertEqual(c.boss_impacts[-1][2],'hunter_charge')


if __name__=='__main__':unittest.main()
