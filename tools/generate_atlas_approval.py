"""Generate one review-only atlas through the configured Apinebula endpoint."""
import base64
import json
import os
from pathlib import Path
import urllib.request

PROMPT = """Create a polished, high-information-density PIXEL WORLD ASSET ATLAS for a first-person endless-wave survival roguelite. Landscape 4:3 composition. This is a professional game development asset catalog, NOT a scene illustration or poster. Theme: Rick and Morty-inspired absurd interdimensional science-fiction, malfunctioning laboratories, bizarre alien ecology and green portals. 16-bit arcade pixel art, crisp dark outlines, consistent pixel density, limited 3-5 shade ramps, no antialiasing, no 3D, no photography. Deep blue-purple, gray-blue and dark teal, acid green, mint cyan, dirty ivory, warning orange accents.
Use an ivory low-distraction background, thin grid separators and ten orderly numbered modules, read left-to-right top-to-bottom. High density but generous separation between individual assets. Short legible English labels only. No watermark.
01 PLAYER: full-body interdimensional survivor with lab coat and light armor, coherent idle, run and jump animation frames in a horizontal row, plus small first-person gloved hands reference.
02 ENEMIES: five clearly different silhouettes: gray-green melee experiment soldier with mechanical claw, slim orange fast claw robot, squat blue acid-spitter, wide armored mechanical guard, purple crystal elite hunter.
03 WEAPONS & ITEMS: all eight distinct weapons clearly separated: compact SMG, chunky shotgun, belt-fed machine gun, scoped sniper rifle, sword and forearm shield, three-blade boomerang, piercing spear, blink dagger. Include ammo, medkit, shield battery, XP crystal and upgrade chip.
04 TERRAIN TILES: visibly modular square floor, wall, platform, corner and edge tiles, laboratory metal and alien rock materials, consistent tile size.
05 OUTDOOR PROPS: twisted alien tree, glowing grass, crystal rocks, containers, damaged crates and spore growths.
06 LAB BUILDINGS: doors, windows, wall panels, pipe sockets, ammo refill station, portal frame and campsite equipment.
07 HAZARDS: lava and acid tiles, pit edges, bridge sections and three rising-wall states.
08 INTERIOR DEVICES: control console, reactor, experiment tank, pipes, vents and metal door.
09 BOSSES: three impressive large silhouettes: organic fan-barrage alien lord, orange-thruster quadruped charging mechanical beast, floating purple dimensional core with green eye and orbital rings. Small clear attack telegraphs beside each.
10 PETS & INTERACTIONS: five distinct small companions: green healer spirit, grounded yellow stationary decoy, blue machine-gun drone, grounded four-legged mine-laying robot dog, orange berserk spirit. Include switches, weapon slot frame, upgrade card frame, narrow boss health frame.
Maintain visual consistency and clear scale hierarchy. Show real sprite-like assets rather than tiny abstract marks. Make each module useful as a production visual reference. No large character portraits, no dominant central illustration, no unreadable decorative paragraphs."""

def main():
    output = Path(__file__).resolve().parents[1] / 'artifacts' / 'theme_approval'
    output.mkdir(parents=True, exist_ok=True)
    (output / '01_atlas_prompt.txt').write_text(PROMPT, encoding='utf-8')
    payload = json.dumps({'model': 'gpt-image-2', 'prompt': PROMPT, 'n': 1, 'size': '1536x1024'}).encode()
    request = urllib.request.Request('https://img-api.apinebula.ai/v1/images/generations', data=payload,
        headers={'Authorization': 'Bearer ' + os.environ['APINEBULA_API_KEY'], 'Content-Type': 'application/json'})
    with urllib.request.urlopen(request, timeout=300) as response:
        result = json.load(response)
    item = result['data'][0]
    if item.get('b64_json'):
        path = output / '01_atlas_review.png'
        path.write_bytes(base64.b64decode(item['b64_json']))
        print(str(path))
    elif item.get('url'):
        print('GENERATED_IMAGE_URL=' + item['url'])
    else:
        raise RuntimeError('Image response contained no image')

if __name__ == '__main__':
    main()
