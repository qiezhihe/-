"""Five original full-screen boss entrance sequences."""
import json
import generate_pixel_pack as api
from generate_pixel_pack import OUT,generate
from generate_boss_cast import CAST
api.STYLE=''
BEATS={
 'colossus':'cracked molten floor, rising basalt armored torso, full giant rising, hammer lifted, hammer striking ground, expanding ember debris, imposing standing giant, final threatening stance',
 'hunter':'dark crimson rift, claws emerging, predator head emerging, body leaping forward, low landing, dust and ivory claws, stalking forward, final crouched threat',
 'judge':'descending ivory mechanical capsule light, armored boots descending, full marksman landing, cloak unfolding, cannon raised, red sight charging, ceremonial stance, final cannon aimed aside',
 'weaver':'jade egg nest, cracking cocoon, spider legs emerging, queen unfolding, full spider queen rising, egg sacs illuminating, spreading six legs, final looming queen',
 'executioner':'dark bronze sword seal, knight silhouette materializing, armored knight visible, sword hand gripping hilt, greatsword drawn, violet blade flourish, shield raised, final duel stance',
}
if __name__=='__main__':
 prompts={}
 for name,desc in CAST.items():
  prompts['entrance_'+name]=('Premium anime 3D cel shaded cinematic storyboard sprite sheet. Exactly 2 columns by 4 rows, eight equal landscape 2:1 panels, no gutters, no text. '
   'Original '+desc+'. Same exact character equipment and proportions in all panels. One continuous entrance, fixed camera and lighting. '
   'Dark deep space fortress background with restrained atmosphere, full creature visible with generous padding, no HUD. '
   'Reading order: '+BEATS[name]+'. Clear meaningful movement between panels, richly rendered but readable, no magenta background.')
 (OUT/'boss_entrance_prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
 for name,prompt in prompts.items():
  result=generate((name,prompt)); print(result,flush=True)
  if 'FAILED' in result: raise SystemExit(1)
