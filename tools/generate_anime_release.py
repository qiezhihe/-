"""Resumable anime 3D boss and interface production, configured image API."""
import json
import generate_pixel_pack as api
from generate_pixel_pack import generate, OUT
from generate_boss_cast import CAST
api.STYLE=''
STYLE='Premium anime 3D cel-shaded game render, polished sculpted forms, clean contours, dramatic controlled lighting, original sci-fi dark fantasy. No pixel art, no text, no watermark. '
JOBS={}
for name,desc in CAST.items():
 JOBS['anime_boss_'+name]=STYLE+'Exactly 4 columns by 4 rows, sixteen equal cells, pure magenta background. Same full body '+desc+'. Same design and equipment throughout, centered fixed scale, generous padding. Row one four smooth walking poses. Row two four attack windup poses. Row three four attack release and recovery poses. Row four two hurt poses and two fallen death poses. Feet baseline identical for living poses. No scenery, no grid lines.'
JOBS['anime_intro']=STYLE+'Exactly 4 columns by 2 rows, eight equal cells, pure magenta background. One coherent summoning portal effect sequence: tiny violet rift, growing rift, opening ring, expanding radiant portal, full portal with lightning, energy burst, dissipating sparks, fading ring. No characters, no text, contained silhouettes and generous padding.'
for key,desc in {
 'hud':'very wide thin player health and ammo panel', 'card':'tall upgrade selection card',
 'slot':'compact square weapon slot','pet':'wide companion status panel','pause':'large pause menu panel',
 'boss':'very wide thin imposing boss health bar','ammo':'wide compact ammo interaction prompt',
 'wave':'wide wave announcement panel','objective':'wide objective panel'}.items():
 JOBS['anime_ui_'+key]=STYLE+'One isolated empty '+desc+'. Satin navy enamel, sculpted ivory edges, restrained cyan light and violet accents, thin refined border, large dark readable interior. Pure magenta background, no lettering, no symbols, no gauges, no characters. Front orthographic UI asset, not tilted.'
JOBS['anime_icons']=STYLE+'Exactly 8 columns by 4 rows, equal cells pure magenta background. 32 isolated readable upgrade icons in reading order: heart vial, regeneration heart, shield, armor, boot, target, critical target, magazine, reload arrows, rapid bullets, piercing bullet, pellets, grouped pellets, ammunition belt, scope, blade, sword arc, blood blade, shield sword, impact, returning blade, spear, dash dagger, ammo refill, cooldown reset, healer spirit, decoy turret, gun drone, robotic dog, flame spirit, crystal, fire. Consistent 3D anime inventory icon style, no text.'
if __name__=='__main__':
 (OUT/'anime_release_prompts.json').write_text(json.dumps(JOBS,ensure_ascii=False,indent=2),encoding='utf-8')
 for name,prompt in JOBS.items():
  result=generate((name,prompt)); print(result,flush=True)
  if 'FAILED' in result: raise SystemExit(1)
