"""Original boss production sheets through the configured image provider."""
import json
import generate_pixel_pack as api
from generate_pixel_pack import OUT,generate

api.STYLE=''
CAST={
 'colossus':'towering basalt and bronze humanoid executioner, massive two handed furnace hammer, ember fissures, heavy grounded feet',
 'hunter':'lean quadruped alien predator, ivory chitin and dark crimson tendons, long hooked claws, low stalking posture, no gun',
 'judge':'tall ceremonial armored marksman, narrow crimson visor, ivory cloak, huge integrated precision cannon, angular silhouette',
 'weaver':'broad grounded abyssal spider queen, six articulated legs, dark jade carapace, luminous egg sacs, organic brood organs',
 'executioner':'imposing dark knight, sweeping split cloak, long violet greatsword and battered bronze shield, crown shaped helmet',
}
PREFIX=('Original premium game boss sprite sheet for a first person arena, refined hand painted dark fantasy science fiction, '
 'clear silhouette and detailed materials, no franchise characters. Exactly 4 columns by 2 rows of equal cells. '
 'Pure magenta #FF00FF background, no text, no grid, no scenery, no shadows outside body. '
 'Same full body creature, same equipment, same scale and feet baseline in every cell, generous padding. '
 'Reading order: idle, left step, right step, dramatic attack windup, attack release, exhausted recovery, wounded recoil, fallen dead. ')

if __name__=='__main__':
 jobs={'boss_cast_'+k:PREFIX+v for k,v in CAST.items()}
 jobs['boss_cast_fx']=('Exactly 4 columns by 2 rows isolated hand painted game effects, pure magenta background, equal cells, no lettering, no scenery. '
 'Reading order: orange hammer shockwave, red predator claw burst, crimson precision cannon muzzle blast, jade egg hatching burst, violet sword arc, '
 'orange heavy impact warning rune, violet shattering armor stagger, ember boss death explosion. Clear readable complete silhouettes with padding.')
 (OUT/'boss_cast_prompts.json').write_text(json.dumps(jobs,ensure_ascii=False,indent=2),encoding='utf-8')
 for name,prompt in jobs.items():
  result=generate((name,prompt)); print(result,flush=True)
  if 'FAILED' in result: raise SystemExit(1)
