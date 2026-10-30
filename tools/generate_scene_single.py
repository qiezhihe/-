"""Generate original, single-frame surface materials; never uploads assets."""
import json
import generate_pixel_pack as provider
from generate_pixel_pack import generate, OUT

provider.STYLE = ''  # Do not prepend the legacy pixel-art style to painted materials.
PREFIX = ('Premium finely hand-painted game environment material for an atmospheric ancient ruin first-person arena. '
          'Flat orthographic surface filling the entire square, seamless all four edges. '
          'No perspective, no objects, no cast shadows, no text, no borders, no UI, no animation sheet. '
          'Large elegant readable forms, nuanced mineral grain and crafted edges, subdued slate teal and warm limestone palette. '
          'Soft material variation, restrained highlights. NOT pixel art, NO dithering, NO neon circuitry, NO noisy tiny panels, NO heavy outlines. ')
JOBS = {
    'scene_painted_floor': 'Large muted blue slate and warm ivory limestone courtyard slabs, very fine natural grain, subtle moss in sparse narrow joints. Quiet spacious walking surface, no emblems.',
    'scene_painted_wall': 'Large hand-carved limestone fortress masonry blocks, subtle aged teal staining and fine chisel wear, sparse shallow carved accents. No doors or horizon.',
    'scene_painted_metal': 'Vertical side cladding of a solid limestone barrier, substantial broad stone blocks, restrained aged bronze reinforcement, fine weathered edges. No top view.',
    'scene_painted_top': 'Horizontal flat top surface of the same limestone barrier: broad smooth slate capstones, fine mineral grain, subtle worn bronze joinery. No perspective or vertical sides.',
    'scene_painted_lava': 'Dark smooth basalt crust with molten amber and vermilion fissures, nuanced hot mineral gradients, dangerous yet restrained, no raised rocks.',
}

if __name__ == '__main__':
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'scene_single_prompts.json').write_text(json.dumps({k:PREFIX+v for k,v in JOBS.items()},ensure_ascii=False,indent=2),encoding='utf-8')
    for name, detail in JOBS.items():
        result=generate((name,PREFIX+detail))
        print(result,flush=True)
        if 'FAILED' in result:
            raise SystemExit(1)
