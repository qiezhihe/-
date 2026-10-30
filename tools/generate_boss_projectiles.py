"""Boss-specific original projectile art through configured image service."""
import json
import generate_pixel_pack as api
from generate_pixel_pack import OUT,generate
api.STYLE=''
JOBS={
 'boss_ammo_colossus':'heavy jagged basalt boulder with orange molten fissures, solid rocky silhouette, few ember chips',
 'boss_ammo_hunter':'ivory hooked chitin bone spike with crimson tendon root, sharp organic silhouette',
 'boss_ammo_judge':'heavy bronze armor piercing cannon shell, crimson mechanical nose and ivory fins, solid ammunition',
 'boss_ammo_weaver':'jade organic egg sac with pale membrane, violet poisonous seeds visible inside, viscous organic silhouette',
 'boss_ammo_executioner':'physical crescent greatsword blade of dark steel with violet engraved edge and bronze guard, spinning weapon fragment',
}
if __name__=='__main__':
 prompts={k:'One isolated game projectile, premium anime 3D cel shaded render. '+v+'. Front three-quarter view, large readable compact shape, pure magenta background. No beam, no energy orb, no light wave, no trails, no text, no shadow outside object. Generous padding.' for k,v in JOBS.items()}
 (OUT/'boss_ammo_prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
 for k,p in prompts.items():
  result=generate((k,p)); print(result,flush=True)
  if 'FAILED' in result: raise SystemExit(1)
