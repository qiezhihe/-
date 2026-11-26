import os
os.environ.setdefault('SDL_VIDEODRIVER','dummy')
os.environ.setdefault('SDL_AUDIODRIVER','dummy')
import unittest
from unittest.mock import patch
import pygame
from fps_game import Game


class BossV14Tests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.g=Game(muted=True)
        cls.g.state='playing'
        cls.g.terrain_cells=set()

    @classmethod
    def tearDownClass(cls):
        pygame.quit()

    def test_complete_colossus_silhouette_and_ground_alignment(self):
        g=self.g;g.wave=5;g.angle=0;g.pitch=0
        boss=[19.,14.,1000.,0,1000.,'boss',999999]
        g.enemies=[boss]
        for zoom in (False,True):
            g.ads=zoom;g.weapon_index=3
            for z in (0,.65):
                g.z=z
                for now in (100,1200,2200):
                    g.now=now
                    g.combat.boss_pattern[id(boss)]=dict(skill='hammer',windup=1000,impact=2000,recover=3000)
                    image,rect=g.enemy_visual(boss)
                    ground=g.project(*boss[:2],-.5)
                    self.assertLessEqual(abs(rect.y+image.get_bounding_rect(min_alpha=128).bottom-ground[1]),2)
        # The old equal-row importer cropped this pose to only 245px tall.
        source=g.enemy_art.cloud['anime_boss_colossus_v14_0']
        self.assertGreater(source.get_bounding_rect(min_alpha=128).height,330)
        g.ads=False;g.z=0;g.combat.boss_pattern.clear()

    def test_hammer_visual_radius_matches_damage_boundary(self):
        g=self.g;g.z=0;g.wave=5
        boss=[10.,14.,1000.,0,1000.,'boss',999999];g.enemies=[boss]
        for stage in range(4):
            radius=g.combat.hammer_radius(stage)
            for offset,hit in ((-.01,True),(.01,False)):
                g.player=[14.+radius+offset,14.];g.hp=100;g.shield=0
                pattern=dict(skill='hammer',windup=1000,impact=4000,recover=5000,
                             stage=stage,enraged=True,origin=(10.,14.),target=(14.,14.))
                g.combat._update_signature(boss,pattern,1000+stage*450)
                self.assertEqual(g.hp<100,hit)
                self.assertEqual(g.combat.boss_impacts[-1][4],radius)
        g.player=[14.,14.];g.combat.boss_impacts.clear()

    def test_world_circle_and_ray_width_are_used_for_effects(self):
        g=self.g;g.player=[14.,14.];g.angle=0;g.z=0
        captured=[]
        with patch.object(g.combat,'_draw_zone',side_effect=lambda surface,vertices,*args,**kwargs:captured.append(vertices)):
            g.combat._draw_circle(g.screen,(19.,14.),3.05)
            self.assertTrue(all(abs(__import__('math').dist(p,(19.,14.))-3.05)<1e-8 for p in captured[-1]))
            g.combat._draw_corridor(g.screen,(16.,14.),0,18,g.combat.LASER_HALF_WIDTH,True)
            self.assertEqual({round(p[1]-14.,2) for p in captured[-1]},{-.45,.45})
        # No vanishing circle when the player stands inside the damage area.
        points=g.combat._ground_polygon([(14.-3,11.),(17.,11.),(17.,17.),(11.,17.)])
        self.assertGreaterEqual(len(points),3)
        self.assertTrue(all(p is not None for p in points))


if __name__=='__main__': unittest.main()
