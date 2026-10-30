"""Perspective sampling of supplied raster art on collision-defined cells."""
from pathlib import Path
import math
import numpy as np
import pygame

class MapArt:
    def __init__(self):
        folder=Path(__file__).parent/'Assets/Art/pixel_portal_v1/runtime'
        self.images={name:pygame.image.load(str(folder/(name+'.png'))).convert() for name in ('floor','lava','metal','wall','menu','station')}
        station=pygame.image.load(str(folder/'station.png')).convert_alpha()
        rgb=pygame.surfarray.pixels3d(station)
        white=(rgb[:,:,0]>255)  # Alpha is prepared offline; keep ivory details.
        del rgb
        alpha=pygame.surfarray.pixels_alpha(station); alpha[white]=0; del alpha
        self.images['station']=station
        cloud=folder
        for name in ('floor','lava','metal','wall'):
            high=folder.parent/'source'/('scene_painted_'+name+'.png')
            dark=folder.parent/'source'/('anime_world_dark_'+name+'.png')
            anime=dark if dark.exists() else folder.parent/'source'/('anime_world_'+name+'.png')
            if anime.exists(): high=anime
            if not high.exists(): high=folder.parent/'source'/('scene_single_'+name+'.png')
            if not high.exists(): high=folder.parent/'source'/('scene_v3_'+name+'.png')
            if high.exists():
                self.images[name]=pygame.image.load(str(high)).convert()
            elif (cloud/(name+'.png')).exists():
                self.images[name]=pygame.image.load(str(cloud/(name+'.png'))).convert()
        self.textures={name:pygame.surfarray.array3d(self.images[name]) for name in ('floor','lava','metal')}
        top=folder.parent/'source'/'scene_painted_top.png'
        if (folder.parent/'source'/'anime_world_dark_top.png').exists(): top=folder.parent/'source'/'anime_world_dark_top.png'
        self.textures['barrier_top']=pygame.surfarray.array3d(pygame.image.load(str(top)).convert()) if top.exists() else self.textures['metal']
        self.floor_mips=[self.textures['floor']]
        for size in (512,256,128,64,32):
            self.floor_mips.append(pygame.surfarray.array3d(pygame.transform.smoothscale(self.images['floor'],(size,size))))
        self._ground_cache={}
        # A deterministic panoramic star field, built once rather than per frame.
        import random
        rng=random.Random(7321)
        self.space=pygame.Surface((3840,1200)); self.space.fill((3,5,16))
        for _ in range(1500):
            x=rng.randrange(3840); y=rng.randrange(1200); v=rng.randrange(75,230)
            pygame.draw.circle(self.space,(v,v,min(255,v+25)),(x,y),1 if v<210 else 2)
        pygame.draw.circle(self.space,(32,48,83),(2500,360),145)
        pygame.draw.circle(self.space,(9,15,35),(2545,335),137)

    def draw_space(self,g):
        w,h=g.screen.get_size()
        offset=int((g.angle%(math.tau))/math.tau*self.space.get_width())
        y=int(-300+g.pitch*h*.72)
        g.screen.fill((3,5,16))
        for x in (-offset,self.space.get_width()-offset):
            g.screen.blit(self.space,(x,y))

    def draw_ground(self,g):
        w,h=g.screen.get_size()
        horizon=h/2+g.pitch*h*.72
        first=max(0,min(h,int(horizon)+1))
        if first>=h: return
        step=2  # Half-resolution ground sampling; retain original HD textures.
        yy=np.arange(first,h,step,dtype=np.float32)[None,:]+.5; xx=np.arange(0,w,step,dtype=np.float32)[:,None]+.5
        zoom=2.5 if g.ads and g.weapon_index==3 else 1.4 if g.ads else 1
        focal=w/(2*math.tan(math.pi/6))*zoom
        denom=yy-horizon
        depth=(g.z+.5)*h*.55*zoom/np.maximum(1,denom)
        side=(xx-w/2)*depth/focal
        wx=g.player[0]+depth*math.cos(g.angle)-side*math.sin(g.angle)
        wy=g.player[1]+depth*math.sin(g.angle)+side*math.cos(g.angle)
        cx=np.floor(wx).astype(int); cy=np.floor(wy).astype(int)
        def sample(name):
            texture=self.textures[name]; tw,th=texture.shape[:2]
            # Large quiet floor slabs instead of repeating a busy panel every metre.
            u=((wx/4)%1)*(tw-1) if name=='floor' else (wx-cx)*(tw-1)
            v=((wy/4)%1)*(th-1) if name=='floor' else (wy-cy)*(th-1)
            return texture[np.rint(u).astype(int),np.rint(v).astype(int)]
        pixels=sample('floor')
        # Filter distant floor detail to reduce crawling/shimmer during movement.
        footprint=np.maximum(1,depth/4*self.images['floor'].get_width()/focal)
        for level,texture in enumerate(self.floor_mips[1:],1):
            columns=np.flatnonzero((footprint>=2**level)[0])
            if not len(columns): continue
            tw,th=texture.shape[:2]
            filtered=texture[((wx[:,columns]/4)%1*(tw-1)).astype(int),((wy[:,columns]/4)%1*(th-1)).astype(int)]
            pixels[:,columns]=filtered
        # Sample lava only at visible lava pixels, rather than projecting a
        # second full-screen texture every frame.
        if g.lava_cells:
            mask=np.zeros(cx.shape,dtype=bool)
            for x,y in g.lava_cells: mask|=(cx==x)&(cy==y)
            if mask.any():
                texture=self.textures['lava']; tw,th=texture.shape[:2]
                u=np.rint((wx[mask]-cx[mask])*(tw-1)).astype(int)
                v=np.rint((wy[mask]-cy[mask])*(th-1)).astype(int)
                pixels[mask]=texture[u,v]
        fog=np.clip(1-depth*.045,0,1)
        pixels=(pixels*fog[:,:,None]+np.array([40,55,65])*(1-fog[:,:,None])).astype('uint8')
        surface=pygame.surfarray.make_surface(pixels)
        g.screen.blit(pygame.transform.scale(surface,(w,h-first)),(0,first))

    def draw_obstacles(self,g):
        w,h=g.screen.get_size()
        focal=w/(2*math.tan(math.pi/6))*(2.5 if g.ads and g.weapon_index==3 else 1.4 if g.ads else 1)
        zoom=focal/(w/(2*math.tan(math.pi/6)))
        horizon=h/2+g.pitch*h*.72
        # Ray/box intersections: visible pixels use the collision box itself.
        for x in range(0,w,2):
            side=(x+.5-w/2)/focal
            dx=math.cos(g.angle)-side*math.sin(g.angle); dy=math.sin(g.angle)+side*math.cos(g.angle)
            hits=[]
            for cx,cy in g.terrain_cells:
                ax=(cx-g.player[0])/dx if abs(dx)>1e-9 else -math.inf
                bx=(cx+1-g.player[0])/dx if abs(dx)>1e-9 else math.inf
                ay=(cy-g.player[1])/dy if abs(dy)>1e-9 else -math.inf
                by=(cy+1-g.player[1])/dy if abs(dy)>1e-9 else math.inf
                if abs(dx)<=1e-9 and not cx<=g.player[0]<=cx+1: continue
                if abs(dy)<=1e-9 and not cy<=g.player[1]<=cy+1: continue
                entry=max(min(ax,bx),min(ay,by))
                near=max(entry,.12); far=min(max(ax,bx),max(ay,by))
                if near>far: continue
                top=int(horizon+(g.z+.5-g.wall_height)*h*.55*zoom/near)
                bottom=int(horizon+(g.z+.5)*h*.55*zoom/near)
                back=int(horizon+(g.z+.5-g.wall_height)*h*.55*zoom/far)
                hitx=g.player[0]+dx*near; hity=g.player[1]+dy*near
                u=hity-cy if min(ax,bx)>min(ay,by) else hitx-cx
                hits.append((near,top,bottom,back,u,cx,cy,entry))
            for near,top,bottom,back,u,cx,cy,entry in sorted(hits,reverse=True):
                texture=self.images['metal']
                col=texture.subsurface((min(texture.get_width()-1,max(0,int(u*(texture.get_width()-1)))),0,1,texture.get_height()))
                # Clip projected columns before scaling: close faces must not stop
                # at an arbitrary 3000-pixel cap and reveal holes underneath.
                for upper,lower in ((top,bottom),):
                    if entry<=0: continue  # Camera above/inside footprint sees the top, not an invented near face.
                    start=max(0,upper); end=min(h,lower)
                    if end<=start or lower<=upper: continue
                    v0=max(0,min(col.get_height()-1,int((start-upper)/(lower-upper)*col.get_height())))
                    v1=max(v0+1,min(col.get_height(),math.ceil((end-upper)/(lower-upper)*col.get_height())))
                    patch=col.subsurface((0,v0,1,v1-v0))
                    g.screen.blit(pygame.transform.scale(patch,(min(2,w-x),end-start)),(x,start))
                # Top is a horizontal world plane, never a stretched side column.
                start=max(0,math.floor(horizon)+1,min(back,top)); end=min(h,max(back,top))
                if end>start and g.z+.5>g.wall_height:
                    yy=np.arange(start,end,dtype=np.float32)+.5
                    denom=yy-horizon
                    depths=(g.z+.5-g.wall_height)*h*.55*zoom/np.maximum(.001,denom)
                    wx=g.player[0]+dx*depths; wy=g.player[1]+dy*depths
                    tex=self.textures['barrier_top']; tw,th=tex.shape[:2]
                    pixels=tex[np.clip(((wx-cx)*(tw-1)).astype(int),0,tw-1),np.clip(((wy-cy)*(th-1)).astype(int),0,th-1)]
                    strip=pygame.surfarray.make_surface(pixels[None,:,:])
                    g.screen.blit(pygame.transform.scale(strip,(min(2,w-x),end-start)),(x,start))
