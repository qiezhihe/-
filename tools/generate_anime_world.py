"""Anime world surfaces and the non-boss enemy cast."""
import json
import generate_pixel_pack as api
from generate_pixel_pack import OUT,generate
api.STYLE=''
STYLE='Premium polished anime 3D cel shaded game assets, smooth sculpted materials, crisp contours, rich restrained lighting. Original sci-fi fantasy. No pixel art, no text, no watermark. '
JOBS={}
for name,detail in {
 'floor':'large ivory and blue ceramic space arena floor slabs, sparse fine seams',
 'wall':'ornate ivory blue space fortress wall cladding, subtle gold structural inlays',
 'metal':'blue stone reinforced barrier vertical side, substantial solid blocks',
 'top':'flat horizontal ivory stone barrier capstone, subtle blue gold joinery',
 'lava':'molten orange plasma in dark blue volcanic crust, clearly hazardous'}.items():
 JOBS['anime_world_'+name]=STYLE+'One seamless square flat orthographic material texture filling canvas. '+detail+'. No perspective, no scenery, no objects, no shadows, all edges tile.'
for name,detail in {'normal':'green armored alien infantry with mechanical claw','runner':'slim orange claw robot','shooter':'blue alien energy gunner','tank':'broad blue ivory armored guard','elite':'violet crystal warrior','bat':'small violet flying alien bat with cyan mouth'}.items():
 JOBS['anime_enemy_'+name]=STYLE+'Exactly 4 columns by 2 rows, eight equal cells on pure magenta background. Same full body '+detail+'. Reading order idle, left step, right step, windup, attack, recovery, hurt, fallen dead. Fixed scale, same proportions and equipment, common feet baseline, generous padding. No grid or scenery.'
if __name__=='__main__':
 (OUT/'anime_world_prompts.json').write_text(json.dumps(JOBS,ensure_ascii=False,indent=2),encoding='utf-8')
 for name,prompt in JOBS.items():
  result=generate((name,prompt)); print(result,flush=True)
  if 'FAILED' in result: raise SystemExit(1)
