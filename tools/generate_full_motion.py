"""Resumable full cast animation pass, using the configured image provider."""
import concurrent.futures
from generate_pixel_pack import generate, OUT, STYLE
import json

JOBS={}
weapons={'smg':'compact gray blue SMG','shotgun':'orange pump shotgun','mg':'belt fed machine gun','sniper':'cyan scoped sniper rifle','boomerang':'three blade green boomerang','dagger':'purple curved blink dagger'}
for name,description in weapons.items():
    poses='four recoil and muzzle flash poses, four recovery poses, eight coherent reload poses' if name in ('smg','shotgun','mg','sniper') else 'four windup poses, four attack release poses, eight recovery poses'
    JOBS['anim16_'+name]='Exactly 4 columns by 4 rows, sixteen equal cells on pure magenta background. First person gloved hands, white lab coat cuffs, blue black armor gloves, '+description+'. '+poses+'. Consecutive reading order, same weapon throughout, identical wrist registration, lower right placement, empty upper left, no full character, no text.'
enemies={'normal':'green experiment soldier with brain helmet and mechanical claw','runner':'slim orange long-legged claw robot','shooter':'squat blue acid sac alien','tank':'broad gray blue armored guard','elite':'purple crystal hunter','bat':'small purple flying bat with cyan energy mouth','boss_fan':'large multi-eyed green organic tentacle lord','boss_dash':'orange thruster quadruped mechanical beast','boss_ring':'purple floating core with green central eye and orbital rings'}
for name,description in enemies.items():
    JOBS['motion_enemy_'+name]='Exactly 4 columns by 4 rows, sixteen equal cells, pure magenta background. Same '+description+' in all frames. Row 1 four consecutive walk cycle poses; row 2 four windup poses; row 3 four attack release and recovery poses; row 4 four hurt then recovery poses. Front facing entire body, fixed scale, feet baseline identical, centered, generous padding. No shadow, no ground, no text. Floating units use fixed center instead of feet.'
for name,description in {'healer':'green healing spirit','taunter':'grounded yellow stationary decoy turret','gunner':'blue machine gun drone','minelayer':'grounded orange four legged robotic dog','berserker':'orange flame spirit'}.items():
    JOBS['motion_pet_'+name]='Exactly 4 columns by 2 rows, eight equal cells, pure magenta background. Same '+description+' every cell. First row four consecutive idle or locomotion poses, second row four skill activation poses. Fixed proportions, same colors, centered fixed feet or hover baseline. No text, no ground.'

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'full_motion_prompts.json').write_text(json.dumps({k:STYLE+v for k,v in JOBS.items()},indent=2),encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(generate,JOBS.items()): print(result,flush=True)
