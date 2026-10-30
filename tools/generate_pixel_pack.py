"""Resumable Apinebula pixel asset production. Never contains credentials."""
import base64
import concurrent.futures
import json
import os
from pathlib import Path
import urllib.request

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'Assets/Art/pixel_portal_v1/source'
STYLE = ('Production game sprites for an absurd interdimensional science-fiction survival FPS, '
         'Rick and Morty inspired alien laboratories and green portals. Consistent crisp 16-bit pixel art, '
         'dark outlines, gray-blue worn metal, acid green, purple, orange accents. Limited color ramps. '
         'No 3D, no painting, no blur, no text, no watermark. ')
JOBS = {}
for name, description in {
    'normal':'gray green experiment soldier with mechanical claw',
    'runner':'slim orange fast robot with long legs and sharp claws',
    'shooter':'squat blue alien with acid sac and spitting mouth',
    'tank':'wide gray blue armored mechanical guard',
    'elite':'tall purple crystal hunter with green eye',
    'boss_fan':'huge organic multi-eyed alien lord with four fan-barrage organs',
    'boss_dash':'heavy quadruped robot beast with orange thrusters and charging horn',
    'boss_ring':'floating purple dimensional core with green eye and three orbital rings',
}.items():
    JOBS['enemy_'+name] = ('Exactly 4 columns by 2 rows sprite sheet, 1024 square canvas, '
        'eight equal 256 square cells, no gutters or grid lines. Solid pure magenta #FF00FF background. '
        'Same character in all cells: '+description+'. Front-facing full body, same scale, centered in '
        'each cell, feet on baseline 232 within each cell. Reading order: idle, left foot forward walk, '
        'right foot forward walk, attack windup, attack release, attack recovery, hurt, fallen dead. '
        'Do not clip limbs; no shadows. Anatomically coherent poses, identical equipment across frames.')
for name, description in {
    'smg':'compact gray blue SMG, short straight magazine, green energy window',
    'shotgun':'chunky short shotgun, orange pump grip and large muzzle',
    'mg':'belt-fed machine gun, yellow cartridge belt and dark teal receiver',
    'sniper':'long thin sniper rifle, small cyan scope and gray white casing',
    'sword':'short thick cyan sword in right hand and shield on left forearm, absolutely no gun',
    'boomerang':'three curved blades boomerang, green cutting edges',
    'spear':'piercing blue metal spear with cyan point',
    'dagger':'small reverse-grip curved dagger, purple dimensional cracks',
}.items():
    poses=('idle, trigger fire with muzzle flash, recoil, recover, magazine removed, magazine inserted, bolt action, idle'
           if name in ('smg','shotgun','mg','sniper') else
           'idle, windup, attack extension, followthrough, recovery, defensive ready, defensive impact, idle')
    JOBS['held_'+name] = ('Exactly 4 columns by 2 rows sprite sheet on 1024 square canvas. '
        'Eight equal 256 square cells, solid pure magenta #FF00FF background, no lines. '
        'First person gloved hands holding '+description+'. Same weapon and hands in every frame. '
        'Only hands and weapon, not full character. Weapon in lower right of each cell, '
        'upper left 60 percent must stay empty. Eight consecutive poses in reading order: '+poses+'. '
        'Compact weapon, unobstructed sight line, no unrelated guns in melee frames.')
JOBS['pets'] = ('Exactly 5 columns by 2 rows sheet, equal cells, pure magenta background. '
    'Top row: green healer spirit, grounded yellow stationary decoy, blue gun drone, '
    'grounded four legged orange mine dog, orange berserk flame spirit. Bottom row: same five '
    'companions activating their own skill. Complete silhouettes, no ground shadows.')
JOBS['ui'] = ('Exactly 3 columns by 2 rows of isolated empty UI frames, pure magenta background. '
    'Reading order: wide HUD panel, tall upgrade card, square weapon slot, wide pet status panel, '
    'very wide thin boss health frame, medium pause panel. Worn cartoon laboratory frames, '
    'dark ink outlines, green slime confined to corners, empty dark teal interior, no text or icons.')
JOBS['ui_v2'] = ('Exactly 4 columns by 2 rows, eight isolated game UI panels on pure magenta background, equal cells, no text. '
    'Premium hand-authored 16-bit sci-fi survival roguelite interface, dark navy glass, worn brass corners, muted teal lines, '
    'small acid-green signal lights and orange warning accents, restrained decoration, readable at 960x600. '
    'Reading order: compact HUD, upgrade card, weapon slot, pet panel, ammo prompt, pause panel, objective banner, wave banner. '
    'No boss health bar, no characters, no logos, no gradients, no plastic 3D, crisp pixel edges.')
JOBS['icons'] = ('Exactly 8 columns by 4 rows of distinct square upgrade icons, equal cells, pure magenta '
    'background. Reading order: health heart vial, regenerating heart, shield, armor, speed boots, '
    'critical target, broken critical target, magazines, reload arrows, rapid bullets, piercing bullet, '
    'shotgun pellets, tight pellets, machinegun belt, sniper scope, blade damage, blade arc, '
    'lifesteal blade, sword shield, stagger impact, returning boomerang, piercing spear, dash dagger, '
    'blue ammo refill, orange cooldown reset, healer pet, decoy pet, drone pet, mine dog pet, '
    'berserk pet, XP crystal, flame. Clear simple silhouettes, no lettering.')
for name, desc in {'floor':'low contrast gray blue worn laboratory floor', 'wall':'gray teal laboratory wall panels',
                   'metal':'solid gray blue rising wall armor', 'lava':'dark red lava with orange cracks'}.items():
    JOBS[name] = 'Single seamless square tileable texture, orthographic flat surface, '+desc+'. No perspective, no objects, no border. Edges must tile. Low visual noise.'
JOBS['enemy_bat'] = ('Exactly 4 columns by 2 rows sprite sheet, eight equal cells, pure magenta background. '
    'Small floating purple alien bat with cyan energy mouth, huge pointed ears, compact body and clear wings. '
    'Same creature in all eight cells: idle hovering, wings up, wings down, mouth charging, energy wave release, recovery, hurt, dead. '
    'Full silhouette with generous padding, no projectile attached. Consistent pixel scale.')
JOBS['boss_souls_fx'] = ('Production-ready 4 columns by 2 rows sprite sheet, eight equal cells, '
    'solid pure magenta background, no words or grid. Original dramatic sci-fi boss effects with readable silhouettes, '
    'not copying any franchise. Reading order: orange ground impact warning sigil, intense volcanic ground slam '
    'with expanding debris ring, purple laser charging star, explosive purple beam impact bloom, green organic '
    'splitting energy blast, violet dimension rupture ring, orange aerial thruster exhaust, white cyan stagger burst. '
    'Crisp pixel art, effects completely contained in each cell, dark contour and bright core, generous empty padding.')
JOBS['boss_header_v2'] = ('One single extremely wide horizontal boss health bar frame centered on solid pure magenta '
    'background. Original premium pixel sci-fi dark fantasy fusion: dark ink worn metal, restrained bone-like alien '
    'corners, crimson accent and glowing purple core, imposing but thin readable silhouette. Empty dark central '
    'channel for health fill and empty name area above it. No text, no numbers, no filled health bar. No bulky knobs.')
JOBS['hybrid_icons'] = ('Exactly 4 columns by 3 rows of isolated pixel upgrade icons, equal cells, pure magenta background, no labels. '
    'Reading order: medical heart and sprout, blood armor, running boot and magazine, target and ammo, '
    'poison flame, ice and shattered target, piercing siege bullet, bomb and long barrel, shield and regeneration, '
    'execution axe and target, book and heart, fast gloved hand and magazine. Clear bold silhouettes, consistent blue green orange palette.')
JOBS['held_sword_v2'] = ('Exactly 4 columns by 2 rows, eight equal cells, pure magenta background. '
    'First-person anatomically correct gloved hands: LEFT hand holds compact blue metal shield with forearm straps, '
    'RIGHT hand grips short cyan sword. White laboratory coat cuffs, navy gloves, cyan wrist modules. '
    'Same equipment all frames, lower part of canvas, clear central aim. Reading order idle, windup, horizontal slash, '
    'followthrough, recovery, raised shield covering lower left and center while sword stays right, '
    'shield recoiling under impact, idle. Never put shield on right hand, never float shield without arm. No gun.')
JOBS['held_spear_v2'] = ('Exactly 4 columns by 2 rows, eight equal cells, pure magenta background. '
    'First-person blue-black gloves and white lab coat cuffs throwing one cyan tipped metal spear. '
    'Same spear throughout. Reading order: held idle, pulled back windup, forward throw release, '
    'empty open right hand after release, empty hand waiting, empty hand reaching to catch, '
    'hand catching returning spear, held idle. Weapon compact at bottom right, center view empty. No gun, no sword.')
JOBS['held_shotgun_v2'] = ('Exactly 4 columns by 2 rows, eight equal cells, pure magenta background. '
    'FIRST PERSON only: blue-black armored gloves and white lab coat cuffs holding one compact orange pump shotgun. '
    'New character-consistent hands, no old hero, no face, no body, no other weapons. Lower right placement with empty center. '
    'Reading order: idle, pump ready, muzzle flash, recoil, recovery, magazine out, magazine in, idle. Crisp pixel art.')
JOBS['held_spear_v3'] = ('Exactly 4 columns by 4 rows, sixteen equal cells, pure magenta background. '
    'FIRST PERSON blue-black armored gloves and white lab coat cuffs, one consistent cyan tipped two-part spear. '
    'Rows: 1 held idle and pullback windup; 2 one forward throw release and empty hand; '
    '3 spear flying away and distant flight; 4 hand reaching, spear returning, catch, held idle. '
    'One spear only, no duplicates, no gun, no sword, lower right, center sight clear, crisp pixel art.')
JOBS['motion_ui_v3'] = ('Exactly 4 columns by 4 rows, equal cells, pure magenta background. '
    'Four coherent sequences, each row same object progressing smoothly through 4 frames. '
    'Row 1: cyan healing ring gradually expanding and fading. Row 2: purple laser charging star pulsing brighter. '
    'Row 3: orange ground slam shockwave expanding and dissipating. Row 4: green portal ring slowly rotating. '
    'Crisp consistent pixel art, no text, no frames, no characters, centered identical registration, no clipping.')
for weapon,action in {
    'sword':'right hand cyan short sword sweeping horizontally, left hand holding strapped blue shield; 4 windup poses, 5 slash poses, 7 recovery poses',
    'spear':'right hand throwing one cyan spear then waiting empty and catching it; 3 windup, 3 release, 4 empty-hand wait, 3 reaching, 3 catching poses',
}.items():
    JOBS['anim16_'+weapon]=('Exactly 4 columns by 4 rows sprite sheet, sixteen equal cells, pure magenta background. '
        'FIRST PERSON perspective, white lab coat cuffs, blue black armored gloves. '+action+'. '
        'Consecutive smooth motion in reading order, identical weapon geometry and hands, anchored wrists, '
        'compact lower right composition, upper left empty. No full characters, no text, no gun, no panel borders.')
JOBS['fx_wave'] = ('One isolated crescent energy wave projectile, cyan blue edges and bright ivory core, '
    'clear compact silhouette, frontal view, pure magenta background, no text, no creature, no scene.')
JOBS['fx_laser'] = ('One horizontal straight energy beam strip, left to right, bright ivory core, magenta purple outer energy, '
    'sharp pixel edges, consistent thickness, no perspective, pure magenta-free dark green #00FF00 background. No labels or objects.')
for material,description in {
    'floor':'large quiet slate blue laboratory concrete slabs, restrained fine chips and subtle aggregate, sparse thin seams, no vents or glowing strips',
    'wall':'industrial blue grey laboratory wall, large readable metal panels, carefully placed rivets and worn edges, restrained cyan accents',
    'metal':'solid dark blue rising barrier armor, substantial worn metal panels, sparse orange hazard corner details',
    'lava':'dark volcanic crust with vivid orange molten cracks and rich red depths, clear dangerous readable surface',
}.items():
    JOBS['hdmap_'+material]=('High resolution production material texture, single seamless square flat orthographic tile, '
        +description+'. Sharp hand-authored pixel game aesthetic with refined surface detail, coherent with the approved alien lab atlas. '
        'Absolutely no perspective, no cast shadows, no objects, no text, no frame, no blur, no repeating tiny busy panels. All edges tile.')
JOBS['station'] = ('Single complete front view ammo refill station, gray blue metal, green friendly lamp, '
    'orange ammo box, large magazine pictogram, grounded base. Pure magenta background, no lettering.')
JOBS['weapon_crate_views'] = ('Exactly 2 columns by 2 rows on 1024 square canvas, solid pure magenta background, '
    'same compact sci-fi weapon crate in four consistent orthographic views: front, right side, top, '
    'and three-quarter front. Gray-blue worn metal, cyan edge lights, acid green central weapon emblem, '
    'orange warning stripe. Same dimensions and corners in every view, grounded, no text, no characters.')
JOBS['menu'] = ('Wide menu background: abandoned alien laboratory framing a luminous spiral green portal, '
    'alien purple plants and worn equipment around edges, middle region low detail and dark for text. '
    'No UI, no lettering, no characters.')
JOBS['effects'] = ('Exactly 4 columns by 4 rows of isolated game effect sprites on solid magenta background. '
    'Equal cells, no labels or lines. Reading order: short SMG muzzle flash, broad shotgun flash, '
    'machinegun flash, thin sniper flash, cyan sword slash, spinning three-blade boomerang, '
    'flying blue spear, purple blink dagger trail, orange enemy bullet with bright yellow core, '
    'magenta energy orb with white core, impact sparks, cyan shield impact, orange mine explosion, '
    'green healing ring, red danger circle, red charge direction arrow. Crisp pixel silhouettes.')
JOBS['player_portrait'] = ('Single original full-body playable hero, blue spiky hair, youthful adult face, '
    'white laboratory coat over dark navy combat suit, blue-black armored gloves, cyan wrist modules, '
    'dark boots. Confident upright stance, arms slightly apart showing gloves clearly. '
    'Match a clean compact pixel game atlas, not detailed illustration. Solid pure magenta background, '
    'complete silhouette centered with generous padding. No weapon, no text, no frame.')
JOBS['props'] = ('Exactly 4 columns by 3 rows isolated environment sprites on solid magenta background, '
    'equal cells, complete objects with padding, no lines or lettering. Reading order: purple alien tree, '
    'green glowing grass, crystal rocks, metal container, damaged crate, alien spore growth, '
    'green portal frame, control console, reactor, experiment tank, ventilation equipment, camp tent. '
    'Front facing or slight three quarter view suitable for billboard objects in a first person game.')

def generate(job):
    name, detail = job
    target = OUT / (name+'.png')
    if target.exists():
        return name+' cached'
    data = json.dumps({'model':'gpt-image-2','prompt':STYLE+detail,'n':1,'size':'1024x1024'}).encode()
    request=urllib.request.Request('https://img-api.apinebula.ai/v1/images/generations',data=data,
        headers={'Authorization':'Bearer '+os.environ['APINEBULA_API_KEY'],'Content-Type':'application/json'})
    try:
        with urllib.request.urlopen(request,timeout=300) as response:
            item=json.load(response)['data'][0]
        if item.get('b64_json'):
            target.write_bytes(base64.b64decode(item['b64_json']))
        elif item.get('url'):
            # Some Apinebula deployments return a short-lived image URL.
            with urllib.request.urlopen(item['url'],timeout=300) as image_response:
                target.write_bytes(image_response.read())
        else:
            return name+' FAILED: response has neither b64_json nor url'
        return name+' saved'
    except Exception as exc:
        return name+' FAILED '+type(exc).__name__+': '+str(exc)

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    (OUT/'prompts.json').write_text(json.dumps({k:STYLE+v for k,v in JOBS.items()},indent=2),encoding='utf-8')
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
        for result in pool.map(generate,JOBS.items()):
            print(result,flush=True)
