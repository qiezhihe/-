"""Generate low-profile first-person weapon sprites with the authorized Qwen workflow.

Run without arguments for one review sample. After visual approval, run with --batch.
Credentials are consumed only by generate_cloud_art.run and are never printed here.
"""
import sys
from pathlib import Path

import generate_cloud_art as cloud

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "Assets" / "Art" / "low_profile_v2"

WEAPONS = {
    "smg": "compact tactical submachine gun",
    "shotgun": "pump-action shotgun",
    "mg": "belt-fed light machine gun",
    "sniper": "precision scoped rifle",
    "sword": "silver-blue energy sword",
    "boomerang": "gold double-bladed combat boomerang",
    "spear": "compact cyan-tipped energy spear",
    "dagger": "purple energy dagger",
}

POSE = {
    "idle": "steady low-ready pose, no flash, no motion blur",
    "attack": "active attack frame; restrained muzzle flash and slight recoil for firearm, compact strike motion for melee",
    "recover": "settling back toward the same low-ready pose immediately after attack",
}
GUN_POSES={
 'idle':'low ready, rear of weapon nearest viewer, no flash',
 'fire':'one brief small muzzle flash at distant barrel tip, trigger pressed',
 'recoil':'same weapon tilted upward by five degrees after firing, no flash',
 'recover_mid':'same weapon halfway down from recoil to ready',
 'recover':'same weapon settling to ready, matching idle silhouette'}
MELEE_POSES={
 'idle':'compact one handed low ready grip',
 'windup':'wrist slightly drawn back preparing attack',
 'attack':'compact forward slash for sword or dagger, throwing release for spear or boomerang',
 'followthrough':'wrist follows the attack toward lower left',
 'recover_mid':'wrist halfway back to original low ready grip',
 'recover':'same weapon back in low ready grip, matching idle silhouette'}

BASE = """Use case: stylized-concept
Asset type: transparent-ready first-person FPS held-weapon sprite on pure white background
Primary request: {subject}, {action}.
View: actual player's eye view from BEHIND the weapon; camera sees the rear/stock and top plane; muzzle or blade tip points AWAY into the distance, never toward camera. Convincing perspective foreshortening.
Composition: miniature isolated weapon and gripping glove strictly within x=650..1000 y=740..1000 of a 1024x1024 WHITE canvas. All pixels above y=700 and left of x=600 MUST be empty white. Entire subject is small in lower right. This is a small overlay, not a closeup. Keep generous whitespace; do not enlarge subject.
Hands: compact dark tactical gloves only, NO exposed skin, NO forearms, NO long arms. Wrists terminate immediately after glove cuff at bottom edge. Firearm uses one grip glove and a small support glove.
Style: polished realistic sci-fi wasteland FPS raster asset, brushed dark metal, crisp readable silhouette, identical weapon design and scale across animation poses.
Constraints: one weapon only; full weapon is inside canvas with generous white padding; pure white flat background; no ground shadow; no text, logo, UI, border, scenery, character, collage or watermark.
Avoid: side-view catalog/product photography, front-facing muzzle, aiming at viewer, centered or oversized weapon, cropped barrel/stock/blade, large arms, hands covering weapon, floating fingers, multiple frames.
"""


def jobs():
    result = []
    for name, subject in WEAPONS.items():
        for pose, action in (GUN_POSES if name in ('smg','shotgun','mg','sniper') else MELEE_POSES).items():
            result.append((f"low_{name}_{pose}", BASE.format(subject=subject, action=action)))
    return result


def main():
    all_jobs = jobs()
    cloud.OUT = OUT
    cloud.JOBS = all_jobs if "--batch" in sys.argv else [all_jobs[0]]
    cloud.run()


if __name__ == "__main__":
    main()
